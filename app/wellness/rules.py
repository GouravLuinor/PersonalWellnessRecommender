"""Evidence-informed rules that turn a profile into wellness targets.

These rules are the "ground truth" behind the synthetic dataset: the generator
applies them (plus noise) to simulated profiles, and the ML models learn to
reproduce them. They are also used directly to explain the wellness score.

All functions are vectorised over a pandas DataFrame containing the columns in
``schema.FEATURES``.

Sources for the constants (simplified for an educational project):
  * Mifflin-St Jeor equation for basal metabolic rate.
  * Standard activity multipliers (1.2 - 1.725).
  * Protein 1.2 - 2.2 g/kg depending on goal and training.
  * WHO: 150-300 min/week moderate activity; adults sleep 7-9 h.
  * ~33 ml water per kg body weight plus exercise losses.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ACTIVITY_FACTOR = {"Sedentary": 1.2, "Lightly Active": 1.375, "Active": 1.55, "Very Active": 1.725}
DEFICIT = {"1 Month": 0.22, "3 Months": 0.18, "6 Months": 0.12}
SURPLUS = {"1 Month": 0.15, "3 Months": 0.12, "6 Months": 0.08}
EXERCISE_RAMP = {"1 Month": 10, "3 Months": 20, "6 Months": 30}  # extra min/day
STEPS_RAMP = {"1 Month": 2000, "3 Months": 3500, "6 Months": 5000}


def bmi(weight_kg, height_cm):
    return weight_kg / (np.asarray(height_cm) / 100) ** 2


def bmr(df: pd.DataFrame) -> pd.Series:
    """Basal metabolic rate (kcal/day), Mifflin-St Jeor."""
    sex_offset = np.where(df["Sex"] == "Male", 5, -161)
    return 10 * df["Weight (kg)"] + 6.25 * df["Height (cm)"] - 5 * df["Age"] + sex_offset


def nutrition_targets(df: pd.DataFrame) -> pd.DataFrame:
    tdee = bmr(df) * df["Activity Level"].map(ACTIVITY_FACTOR)
    adj = np.select(
        [df["Objective"] == "Weight Loss", df["Objective"] == "Weight Gain"],
        [-df["Timeline"].map(DEFICIT), df["Timeline"].map(SURPLUS)],
        default=0.0,
    )
    floor = np.where(df["Sex"] == "Male", 1500, 1200)
    calories = np.maximum(tdee * (1 + adj), floor)

    # Protein: per kg of reference weight (capped at a BMI-25 weight for high BMI).
    ref_weight = np.minimum(df["Weight (kg)"], 25 * (df["Height (cm)"] / 100) ** 2 * 1.2)
    trains_hard = (df["Exercise (min/day)"] >= 30) & df["Workout Type"].isin(["Strength", "HIIT", "Mixed"])
    g_per_kg = (
        1.2
        + 0.3 * trains_hard
        + 0.4 * (df["Objective"] == "Weight Loss")
        + 0.3 * (df["Objective"] == "Weight Gain")
        + 0.3 * (df["Diet Type"] == "High Protein")
    ).clip(upper=2.2)
    protein = ref_weight * g_per_kg

    keto = df["Diet Type"] == "Keto"
    carbs_keto = 0.05 * calories / 4
    fats_keto = (calories - protein * 4 - carbs_keto * 4) / 9
    fats_std = 0.30 * calories / 9
    carbs_std = np.maximum((calories - protein * 4 - fats_std * 9) / 4, 50)

    return pd.DataFrame(
        {
            "Calories": calories,
            "Protein (g)": protein,
            "Carbs (g)": np.where(keto, carbs_keto, carbs_std),
            "Fats (g)": np.where(keto, fats_keto, fats_std),
        },
        index=df.index,
    )


def water_target(df: pd.DataFrame) -> pd.Series:
    return (0.033 * df["Weight (kg)"] + df["Exercise (min/day)"] / 30 * 0.35).clip(1.5, 5.0)


def sleep_target(df: pd.DataFrame) -> pd.Series:
    base = np.select([df["Age"] <= 25, df["Age"] <= 64], [8.0, 7.5], default=7.25)
    return pd.Series(
        base + 0.25 * (df["Exercise (min/day)"] >= 60) + 0.25 * (df["Stress Level"] == "High"),
        index=df.index,
    )


def exercise_target(df: pd.DataFrame) -> pd.Series:
    goal = df["Objective"].map({"Weight Loss": 45, "Maintenance": 30, "Weight Gain": 40})
    current = df["Exercise (min/day)"]
    ramped = np.minimum(goal, current + df["Timeline"].map(EXERCISE_RAMP))
    return pd.Series(np.maximum(ramped, np.minimum(current, 90)), index=df.index)


def steps_target(df: pd.DataFrame) -> pd.Series:
    goal = np.where(df["Objective"] == "Weight Loss", 12000, 10000)
    current = df["Daily Steps"]
    ramped = np.minimum(goal, current + df["Timeline"].map(STEPS_RAMP))
    return pd.Series(np.maximum(ramped, np.minimum(current, 15000)), index=df.index)


def workout_plan(df: pd.DataFrame) -> pd.Series:
    obj = df["Objective"]
    low_impact = (df["BMI"] >= 32) | (df["Age"] >= 62) | (df["Exercise (min/day)"] < 15)
    plan = np.select(
        [
            obj == "Weight Gain",
            (obj == "Weight Loss") & low_impact,
            obj == "Weight Loss",
            df["Stress Level"] == "High",
            low_impact,
            df["Workout Type"] == "Strength",
            df["Exercise (min/day)"] >= 60,
        ],
        [
            "Strength Training",
            "Low-Impact Cardio",
            "Cardio + Strength",
            "Yoga & Mobility",
            "Low-Impact Cardio",
            "Strength Training",
            "HIIT + Recovery",
        ],
        default="Cardio + Strength",
    )
    return pd.Series(plan, index=df.index)


def meal_pattern(df: pd.DataFrame) -> pd.Series:
    poor_sleep = df["Sleep Quality"].isin(["Poor"]) | (df["Sleep Duration (hrs)"] < 6)
    pattern = np.select(
        [
            df["Objective"] == "Weight Gain",
            poor_sleep | (df["Stress Level"] == "High"),
            (df["Objective"] == "Weight Loss") | (df["Diet Type"] == "Keto"),
        ],
        ["5-6 Smaller Meals", "Regular Meals, Early Dinner", "Time-Restricted Eating"],
        default="3 Balanced Meals",
    )
    return pd.Series(pattern, index=df.index)


def mindfulness_practice(df: pd.DataFrame) -> pd.Series:
    high_stress = df["Stress Level"] == "High"
    practice = np.select(
        [
            high_stress & (df["Sleep Quality"] == "Poor"),
            high_stress,
            df["Mood"].isin(["Sad", "Tired"]),
            df["Mental Focus"] == "Low",
        ],
        ["Body-Scan Meditation", "Box Breathing", "Nature Walk", "Focused-Attention Meditation"],
        default="Gratitude Journaling",
    )
    return pd.Series(practice, index=df.index)


# --- Wellness score -----------------------------------------------------------

def _band(x, lo, hi, soft):
    """1 inside [lo, hi], falling linearly to 0 at `soft` units outside."""
    x = np.asarray(x, dtype=float)
    below = np.clip(1 - (lo - x) / soft, 0, 1)
    above = np.clip(1 - (x - hi) / soft, 0, 1)
    return np.where(x < lo, below, np.where(x > hi, above, 1.0))


FACTOR_WEIGHTS = {
    "Sleep duration": 14,
    "Sleep quality": 10,
    "Body weight (BMI)": 12,
    "Daily steps": 10,
    "Exercise": 12,
    "Stress": 12,
    "Mood": 8,
    "Hydration": 7,
    "Resting heart rate": 7,
    "Blood pressure": 8,
}


def wellness_factors(df: pd.DataFrame) -> pd.DataFrame:
    """Per-factor scores in [0, 1] for each profile."""
    quality = df["Sleep Quality"].map({"Poor": 0.1, "Average": 0.5, "Good": 0.85, "Excellent": 1.0})
    stress = df["Stress Level"].map({"Low": 1.0, "Moderate": 0.6, "High": 0.15})
    mood = df["Mood"].map({"Happy": 1.0, "Energetic": 1.0, "Neutral": 0.65, "Tired": 0.35, "Sad": 0.2})
    bp = np.minimum(_band(df["Systolic BP"], 90, 120, 25), _band(df["Diastolic BP"], 60, 80, 15))
    return pd.DataFrame(
        {
            "Sleep duration": _band(df["Sleep Duration (hrs)"], 7, 9, 2.5),
            "Sleep quality": quality,
            "Body weight (BMI)": _band(df["BMI"], 18.5, 24.9, 8),
            "Daily steps": np.clip(df["Daily Steps"] / 8000, 0, 1),
            "Exercise": np.clip(df["Exercise (min/day)"] / 30, 0, 1),
            "Stress": stress,
            "Mood": mood,
            "Hydration": np.clip(df["Water Intake (L)"] / water_target(df), 0, 1),
            "Resting heart rate": _band(df["Resting Heart Rate"], 50, 72, 20),
            "Blood pressure": bp,
        },
        index=df.index,
    ).astype(float)


def wellness_score(df: pd.DataFrame) -> pd.Series:
    factors = wellness_factors(df)
    weights = pd.Series(FACTOR_WEIGHTS)
    return factors[weights.index] @ weights / weights.sum() * 100


def score_category(score: float) -> str:
    if score >= 80:
        return "Excellent"
    if score >= 65:
        return "Good"
    if score >= 45:
        return "Fair"
    return "Needs attention"


def compute_targets(df: pd.DataFrame) -> pd.DataFrame:
    """Noise-free targets for every profile in ``df``."""
    out = nutrition_targets(df)
    out["Water Target (L)"] = water_target(df)
    out["Sleep Target (hrs)"] = sleep_target(df)
    out["Exercise Target (min/day)"] = exercise_target(df)
    out["Steps Target"] = steps_target(df)
    out["Wellness Score"] = wellness_score(df)
    out["Workout Plan"] = workout_plan(df)
    out["Meal Pattern"] = meal_pattern(df)
    out["Mindfulness Practice"] = mindfulness_practice(df)
    return out
