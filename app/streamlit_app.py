"""Streamlit UI for the Personal Wellness Recommender."""

import datetime as dt
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))  # make `wellness` importable from any CWD

from wellness import data, model, recommend, rules, schema  # noqa: E402

st.set_page_config(
    page_title="Wellness Recommender",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="auto",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.2rem; max-width: 1180px; }
      [data-testid="stMetricValue"] { font-size: 1.6rem; }
      .eyebrow { text-transform: uppercase; letter-spacing: .08em; font-size: .75rem; opacity: .7; margin: 0; }
      .big-score { font-size: 3.4rem; font-weight: 700; line-height: 1; margin: .2rem 0 .1rem; }
      .big-score small { font-size: 1.1rem; font-weight: 500; opacity: .6; }
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORY_COLOR = {"Excellent": "green", "Good": "green", "Fair": "orange", "Needs attention": "red"}
GOOD, OK, POOR = "#3f9a6b", "#d69e2e", "#d0574a"


# --- Data & models -------------------------------------------------------------

@st.cache_resource(show_spinner=False)
def get_models() -> model.ModelBundle:
    return model.load_or_train(get_dataset())


@st.cache_data(show_spinner=False)
def get_dataset() -> pd.DataFrame:
    return data.load_or_create_dataset()


# --- Profile form --------------------------------------------------------------

def profile_form() -> tuple[bool, pd.DataFrame]:
    with st.form("profile_form"):
        st.markdown("### Your profile")
        st.caption("All fields have sensible defaults. Adjust what you know and press **Build my plan**.")

        with st.expander("Body & goal", expanded=True, icon=":material/person:"):
            sex = st.segmented_control("Sex", schema.SEXES, default="Female", required=True,
                                       help="Used to estimate your basal metabolic rate.")
            age = st.number_input("Age", 18, 70, 32)
            c1, c2 = st.columns(2)
            height = c1.number_input("Height (cm)", 140, 210, 168)
            weight = c2.number_input("Weight (kg)", 35.0, 200.0, 66.0, step=0.5)
            objective = st.selectbox("Goal", schema.OBJECTIVES, index=1)
            timeline = st.select_slider("Timeline", schema.TIMELINES, value="3 Months",
                                        help="Shorter timelines mean bigger, faster changes.")
            diet = st.selectbox("Diet", schema.DIETS)

        with st.expander("Activity", icon=":material/directions_run:"):
            activity = st.select_slider("Day-to-day activity", schema.ACTIVITY_LEVELS, value="Lightly Active",
                                        help="Sedentary = mostly sitting; Very Active = physical job or daily training.")
            workout_type = st.selectbox("Main type of exercise", schema.WORKOUT_TYPES, index=1)
            exercise = st.slider("Exercise (minutes per day)", 0, 180, 25, step=5,
                                 help="Average across the week. 150 min/week is about 20 min/day.")
            steps = st.slider("Daily steps", 1000, 25000, 6500, step=500)

        with st.expander("Sleep", icon=":material/bedtime:"):
            sleep = st.slider("Sleep per night (hours)", 3.5, 11.0, 6.75, step=0.25)
            quality = st.select_slider("Sleep quality", schema.SLEEP_QUALITIES, value="Average")
            wake = st.time_input("Usual wake-up time", dt.time(7, 0), step=900)

        with st.expander("Mind & hydration", icon=":material/self_improvement:"):
            stress = st.segmented_control("Stress", schema.STRESS_LEVELS, default="Moderate", required=True)
            mood = st.selectbox("Mood most days", schema.MOODS, index=2)
            focus = st.segmented_control("Mental focus", schema.FOCUS_LEVELS, default="Medium", required=True)
            water = st.slider("Water per day (litres)", 0.5, 5.0, 1.8, step=0.1)

        with st.expander("Vitals (optional)", icon=":material/monitor_heart:"):
            st.caption("Leave the defaults if you don't know them.")
            rhr = st.number_input("Resting heart rate (bpm)", 40, 120, 68)
            c1, c2 = st.columns(2)
            systolic = c1.number_input("Systolic BP", 85, 200, 118)
            diastolic = c2.number_input("Diastolic BP", 50, 130, 76)

        submitted = st.form_submit_button("Build my plan", type="primary", icon=":material/auto_awesome:",
                                          width="stretch")

    profile = recommend.build_profile(**{
        "Sex": sex, "Age": age, "Height (cm)": height, "Weight (kg)": weight,
        "Objective": objective, "Timeline": timeline, "Diet Type": diet,
        "Activity Level": activity, "Workout Type": workout_type, "Exercise (min/day)": exercise,
        "Daily Steps": steps, "Sleep Duration (hrs)": sleep, "Sleep Quality": quality,
        "Wake Up Time (min)": wake.hour * 60 + wake.minute,
        "Stress Level": stress, "Mood": mood, "Mental Focus": focus, "Water Intake (L)": water,
        "Resting Heart Rate": rhr, "Systolic BP": systolic, "Diastolic BP": diastolic,
    })
    return submitted, profile


