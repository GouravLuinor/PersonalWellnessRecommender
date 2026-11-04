import pandas as pd

from wellness import data, schema


def test_dataset_has_expected_columns_and_no_missing_values(dataset):
    assert list(dataset.columns) == schema.FEATURES + schema.TARGETS
    assert not dataset.isna().any().any()
    assert len(dataset) == 4000


def test_generation_is_deterministic():
    a = data.generate_dataset(n=300, seed=1)
    b = data.generate_dataset(n=300, seed=1)
    c = data.generate_dataset(n=300, seed=2)
    pd.testing.assert_frame_equal(a, b)
    assert not a.equals(c)


def test_categorical_values_are_valid(dataset):
    options = {
        "Sex": schema.SEXES, "Objective": schema.OBJECTIVES, "Timeline": schema.TIMELINES,
        "Diet Type": schema.DIETS, "Workout Type": schema.WORKOUT_TYPES, "Activity Level": schema.ACTIVITY_LEVELS,
        "Sleep Quality": schema.SLEEP_QUALITIES, "Stress Level": schema.STRESS_LEVELS, "Mood": schema.MOODS,
        "Mental Focus": schema.FOCUS_LEVELS, "Workout Plan": schema.WORKOUT_PLANS,
        "Meal Pattern": schema.MEAL_PATTERNS, "Mindfulness Practice": schema.MINDFULNESS_PRACTICES,
    }
    for col, allowed in options.items():
        assert set(dataset[col]) <= set(allowed), col


def test_values_are_physiologically_plausible(dataset):
    assert dataset["Age"].between(18, 70).all()
    assert dataset["BMI"].between(14, 50).all()
    assert dataset["Calories"].between(1000, 4500).all()
    assert dataset["Wellness Score"].between(0, 100).all()
    assert (dataset["Systolic BP"] > dataset["Diastolic BP"]).mean() > 0.99


def test_modeled_correlations_exist(dataset):
    # Inputs drive targets: heavier people need more calories, stressed people sleep worse.
    assert dataset["Weight (kg)"].corr(dataset["Calories"]) > 0.25
    mean_sleep = dataset.groupby("Stress Level")["Sleep Duration (hrs)"].mean()
    assert mean_sleep["High"] < mean_sleep["Low"]


def test_load_or_create_caches_and_recovers(tmp_path):
    path = tmp_path / "ds.csv"
    first = data.load_or_create_dataset(path, n=200)
    assert path.exists()
    second = data.load_or_create_dataset(path, n=200)
    pd.testing.assert_frame_equal(first, second, check_dtype=False)

    path.write_text("not,a\nvalid,dataset\n")
    recovered = data.load_or_create_dataset(path, n=200)
    assert list(recovered.columns) == schema.FEATURES + schema.TARGETS
