"""End-to-end smoke tests of the Streamlit app using Streamlit's AppTest harness."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


@pytest.fixture(scope="module")
def app():
    at = AppTest.from_file(APP, default_timeout=600).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_first_load_shows_sample_plan(app):
    assert any("sample plan" in i.value for i in app.info)
    assert {m.label for m in app.metric} >= {"Sleep target", "Daily steps", "Calories"}


def test_submitting_profile_personalises_plan(app):
    before = {m.label: m.value for m in app.metric}
    app.sidebar.number_input[2].set_value(110.0)  # weight
    app.sidebar.number_input[4].set_value(150)  # systolic BP
    app.sidebar.button[0].click().run()

    assert not app.exception, [e.value for e in app.exception]
    assert not any("sample plan" in i.value for i in app.info)
    after = {m.label: m.value for m in app.metric}
    assert after["Calories"] != before["Calories"]
    assert any("blood pressure" in w.value for w in app.warning)


def test_compare_tab_switches_metric(app):
    app.segmented_control(key="compare_metric").set_value("BMI").run()
    assert not app.exception
    assert any("BMI" in m.value and "higher than" in m.value for m in app.markdown)