# --- Result sections -----------------------------------------------------------

def _fmt_delta(value: float, unit: str, decimals: int = 0) -> str | None:
    if round(value, decimals) == 0:
        return "On target"
    text = f"{value:+,.{decimals}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return f"{text} {unit}"


def summary(plan: recommend.Plan) -> None:
    t, p = plan.targets, plan.profile
    with st.container(border=True):
        left, right = st.columns([1, 2], gap="large")
        with left:
            st.markdown('<div class="eyebrow">Wellness score</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="big-score">{t["Wellness Score"]:.0f}<small> / 100</small></div>',
                        unsafe_allow_html=True)
            st.badge(plan.category, color=CATEGORY_COLOR[plan.category])
            st.progress(int(t["Wellness Score"]) / 100)
            st.caption(f"Goal: **{p['Objective'].lower()}** over **{p['Timeline'].lower()}** · "
                       f"BMI {p['BMI']:.1f}")
        with right:
            st.markdown('<div class="eyebrow">Biggest opportunities</div>', unsafe_allow_html=True)
            focus = plan.focus_areas[:3]
            if focus:
                for f in focus:
                    st.markdown(f"**{f.name}**: {f.detail}")
            else:
                st.markdown("Every area is in a healthy range. Keep doing what you're doing.")
            if plan.strengths:
                st.caption("Going well: " + " · ".join(f.name for f in plan.strengths[:4]))

    cols = st.columns(4)
    cols[0].metric("Sleep target", f"{t['Sleep Target (hrs)']:g} h",
                   _fmt_delta(t["Sleep Target (hrs)"] - p["Sleep Duration (hrs)"], "h", 2),
                   help=f"You currently sleep {p['Sleep Duration (hrs)']:g} h.", border=True)
    cols[1].metric("Daily steps", f"{t['Steps Target']:,.0f}",
                   _fmt_delta(t["Steps Target"] - p["Daily Steps"], "steps"),
                   help=f"You currently walk {p['Daily Steps']:,.0f} steps.", border=True)
    cols[2].metric("Exercise", f"{t['Exercise Target (min/day)']:.0f} min/day",
                   _fmt_delta(t["Exercise Target (min/day)"] - p["Exercise (min/day)"], "min"),
                   help=f"You currently exercise {p['Exercise (min/day)']:.0f} min/day.", border=True)
    cols[3].metric("Water", f"{t['Water Target (L)']:.1f} L",
                   _fmt_delta(t["Water Target (L)"] - p["Water Intake (L)"], "L", 1),
                   help=f"You currently drink {p['Water Intake (L)']:.1f} L.", border=True)
    st.caption("Arrows show the change from your current habits. Targets ramp up gradually to fit your timeline.")


def nutrition_tab(plan: recommend.Plan) -> None:
    t = plan.targets
    cols = st.columns(4)
    cols[0].metric("Calories", f"{t['Calories']:,.0f}", help="kcal per day", border=True)
    cols[1].metric("Protein", f"{t['Protein (g)']:.0f} g", border=True)
    cols[2].metric("Carbs", f"{t['Carbs (g)']:.0f} g", border=True)
    cols[3].metric("Fats", f"{t['Fats (g)']:.0f} g", border=True)

    left, right = st.columns([1, 1], gap="large")
    with left:
        macros = pd.DataFrame({
            "Macro": ["Protein", "Carbs", "Fats"],
            "kcal": [t["Protein (g)"] * 4, t["Carbs (g)"] * 4, t["Fats (g)"] * 9],
        })
        macros["Share"] = macros["kcal"] / macros["kcal"].sum()
        chart = (
            alt.Chart(macros)
            .mark_arc(innerRadius=62, outerRadius=100, cornerRadius=4, padAngle=0.02)
            .encode(
                theta="kcal:Q",
                color=alt.Color("Macro:N", legend=alt.Legend(orient="bottom", title=None)),
                tooltip=["Macro", alt.Tooltip("kcal:Q", format=",.0f"), alt.Tooltip("Share:Q", format=".0%")],
            )
            .properties(height=300, title="Where your calories come from")
        )
        st.altair_chart(chart, width="stretch")
    with right:
        st.markdown(f"#### {t['Meal Pattern']}")
        st.write(recommend.DESCRIPTIONS[t["Meal Pattern"]])
        st.markdown(f"**Diet:** {plan.profile['Diet Type']}  \n**Water:** {t['Water Target (L)']:.1f} L a day")
        bmr = float(rules.bmr(pd.DataFrame([plan.profile])).iloc[0])
        st.caption(f"Your estimated resting burn (BMR) is about {bmr:,.0f} kcal. "
                   "Calories are adjusted for activity and your goal.")


