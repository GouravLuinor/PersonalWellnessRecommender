"""Training, evaluation, persistence and inference for the wellness models."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import schema
from .data import GENERATED_DIR

MODEL_PATH = GENERATED_DIR / f"wellness_models_v{schema.DATA_VERSION}.joblib"


@dataclass
class ModelBundle:
    regressor: Pipeline
    classifiers: dict[str, Pipeline]
    metrics: dict[str, dict] = field(default_factory=dict)
    feature_importance: pd.Series | None = None
    sklearn_version: str = sklearn.__version__
    data_version: int = schema.DATA_VERSION


def _preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        [
            ("num", StandardScaler(), schema.NUMERICAL_FEATURES),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), schema.CATEGORICAL_FEATURES),
        ]
    )


def _score_importance(regressor: Pipeline, X: pd.DataFrame, y: pd.Series, seed: int) -> pd.Series:
    """Permutation importance of each input feature for the wellness score."""
    idx = schema.REGRESSION_TARGETS.index("Wellness Score")

    def scorer(est, X_, y_):
        return r2_score(y_, est.predict(X_)[:, idx])

    result = permutation_importance(regressor, X, y, scoring=scorer, n_repeats=3, random_state=seed, n_jobs=1)
    return pd.Series(result.importances_mean, index=X.columns).clip(lower=0).sort_values(ascending=False)


def train(df: pd.DataFrame, seed: int = 42, n_estimators: int = 150) -> ModelBundle:
    X = df[schema.FEATURES]
    y_reg = df[schema.REGRESSION_TARGETS]
    y_clf = df[schema.CLASSIFICATION_TARGETS].astype(str)
    X_tr, X_te, yr_tr, yr_te, yc_tr, yc_te = train_test_split(X, y_reg, y_clf, test_size=0.2, random_state=seed)

    # Gradient boosting captures the additive / multiplicative structure of the
    # targets far better than a random forest (R² ~0.95 vs ~0.8 on held-out data).
    regressor = Pipeline(
        [
            ("prep", _preprocessor()),
            (
                "model",
                MultiOutputRegressor(
                    HistGradientBoostingRegressor(max_iter=400, learning_rate=0.08, random_state=seed)
                ),
            ),
        ]
    )
    regressor.fit(X_tr, yr_tr)

    classifiers = {}
    for col in schema.CLASSIFICATION_TARGETS:
        clf = Pipeline(
            [
                ("prep", _preprocessor()),
                ("model", RandomForestClassifier(n_estimators=n_estimators, min_samples_leaf=2, n_jobs=-1, random_state=seed)),
            ]
        )
        clf.fit(X_tr, yc_tr[col])
        classifiers[col] = clf

    metrics: dict[str, dict] = {}
    pred = pd.DataFrame(regressor.predict(X_te), columns=schema.REGRESSION_TARGETS, index=X_te.index)
    for col in schema.REGRESSION_TARGETS:
        metrics[col] = {
            "kind": "regression",
            "r2": float(r2_score(yr_te[col], pred[col])),
            "mae": float(mean_absolute_error(yr_te[col], pred[col])),
        }
    for col, clf in classifiers.items():
        metrics[col] = {
            "kind": "classification",
            "accuracy": float(accuracy_score(yc_te[col], clf.predict(X_te))),
            "baseline": float(yc_te[col].value_counts(normalize=True).iloc[0]),
        }

    sample = X_te.sample(min(len(X_te), 1000), random_state=seed)
    importance = _score_importance(regressor, sample, yr_te.loc[sample.index, "Wellness Score"], seed)
    return ModelBundle(regressor, classifiers, metrics, importance)


def load_or_train(df: pd.DataFrame, path: Path = MODEL_PATH) -> ModelBundle:
    path = Path(path)
    if path.exists():
        try:
            bundle = joblib.load(path)
            if (
                isinstance(bundle, ModelBundle)
                and bundle.sklearn_version == sklearn.__version__
                and bundle.data_version == schema.DATA_VERSION
            ):
                return bundle
        except Exception:  # corrupt or incompatible pickle -> retrain
            pass
    bundle = train(df)
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path, compress=3)
    return bundle


def predict(bundle: ModelBundle, profile: pd.DataFrame) -> pd.DataFrame:
    """Predict all targets for one or more profiles (rows of ``schema.FEATURES``)."""
    X = profile[schema.FEATURES]
    out = pd.DataFrame(bundle.regressor.predict(X), columns=schema.REGRESSION_TARGETS, index=X.index)
    for col, clf in bundle.classifiers.items():
        out[col] = clf.predict(X)
    out["Wellness Score"] = out["Wellness Score"].clip(0, 100)
    return out
