import datetime as dt
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))  # make `wellness` importable from any CWD

from wellness import data, model, recommend, schema  # noqa: E402


@st.cache_resource(show_spinner=False)
def get_models() -> model.ModelBundle:
    return model.load_or_train(data.load_or_create_dataset())


def get_user_input():
    st.subheader("Personal Health Information")
    with st.form("user_input_form"):
        col1, col2 = st.columns(2)
        with col1:
            sex = st.selectbox("Sex", schema.SEXES)
            age = st.slider("Age", 18, 70, 35)
            height = st.number_input("Height (cm)", 140, 210, 170)
            weight = st.number_input("Weight (kg)", 35.0, 200.0, 68.0, step=0.5)
            objective = st.selectbox("Objective", schema.OBJECTIVES, index=1)
            timeline = st.selectbox("Timeline", schema.TIMELINES, index=1)
            diet_type = st.selectbox("Diet Type", schema.DIETS)
            sleep_duration = st.slider("Sleep Duration (hrs)", 3.5, 11.0, 7.0, step=0.25)
            wake_up_time = st.time_input("Wake Up Time", dt.time(6, 30), step=900)
            sleep_quality = st.selectbox("Sleep Quality", schema.SLEEP_QUALITIES, index=1)
        with col2:
            exercise = st.slider("Exercise (min/day)", 0, 180, 30, step=5)
            workout_type = st.selectbox("Workout Type", schema.WORKOUT_TYPES, index=1)
            activity_level = st.selectbox("Activity Level", schema.ACTIVITY_LEVELS, index=1)
            stress_level = st.selectbox("Stress Level", schema.STRESS_LEVELS, index=1)
            mood = st.selectbox("Mood", schema.MOODS, index=2)
            mental_focus = st.selectbox("Mental Focus", schema.FOCUS_LEVELS, index=1)
            water = st.slider("Water Intake (L/day)", 0.5, 5.0, 2.0, step=0.1)
            daily_steps = st.slider("Daily Steps", 1000, 25000, 7000, step=500)
            resting_heart_rate = st.slider("Resting Heart Rate (bpm)", 40, 110, 68)
            systolic = st.slider("Systolic Blood Pressure", 85, 190, 120)
            diastolic = st.slider("Diastolic Blood Pressure", 50, 120, 80)

        if not st.form_submit_button("Get Wellness Recommendations"):
            return None

    return recommend.build_profile(
        **{
            "Sex": sex, "Age": age, "Height (cm)": height, "Weight (kg)": weight,
            "Objective": objective, "Timeline": timeline, "Diet Type": diet_type,
            "Sleep Duration (hrs)": sleep_duration,
            "Wake Up Time (min)": wake_up_time.hour * 60 + wake_up_time.minute,
            "Sleep Quality": sleep_quality, "Exercise (min/day)": exercise, "Workout Type": workout_type,
            "Activity Level": activity_level, "Stress Level": stress_level, "Mood": mood,
            "Mental Focus": mental_focus, "Water Intake (L)": water, "Daily Steps": daily_steps,
            "Resting Heart Rate": resting_heart_rate, "Systolic BP": systolic, "Diastolic BP": diastolic,
        }
    )


def main():
    st.set_page_config(page_title="Wellness Prediction System", page_icon="🌿", layout="wide")
    st.title("🌿 Personalized Wellness Prediction System")

    with st.spinner("Loading wellness data and training models (first run only)..."):
        bundle = get_models()

    profile = get_user_input()
    if profile is None:
        return

    plan = recommend.build_plan(bundle, profile)
    t = plan.targets
    for alert in plan.alerts:
        st.warning(alert)

    st.subheader("Your Health Profile")
    st.dataframe(profile.T.astype(str).rename(columns={0: "Value"}), width="stretch")

    st.subheader("Your Personalized Wellness Recommendations")
    st.markdown(f"### 🌟 Wellness Score: {t['Wellness Score']:.0f}/100 ({plan.category})")

    st.markdown("### 🍎 Nutrition")
    c = st.columns(4)
    c[0].metric("Calories", f"{t['Calories']:,.0f} kcal")
    c[1].metric("Protein", f"{t['Protein (g)']:.0f} g")
    c[2].metric("Carbs", f"{t['Carbs (g)']:.0f} g")
    c[3].metric("Fats", f"{t['Fats (g)']:.0f} g")
    st.markdown(f"**Meal pattern:** {t['Meal Pattern']} · **Water:** {t['Water Target (L)']:.1f} L/day")

    st.markdown("### 💪 Exercise")
    c = st.columns(3)
    c[0].metric("Workout plan", t["Workout Plan"])
    c[1].metric("Exercise", f"{t['Exercise Target (min/day)']:.0f} min/day")
    c[2].metric("Daily steps", f"{t['Steps Target']:,.0f}")

    st.markdown("### 😴 Sleep & 🧘 Mind")
    c = st.columns(3)
    c[0].metric("Sleep", f"{t['Sleep Target (hrs)']:.2g} h")
    c[1].metric("Bedtime", plan.bedtime)
    c[2].metric("Mindfulness", t["Mindfulness Practice"])

    for tip in plan.tips:
        st.markdown(f"- {tip}")
    st.info("These are educational, model-generated suggestions based on synthetic data, not medical advice.")


if __name__ == "__main__":
    main()