def movement_tab(plan: recommend.Plan) -> None:
    t, p = plan.targets, plan.profile
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.markdown(f"#### {t['Workout Plan']}")
        st.write(recommend.DESCRIPTIONS[t["Workout Plan"]])
        st.markdown(f"Aim for **{t['Exercise Target (min/day)']:.0f} minutes a day** "
                    f"(≈ {t['Exercise Target (min/day)'] * 7:.0f} min/week) and "
                    f"**{t['Steps Target']:,.0f} steps**.")
    with right, st.container(border=True):
        st.markdown('<div class="eyebrow">Progress to target</div>', unsafe_allow_html=True)
        for label, now, target, unit in [
            ("Exercise", p["Exercise (min/day)"], t["Exercise Target (min/day)"], "min/day"),
            ("Steps", p["Daily Steps"], t["Steps Target"], "a day"),
        ]:
            share = min(now / target, 1.0) if target else 1.0
            st.progress(share, text=f"**{label}**: {now:,.0f} → {target:,.0f} {unit} ({share:.0%} there)")


def sleep_mind_tab(plan: recommend.Plan) -> None:
    t, p = plan.targets, plan.profile
    cols = st.columns(3)
    cols[0].metric("Sleep target", f"{t['Sleep Target (hrs)']:g} h", border=True)
    cols[1].metric("Lights out by", plan.bedtime, border=True,
                   help=f"Allows ~{recommend.FALL_ASLEEP_MIN} minutes to fall asleep.")
    cols[2].metric("Wake up", recommend.minutes_to_hhmm(p["Wake Up Time (min)"]), border=True)
    st.markdown(f"#### {t['Mindfulness Practice']}")
    st.write(recommend.DESCRIPTIONS[t["Mindfulness Practice"]])
    st.caption(f"Chosen for {p['Stress Level'].lower()} stress, {p['Sleep Quality'].lower()} sleep "
               f"and {p['Mood'].lower()} mood.")


def breakdown_tab(plan: recommend.Plan) -> None:
    st.write("How each area of your profile rates against healthy reference ranges. Longer bars are better. "
             "Areas with a higher impact count for more in the score.")
    rows = pd.DataFrame([
        {"Area": f.name, "Rating": f.score, "Impact": f.weight, "Detail": f.detail} for f in plan.factors
    ]).sort_values("Rating")
    rows["Band"] = pd.cut(rows["Rating"], [-0.01, 0.5, 0.85, 1.0], labels=["Needs work", "Fair", "Healthy"])
    chart = (
        alt.Chart(rows)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            x=alt.X("Rating:Q", scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format="%", title=None)),
            y=alt.Y("Area:N", sort=rows["Area"].tolist(), title=None),
            color=alt.Color("Band:N", scale=alt.Scale(domain=["Needs work", "Fair", "Healthy"], range=[POOR, OK, GOOD]),
                            legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["Area", alt.Tooltip("Rating:Q", format=".0%"), "Impact", "Detail"],
        )
        .properties(height=34 * len(rows))
    )
    st.altair_chart(chart, width="stretch")
    with st.expander("What drives the wellness score in the model?"):
        imp = get_models().feature_importance
        if imp is not None:
            top = imp.head(10).rename_axis("Feature").reset_index(name="Importance")
            st.altair_chart(
                alt.Chart(top).mark_bar(cornerRadiusEnd=4, color=GOOD).encode(
                    x=alt.X("Importance:Q", title="Drop in R² when shuffled"),
                    y=alt.Y("Feature:N", sort="-x", title=None),
                ).properties(height=28 * len(top)),
                width="stretch",
            )


COMPARE_METRICS = {
    "Sleep (hours)": "Sleep Duration (hrs)",
    "Daily steps": "Daily Steps",
    "Exercise (min/day)": "Exercise (min/day)",
    "BMI": "BMI",
    "Resting heart rate": "Resting Heart Rate",
    "Systolic BP": "Systolic BP",
    "Water (L)": "Water Intake (L)",
    "Wellness score": "Wellness Score",
}


