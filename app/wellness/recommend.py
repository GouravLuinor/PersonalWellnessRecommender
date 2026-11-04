"""Turn model predictions into a human-readable wellness plan."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import pandas as pd

from . import model, rules, schema
from .data import round_targets

FALL_ASLEEP_MIN = 15


def minutes_to_hhmm(minutes: float) -> str:
    minutes = int(round(minutes)) % (24 * 60)
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def build_profile(**values) -> pd.DataFrame:
    """Single-row feature frame; BMI is derived from height and weight."""
    values = dict(values)
    values["BMI"] = round(float(rules.bmi(values["Weight (kg)"], values["Height (cm)"])), 1)
    missing = set(schema.FEATURES) - set(values)
    if missing:
        raise ValueError(f"Missing profile fields: {sorted(missing)}")
    return pd.DataFrame([values])[schema.FEATURES]


@dataclass
class Factor:
    name: str
    score: float  # 0..1
    weight: int
    detail: str


@dataclass
class Plan:
    profile: dict
    targets: dict
    category: str
    bedtime: str
    factors: list[Factor]
    tips: list[str] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return self.targets["Wellness Score"]

    @property
    def strengths(self) -> list[Factor]:
        return [f for f in sorted(self.factors, key=lambda f: -f.score) if f.score >= 0.85]

    @property
    def focus_areas(self) -> list[Factor]:
        """Factors costing the most points, worst first."""
        lacking = [f for f in self.factors if f.score < 0.85]
        return sorted(lacking, key=lambda f: -(1 - f.score) * f.weight)


def _factor_details(p: dict, water_goal: float) -> dict[str, str]:
    return {
        "Sleep duration": f"{p['Sleep Duration (hrs)']:.1f} h a night (7-9 h is the healthy range)",
        "Sleep quality": f"{p['Sleep Quality']} sleep quality",
        "Body weight (BMI)": f"BMI {p['BMI']:.1f} (18.5-24.9 is the reference range)",
        "Daily steps": f"{int(p['Daily Steps']):,} steps a day (8,000+ is associated with better outcomes)",
        "Exercise": f"{int(p['Exercise (min/day)'])} min/day of exercise (30+ meets WHO guidance)",
        "Stress": f"{p['Stress Level']} stress",
        "Mood": f"Mostly feeling {p['Mood'].lower()}",
        "Hydration": f"{p['Water Intake (L)']:.1f} L of water vs ~{water_goal:.1f} L needed",
        "Resting heart rate": f"{int(p['Resting Heart Rate'])} bpm resting (50-72 is typical for healthy adults)",
        "Blood pressure": f"{int(p['Systolic BP'])}/{int(p['Diastolic BP'])} mmHg (below 120/80 is optimal)",
    }


def _alerts(p: dict) -> list[str]:
    alerts = []
    sys_bp, dia_bp = p["Systolic BP"], p["Diastolic BP"]
    if sys_bp >= 180 or dia_bp >= 120:
        alerts.append("Your blood pressure reading is in the hypertensive-crisis range. Seek medical care promptly.")
    elif sys_bp >= 140 or dia_bp >= 90:
        alerts.append("Your blood pressure is in the high range. Please have it checked by a healthcare professional.")
    if p["Resting Heart Rate"] > 100:
        alerts.append("A resting heart rate above 100 bpm is worth discussing with a doctor.")
    if p["BMI"] < 17:
        alerts.append("Your BMI is well below the healthy range. A doctor or dietitian can help with safe weight gain.")
    if p["BMI"] >= 35 or p["Age"] >= 60:
        alerts.append("Check with a doctor before starting a new exercise programme.")
    return alerts


def _tips(p: dict, t: dict) -> list[str]:
    tips = []
    water_gap = t["Water Target (L)"] - p["Water Intake (L)"]
    if water_gap >= 0.3:
        tips.append(f"Add about {water_gap:.1f} L of water a day. Keeping a bottle in sight makes this easier.")
    if p["Sleep Duration (hrs)"] < t["Sleep Target (hrs)"] - 0.25:
        tips.append("Move bedtime earlier in 15-minute steps rather than all at once.")
    if p["Sleep Quality"] in ("Poor", "Average"):
        tips.append("Keep screens out of the last 30-60 minutes before bed and keep the bedroom cool and dark.")
    step_gap = t["Steps Target"] - p["Daily Steps"]
    if step_gap >= 500:
        tips.append(f"Add ~{int(round(step_gap, -2)):,} steps: a 10-minute walk after meals adds about 1,000 each time.")
    if p["Stress Level"] == "High":
        tips.append("Schedule two short breaks a day for your mindfulness practice. Consistency matters more than length.")
    if p["Diet Type"] == "Vegan":
        tips.append("On a vegan diet, make sure you get a reliable source of vitamin B12 (fortified foods or a supplement).")
    if p["Diet Type"] == "Keto":
        tips.append("On keto, prioritise vegetables, nuts and olive oil over processed meats to protect heart health.")
    if p["Objective"] == "Weight Loss" and p["Timeline"] == "1 Month":
        tips.append("A 1-month timeline is aggressive. Aim for 0.5-1 kg a week to keep the progress sustainable.")
    if p["Mental Focus"] == "Low":
        tips.append("Try working in focused 25-minute blocks with 5-minute breaks.")
    return tips


def build_plan(bundle: model.ModelBundle, profile: pd.DataFrame) -> Plan:
    pred = model.predict(bundle, profile)
    targets = round_targets(pred).iloc[0].to_dict()
    p = profile.iloc[0].to_dict()

    factor_scores = rules.wellness_factors(profile).iloc[0]
    details = _factor_details(p, float(rules.water_target(profile).iloc[0]))
    factors = [
        Factor(name, float(factor_scores[name]), weight, details[name])
        for name, weight in rules.FACTOR_WEIGHTS.items()
    ]
    bedtime = minutes_to_hhmm(p["Wake Up Time (min)"] - targets["Sleep Target (hrs)"] * 60 - FALL_ASLEEP_MIN)

    return Plan(
        profile=p,
        targets=targets,
        category=rules.score_category(targets["Wellness Score"]),
        bedtime=bedtime,
        factors=factors,
        tips=_tips(p, targets),
        alerts=_alerts(p),
    )



def plan_to_markdown(plan: Plan) -> str:
    t, p = plan.targets, plan.profile
    lines = [
        "# My Wellness Plan",
        f"_Generated {date.today():%d %B %Y}_",
        "",
        f"**Wellness score:** {t['Wellness Score']:.0f}/100 ({plan.category})",
        f"**Goal:** {p['Objective']} over {p['Timeline'].lower()}",
        "",
        "## Nutrition",
        f"- Calories: {t['Calories']:,.0f} kcal/day",
        f"- Protein {t['Protein (g)']:.0f} g · Carbs {t['Carbs (g)']:.0f} g · Fats {t['Fats (g)']:.0f} g",
        f"- Meal pattern: {t['Meal Pattern']}",
        f"- Water: {t['Water Target (L)']:.1f} L/day",
        "",
        "## Movement",
        f"- Workout plan: {t['Workout Plan']}",
        f"- Exercise: {t['Exercise Target (min/day)']:.0f} min/day",
        f"- Steps: {t['Steps Target']:,.0f}/day",
        "",
        "## Sleep & mind",
        f"- Sleep: {t['Sleep Target (hrs)']:.2g} h/night: in bed by {plan.bedtime} to wake at "
        f"{minutes_to_hhmm(p['Wake Up Time (min)'])}",
        f"- Mindfulness: {t['Mindfulness Practice']}",
    ]
    if plan.focus_areas:
        lines += ["", "## Focus areas"] + [f"- {f.name}: {f.detail}" for f in plan.focus_areas[:3]]
    if plan.tips:
        lines += ["", "## Tips"] + [f"- {tip}" for tip in plan.tips]
    if plan.alerts:
        lines += ["", "## Health notes"] + [f"- {a}" for a in plan.alerts]
    lines += [
        "",
        "---",
        "_Educational project trained on synthetic data. Not medical advice. Consult a qualified "
        "professional before making significant changes._",
    ]
    return "\n".join(lines) + "\n"
