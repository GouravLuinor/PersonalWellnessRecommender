import pytest

from wellness import recommend, schema


def test_build_profile_derives_bmi(profile):
    p = profile(**{"Height (cm)": 180, "Weight (kg)": 81.0})
    assert p["BMI"].iloc[0] == 25.0
    assert list(p.columns) == schema.FEATURES


def test_build_profile_rejects_missing_fields():
    with pytest.raises(ValueError, match="Missing profile fields"):
        recommend.build_profile(**{"Height (cm)": 170, "Weight (kg)": 70})


@pytest.mark.parametrize(("minutes", "text"), [(0, "00:00"), (390, "06:30"), (-30, "23:30"), (1455, "00:15")])
def test_minutes_to_hhmm_wraps_midnight(minutes, text):
    assert recommend.minutes_to_hhmm(minutes) == text


def test_plan_bedtime_is_consistent(bundle, profile):
    plan = recommend.build_plan(bundle, profile(**{"Wake Up Time (min)": 360}))
    sleep_min = plan.targets["Sleep Target (hrs)"] * 60 + recommend.FALL_ASLEEP_MIN
    assert plan.bedtime == recommend.minutes_to_hhmm(360 - sleep_min)


def test_focus_areas_rank_worst_first(bundle, profile):
    plan = recommend.build_plan(bundle, profile(**{"Stress Level": "High", "Exercise (min/day)": 0}))
    names = [f.name for f in plan.focus_areas]
    assert {"Stress", "Exercise"} <= set(names[:3])
    assert all(f.score >= 0.85 for f in plan.strengths)


@pytest.mark.parametrize(
    ("bp", "phrase"),
    [((185, 100), "crisis"), ((145, 85), "high range"), ((118, 76), None)],
)
def test_blood_pressure_alerts(bundle, profile, bp, phrase):
    plan = recommend.build_plan(bundle, profile(**{"Systolic BP": bp[0], "Diastolic BP": bp[1]}))
    bp_alerts = [a for a in plan.alerts if "blood pressure" in a]
    if phrase is None:
        assert not bp_alerts
    else:
        assert len(bp_alerts) == 1 and phrase in bp_alerts[0]


def test_tips_reflect_profile(bundle, profile):
    plan = recommend.build_plan(bundle, profile(**{"Diet Type": "Vegan", "Water Intake (L)": 0.8}))
    assert any("B12" in t for t in plan.tips)
    assert any("water" in t for t in plan.tips)


def test_every_recommendation_has_a_description():
    for option in schema.WORKOUT_PLANS + schema.MEAL_PATTERNS + schema.MINDFULNESS_PRACTICES:
        assert option in recommend.DESCRIPTIONS


def test_markdown_export(bundle, profile):
    md = recommend.plan_to_markdown(recommend.build_plan(bundle, profile()))
    for heading in ["# My Wellness Plan", "## Nutrition", "## Movement", "## Sleep & mind"]:
        assert heading in md
    assert "Not medical advice" in md