def compare_tab(plan: recommend.Plan) -> None:
    df = get_dataset()
    label = st.segmented_control("Compare", list(COMPARE_METRICS), default="Sleep (hours)", required=True,
                                 label_visibility="collapsed", key="compare_metric")
    col = COMPARE_METRICS[label]
    value = plan.targets[col] if col == "Wellness Score" else plan.profile[col]
    pct = (df[col] < value).mean()
    name = label if label.split()[0].isupper() else label[0].lower() + label[1:]
    st.markdown(f"Your **{name}** of **{value:,.4g}** is higher than **{pct:.0%}** of the "
                f"{len(df):,} simulated profiles.")
    base = alt.Chart(df[[col]])
    hist = base.mark_bar(opacity=0.75, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
        x=alt.X(f"{col}:Q", bin=alt.Bin(maxbins=40), title=label),
        y=alt.Y("count():Q", title="Profiles"),
    )
    rule = alt.Chart(pd.DataFrame({"v": [value]})).mark_rule(color=POOR, strokeWidth=3).encode(x="v:Q")
    st.altair_chart((hist + rule).properties(height=300), width="stretch")
    st.caption("Red line = you. The population is synthetic, so treat this as illustrative only.")


def model_tab() -> None:
    bundle = get_models()
    st.write("Models are trained on 10,000 synthetic profiles generated from published guidelines "
             "(Mifflin-St Jeor energy needs, WHO activity and sleep guidance) plus random variation. "
             "Scores below are on a 20% held-out test set.")
    reg = pd.DataFrame([
        {"Target": k, "R²": v["r2"], "Mean abs. error": v["mae"]}
        for k, v in bundle.metrics.items() if v["kind"] == "regression"
    ])
    clf = pd.DataFrame([
        {"Target": k, "Accuracy": v["accuracy"], "Baseline (guess most common)": v["baseline"]}
        for k, v in bundle.metrics.items() if v["kind"] == "classification"
    ])
    st.markdown("**Numeric targets**")
    st.dataframe(reg, hide_index=True, width="stretch",
                   column_config={"R²": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
                                  "Mean abs. error": st.column_config.NumberColumn(format="%.1f")})
    st.markdown("**Categorical recommendations**")
    st.dataframe(clf, hide_index=True, width="stretch",
                    column_config={c: st.column_config.NumberColumn(format="percent") for c in clf.columns[1:]})
    st.caption("Gradient-boosted trees (regression) and random forests (classification), scikit-learn. "
               "High scores show the models learned the generating rules. They are **not** evidence of "
               "real-world clinical accuracy.")


# --- Page ----------------------------------------------------------------------

def main() -> None:
    with st.sidebar:
        submitted, profile = profile_form()
        st.caption("Your data stays in this session and is never stored.")

    if submitted or "profile" not in st.session_state:
        st.session_state.profile = profile
        st.session_state.is_sample = not submitted

    st.title("Your wellness plan")
    st.caption("Personalised nutrition, movement, sleep and mindfulness targets from your lifestyle profile.")

    if "models_ready" not in st.session_state:
        with st.spinner("Preparing models. This only happens on the first launch..."):
            get_models()
        st.session_state.models_ready = True

    if st.session_state.is_sample:
        st.info("This is a **sample plan** for the default profile. Enter your details in the sidebar and press "
                "**Build my plan** to personalise it.", icon=":material/info:")

    plan = recommend.build_plan(get_models(), st.session_state.profile)
    for alert in plan.alerts:
        st.warning(alert, icon=":material/medical_services:")

    summary(plan)

    tabs = st.tabs([
        ":material/restaurant: Nutrition",
        ":material/fitness_center: Movement",
        ":material/bedtime: Sleep & mind",
        ":material/insights: Score breakdown",
        ":material/groups: Compare",
        ":material/model_training: About the model",
    ])
    with tabs[0]:
        nutrition_tab(plan)
    with tabs[1]:
        movement_tab(plan)
    with tabs[2]:
        sleep_mind_tab(plan)
    with tabs[3]:
        breakdown_tab(plan)
    with tabs[4]:
        compare_tab(plan)
    with tabs[5]:
        model_tab()

    if plan.tips:
        st.subheader("Next steps")
        for tip in plan.tips:
            st.markdown(f"- {tip}")

    st.download_button(
        "Download my plan",
        recommend.plan_to_markdown(plan),
        file_name="wellness-plan.md",
        mime="text/markdown",
        icon=":material/download:",
    )
    st.divider()
    st.caption("Educational project trained on synthetic data. It does not provide medical advice, diagnosis or "
               "treatment. Talk to a qualified professional before making significant changes.")


main()
