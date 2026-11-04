import pytest

from wellness import rules


def test_bmr_matches_mifflin_st_jeor(profile):
    male = profile(Sex="Male", Age=30, **{"Height (cm)": 180, "Weight (kg)": 80.0})
    female = profile(Sex="Female", Age=30, **{"Height (cm)": 165, "Weight (kg)": 60.0})
    assert rules.bmr(male).iloc[0] == pytest.approx(10 * 80 + 6.25 * 180 - 5 * 30 + 5)
    assert rules.bmr(female).iloc[0] == pytest.approx(10 * 60 + 6.25 * 165 - 5 * 30 - 161)


def test_calories_follow_goal(profile):
    cals = {
        goal: rules.nutrition_targets(profile(Objective=goal))["Calories"].iloc[0]
        for goal in ["Weight Loss", "Maintenance", "Weight Gain"]
    }
    assert cals["Weight Loss"] < cals["Maintenance"] < cals["Weight Gain"]


def test_shorter_timeline_means_bigger_deficit(profile):
    fast = rules.nutrition_targets(profile(Objective="Weight Loss", Timeline="1 Month"))["Calories"].iloc[0]
    slow = rules.nutrition_targets(profile(Objective="Weight Loss", Timeline="6 Months"))["Calories"].iloc[0]
    assert fast < slow


def test_calories_never_below_safe_floor(profile):
    tiny = profile(Objective="Weight Loss", Timeline="1 Month", Age=70,
                   **{"Height (cm)": 145, "Weight (kg)": 40.0, "Activity Level": "Sedentary"})
    assert rules.nutrition_targets(tiny)["Calories"].iloc[0] >= 1200


def test_macros_add_up_to_calories(profile):
    for diet in ["Balanced", "Keto", "High Protein"]:
        n = rules.nutrition_targets(profile(**{"Diet Type": diet})).iloc[0]
        kcal = n["Protein (g)"] * 4 + n["Carbs (g)"] * 4 + n["Fats (g)"] * 9
        assert kcal == pytest.approx(n["Calories"], rel=0.02)


def test_keto_is_low_carb(profile):
    keto = rules.nutrition_targets(profile(**{"Diet Type": "Keto"})).iloc[0]
    assert keto["Carbs (g)"] < 40
    assert keto["Fats (g)"] * 9 > 0.6 * keto["Calories"]


def test_targets_ramp_toward_goal_without_regressing(profile):
    couch = profile(**{"Exercise (min/day)": 0, "Daily Steps": 3000})
    athlete = profile(**{"Exercise (min/day)": 120, "Daily Steps": 18000})
    assert rules.exercise_target(couch).iloc[0] == 20  # 0 + 3-month ramp, below the 30 min goal
    assert rules.steps_target(couch).iloc[0] == 6500
    assert rules.exercise_target(athlete).iloc[0] == 90  # keeps high activity, capped
    assert rules.steps_target(athlete).iloc[0] == 15000


@pytest.mark.parametrize(
    ("overrides", "plan"),
    [
        ({"Objective": "Weight Gain"}, "Strength Training"),
        ({"Objective": "Weight Loss", "Weight (kg)": 110.0}, "Low-Impact Cardio"),
        ({"Objective": "Weight Loss"}, "Cardio + Strength"),
        ({"Stress Level": "High"}, "Yoga & Mobility"),
    ],
)
def test_workout_plan_rules(profile, overrides, plan):
    assert rules.workout_plan(profile(**overrides)).iloc[0] == plan


def test_wellness_score_rewards_healthy_habits(profile):
    healthy = profile(**{"Sleep Duration (hrs)": 8.0, "Sleep Quality": "Excellent", "Stress Level": "Low",
                         "Mood": "Happy", "Daily Steps": 10000, "Exercise (min/day)": 45,
                         "Water Intake (L)": 3.0})
    unhealthy = profile(**{"Sleep Duration (hrs)": 4.5, "Sleep Quality": "Poor", "Stress Level": "High",
                           "Mood": "Sad", "Daily Steps": 2000, "Exercise (min/day)": 0,
                           "Water Intake (L)": 0.8, "Weight (kg)": 110.0, "Systolic BP": 160,
                           "Diastolic BP": 100, "Resting Heart Rate": 95})
    hi, lo = rules.wellness_score(healthy).iloc[0], rules.wellness_score(unhealthy).iloc[0]
    assert 90 <= hi <= 100
    assert 0 <= lo < 30


def test_factors_are_bounded(dataset):
    factors = rules.wellness_factors(dataset)
    assert factors.min().min() >= 0 and factors.max().max() <= 1
    assert list(factors.columns) == list(rules.FACTOR_WEIGHTS)


@pytest.mark.parametrize(("score", "category"), [(95, "Excellent"), (70, "Good"), (50, "Fair"), (20, "Needs attention")])
def test_score_category(score, category):
    assert rules.score_category(score) == category
