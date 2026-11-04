import joblib

from wellness import model, schema


def test_models_beat_naive_baselines(bundle):
    for target, m in bundle.metrics.items():
        if m["kind"] == "regression":
            assert m["r2"] > 0.5, (target, m)
        else:
            assert m["accuracy"] > m["baseline"] + 0.3, (target, m)


def test_predictions_have_all_targets(bundle, profile):
    pred = model.predict(bundle, profile())
    assert list(pred.columns) == schema.TARGETS
    assert 0 <= pred["Wellness Score"].iloc[0] <= 100


def test_predictions_respond_to_inputs(bundle, profile):
    light = model.predict(bundle, profile(**{"Weight (kg)": 55.0})).iloc[0]
    heavy = model.predict(bundle, profile(**{"Weight (kg)": 95.0})).iloc[0]
    assert heavy["Calories"] > light["Calories"] + 150
    assert heavy["Water Target (L)"] > light["Water Target (L)"]

    gain = model.predict(bundle, profile(Objective="Weight Gain")).iloc[0]
    assert gain["Workout Plan"] == "Strength Training"


def test_predictions_are_deterministic(bundle, profile):
    a = model.predict(bundle, profile())
    b = model.predict(bundle, profile())
    assert a.equals(b)


def test_feature_importance_covers_inputs(bundle):
    assert set(bundle.feature_importance.index) == set(schema.FEATURES)


def test_load_or_train_reuses_saved_bundle(tmp_path, dataset, bundle):
    path = tmp_path / "models.joblib"
    joblib.dump(bundle, path)
    loaded = model.load_or_train(dataset, path)
    assert loaded.metrics == bundle.metrics


def test_load_or_train_retrains_on_stale_bundle(tmp_path, dataset, bundle, monkeypatch):
    path = tmp_path / "models.joblib"
    joblib.dump(bundle, path)
    monkeypatch.setattr(model.schema, "DATA_VERSION", bundle.data_version + 1)
    calls = []
    monkeypatch.setattr(model, "train", lambda df: calls.append(1) or bundle)
    model.load_or_train(dataset, path)
    assert calls == [1]
