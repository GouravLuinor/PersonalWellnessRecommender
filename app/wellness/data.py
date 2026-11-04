"""Synthetic wellness dataset generation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import rules, schema

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATED_DIR = PROJECT_ROOT / "data" / "generated"
DATASET_PATH = GENERATED_DIR / f"wellness_dataset_v{schema.DATA_VERSION}.csv"


def _choice(rng, options, n, p=None):
    return rng.choice(np.array(options, dtype=object), size=n, p=p)


def _choice_rows(rng, options, probs):
    """Pick one option per row, with a separate probability vector per row."""
    probs = np.asarray(probs, dtype=float)
    probs = probs / probs.sum(axis=1, keepdims=True)
    idx = (probs.cumsum(axis=1) > rng.random((len(probs), 1))).argmax(axis=1)
    return np.array(options, dtype=object)[idx]


def generate_profiles(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """Simulated input profiles with plausible correlations between features."""
    sex = _choice(rng, schema.SEXES, n)
    male = sex == "Male"
    age = rng.integers(18, 71, n)
    height = np.where(male, rng.normal(176, 7, n), rng.normal(163, 6.5, n)).clip(145, 205).round()
    body_mass_index = rng.normal(26, 4.5, n).clip(16, 45)
    weight = (body_mass_index * (height / 100) ** 2).round(1)
    body_mass_index = rules.bmi(weight, height).round(1)

    # Higher BMI -> more likely sedentary.
    heavy = (body_mass_index > 30)[:, None]
    lean = (body_mass_index < 21)[:, None]
    activity_p = np.where(heavy, [0.45, 0.3, 0.18, 0.07], np.where(lean, [0.1, 0.25, 0.35, 0.3], [0.25, 0.3, 0.3, 0.15]))
    activity = _choice_rows(rng, schema.ACTIVITY_LEVELS, activity_p)
    level = pd.Series(activity).map({a: i for i, a in enumerate(schema.ACTIVITY_LEVELS)}).to_numpy()

    steps = (np.array([3500, 6000, 9000, 12500])[level] + rng.normal(0, 1500, n)).clip(1000, 25000).round(-2)
    exercise = (np.array([8, 25, 45, 70])[level] + rng.normal(0, 12, n)).clip(0, 180).round(-1) / 1
    exercise = np.where(rng.random(n) < 0.15 * (level == 0), 0, exercise)
    workout = np.where(
        exercise < 10,
        "None",
        _choice(rng, schema.WORKOUT_TYPES[1:], n, p=[0.3, 0.25, 0.15, 0.15, 0.15]),
    )

    objective_p = np.where(
        body_mass_index[:, None] > 27, [0.75, 0.2, 0.05],
        np.where(body_mass_index[:, None] < 20, [0.05, 0.3, 0.65], [0.3, 0.5, 0.2]),
    )
    objective = _choice_rows(rng, schema.OBJECTIVES, objective_p)

    stress = _choice(rng, schema.STRESS_LEVELS, n, p=[0.3, 0.45, 0.25])
    high_stress = stress == "High"
    sleep = (rng.normal(7.1, 1.0, n) - 0.5 * high_stress).clip(3.5, 11).round(1)
    sleep_q_idx = (
        1.4 + 0.6 * (sleep - 7) - 0.8 * high_stress + 0.3 * (stress == "Low") + rng.normal(0, 0.7, n)
    ).round().clip(0, 3).astype(int)
    sleep_quality = np.array(schema.SLEEP_QUALITIES, dtype=object)[sleep_q_idx]

    mood_p = np.where(
        high_stress[:, None], [0.15, 0.05, 0.3, 0.25, 0.25],
        np.where((stress == "Low")[:, None], [0.4, 0.25, 0.25, 0.05, 0.05], [0.25, 0.15, 0.35, 0.15, 0.1]),
    )
    mood = _choice_rows(rng, schema.MOODS, mood_p)
    focus_idx = (1 + 0.4 * (sleep_q_idx - 1.5) - 0.6 * high_stress + rng.normal(0, 0.6, n)).round().clip(0, 2)
    focus = np.array(schema.FOCUS_LEVELS, dtype=object)[focus_idx.astype(int)]

    water = rng.normal(2.1, 0.7, n).clip(0.5, 5).round(1)
    wake = (rng.normal(420, 45, n) / 15).round().clip(18, 44) * 15  # 04:30 - 11:00
    rhr = (74 - 0.12 * exercise + 0.5 * (body_mass_index - 25) + 3 * high_stress + rng.normal(0, 6, n)).clip(42, 105).round()
    systolic = (108 + 0.45 * (age - 18) + 1.0 * (body_mass_index - 25) + 4 * high_stress + rng.normal(0, 9, n)).clip(88, 185).round()
    diastolic = (70 + 0.2 * (age - 18) + 0.6 * (body_mass_index - 25) + 2 * high_stress + rng.normal(0, 6, n)).clip(55, 115).round()

    return pd.DataFrame(
        {
            "Age": age,
            "Height (cm)": height,
            "Weight (kg)": weight,
            "BMI": body_mass_index,
            "Sleep Duration (hrs)": sleep,
            "Wake Up Time (min)": wake,
            "Exercise (min/day)": exercise,
            "Water Intake (L)": water,
            "Daily Steps": steps,
            "Resting Heart Rate": rhr,
            "Systolic BP": systolic,
            "Diastolic BP": diastolic,
            "Sex": sex,
            "Objective": objective,
            "Timeline": _choice(rng, schema.TIMELINES, n),
            "Diet Type": _choice(rng, schema.DIETS, n, p=[0.35, 0.2, 0.1, 0.2, 0.15]),
            "Workout Type": workout,
            "Activity Level": activity,
            "Sleep Quality": sleep_quality,
            "Stress Level": stress,
            "Mood": mood,
            "Mental Focus": focus,
        }
    )[schema.FEATURES]


def _add_noise(targets: pd.DataFrame, rng: np.random.Generator, label_noise: float) -> pd.DataFrame:
    """Simulate individual variation / expert disagreement around the rules."""
    t = targets.copy()
    n = len(t)
    for col, rel in [("Calories", 0.04), ("Protein (g)", 0.06), ("Carbs (g)", 0.06), ("Fats (g)", 0.06), ("Water Target (L)", 0.05)]:
        t[col] = t[col] * rng.normal(1, rel, n)
    t["Sleep Target (hrs)"] += rng.normal(0, 0.15, n)
    t["Exercise Target (min/day)"] += rng.normal(0, 3, n)
    t["Steps Target"] += rng.normal(0, 400, n)
    t["Wellness Score"] = (t["Wellness Score"] + rng.normal(0, 2.5, n)).clip(0, 100)

    options = {
        "Workout Plan": schema.WORKOUT_PLANS,
        "Meal Pattern": schema.MEAL_PATTERNS,
        "Mindfulness Practice": schema.MINDFULNESS_PRACTICES,
    }
    for col, opts in options.items():
        flip = rng.random(n) < label_noise
        t.loc[flip, col] = _choice(rng, opts, int(flip.sum()))
    return round_targets(t)


def round_targets(t: pd.DataFrame) -> pd.DataFrame:
    t = t.copy()
    t["Calories"] = (t["Calories"] / 10).round() * 10
    for col in ["Protein (g)", "Carbs (g)", "Fats (g)"]:
        t[col] = t[col].round()
    t["Water Target (L)"] = t["Water Target (L)"].round(1)
    t["Sleep Target (hrs)"] = (t["Sleep Target (hrs)"] * 4).round() / 4
    t["Exercise Target (min/day)"] = (t["Exercise Target (min/day)"] / 5).round() * 5
    t["Steps Target"] = t["Steps Target"].round(-2)
    t["Wellness Score"] = t["Wellness Score"].round(1)
    return t


def generate_dataset(n: int = 10_000, seed: int = 42, label_noise: float = 0.08) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    profiles = generate_profiles(n, rng)
    targets = _add_noise(rules.compute_targets(profiles), rng, label_noise)
    return pd.concat([profiles, targets], axis=1)


def load_or_create_dataset(path: Path = DATASET_PATH, n: int = 10_000, seed: int = 42) -> pd.DataFrame:
    """Read the cached dataset, regenerating it if missing or unreadable."""
    path = Path(path)
    if path.exists():
        try:
            df = pd.read_csv(path)
            if set(schema.FEATURES + schema.TARGETS) <= set(df.columns) and len(df) == n:
                return df
        except (pd.errors.ParserError, pd.errors.EmptyDataError, OSError):
            pass
    df = generate_dataset(n=n, seed=seed)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return df
