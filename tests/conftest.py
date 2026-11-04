import pandas as pd
import pytest

from wellness import data, model, recommend


def make_profile(**overrides) -> pd.DataFrame:
    values = {
        "Sex": "Female", "Age": 32, "Height (cm)": 168, "Weight (kg)": 66.0,
        "Objective": "Maintenance", "Timeline": "3 Months", "Diet Type": "Balanced",
        "Activity Level": "Lightly Active", "Workout Type": "Cardio", "Exercise (min/day)": 25,
        "Daily Steps": 6500, "Sleep Duration (hrs)": 7.0, "Sleep Quality": "Good",
        "Wake Up Time (min)": 420, "Stress Level": "Moderate", "Mood": "Neutral",
        "Mental Focus": "Medium", "Water Intake (L)": 2.0, "Resting Heart Rate": 66,
        "Systolic BP": 118, "Diastolic BP": 76,
    }
    values.update(overrides)
    return recommend.build_profile(**values)


@pytest.fixture
def profile():
    return make_profile


@pytest.fixture(scope="session")
def dataset():
    return data.generate_dataset(n=4000, seed=7)


@pytest.fixture(scope="session")
def bundle(dataset):
    return model.train(dataset, n_estimators=60)
