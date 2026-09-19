from pathlib import Path

import json
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ============================================================
# WAYANAD SPATIAL BASELINE MODEL TRAINING
# ============================================================
#
# Model A:
#   slope + WorldCover + GSI
#
# Model B:
#   slope + WorldCover
#
# Same:
#   - spatial train/validation/test split
#   - algorithm
#   - class weighting
#   - random seed
#
# Primary metric:
#   Average Precision / PR-AUC
#
# IMPORTANT:
#   Test data remains untouched during model/threshold selection.
#
# ============================================================


ROOT = Path(__file__).resolve().parents[1]

FEATURE_DIR = (
    ROOT
    / "data"
    / "processed"
    / "features"
)

MODEL_DIR = (
    ROOT
    / "models"
    / "spatial_baseline"
)

REPORT_DIR = (
    ROOT
    / "data"
    / "processed"
    / "model_results"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


MODEL_A_FILE = (
    FEATURE_DIR
    / "wayanad_ml_baseline_with_gsi.parquet"
)

MODEL_B_FILE = (
    FEATURE_DIR
    / "wayanad_ml_baseline_without_gsi.parquet"
)


TARGET = "historical_landslide"


MODEL_A_FEATURES = [
    "slope_degrees",
    "tree_fraction",
    "shrub_fraction",
    "grass_fraction",
    "crop_fraction",
    "builtup_fraction",
    "bare_fraction",
    "water_fraction",
    "wetland_fraction",
    "gsi_susceptibility",
    "gsi_coverage",
]


MODEL_B_FEATURES = [
    "slope_degrees",
    "tree_fraction",
    "shrub_fraction",
    "grass_fraction",
    "crop_fraction",
    "builtup_fraction",
    "bare_fraction",
    "water_fraction",
    "wetland_fraction",
]


RANDOM_STATE = 42


# ============================================================
# RANDOM FOREST CONFIGURATION
# ============================================================

RF_PARAMS = {
    "n_estimators": 300,
    "max_depth": None,
    "min_samples_leaf": 5,
    "max_features": "sqrt",
    "class_weight": "balanced",
    "random_state": RANDOM_STATE,
    "n_jobs": -1,
}


# ============================================================
# HELPERS
# ============================================================

def header(title):

    print()
    print("=" * 90)
    print(title)
    print("=" * 90)


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(path):

    header(
        f"LOADING {path.name}"
    )

    if not path.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{path}"
        )

    df = pd.read_parquet(
        path
    )

    print(
        f"Shape: {df.shape}"
    )

    required = [
        "row",
        "col",
        "split",
        TARGET,
    ]

    missing = [
        column
        for column in required
        if column not in df.columns
    ]

    if missing:

        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df


# ============================================================
# PREPARE SPLITS
# ============================================================

def prepare_splits(
    df,
    features,
):

    header(
        "PREPARING SPATIAL SPLITS"
    )

    X = df[
        features
    ].copy()

    y = df[
        TARGET
    ].astype(
        np.uint8
    )

    split = df[
        "split"
    ]

    train_mask = (
        split == "train"
    )

    validation_mask = (
        split == "validation"
    )

    test_mask = (
        split == "test"
    )

    X_train = X.loc[
        train_mask
    ]

    y_train = y.loc[
        train_mask
    ]

    X_validation = X.loc[
        validation_mask
    ]

    y_validation = y.loc[
        validation_mask
    ]

    X_test = X.loc[
        test_mask
    ]

    y_test = y.loc[
        test_mask
    ]

    print(
        f"Train:      {len(X_train):,}"
    )

    print(
        f"Validation: {len(X_validation):,}"
    )

    print(
        f"Test:       {len(X_test):,}"
    )

    print()

    print(
        f"Train positives: "
        f"{int(y_train.sum()):,}"
    )

    print(
        f"Validation positives: "
        f"{int(y_validation.sum()):,}"
    )

    print(
        f"Test positives: "
        f"{int(y_test.sum()):,}"
    )

    if len(X_train) == 0:
        raise ValueError("Training split is empty.")

    if len(X_validation) == 0:
        raise ValueError("Validation split is empty.")

    if len(X_test) == 0:
        raise ValueError("Test split is empty.")

    return (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    )


# ============================================================
# TRAIN MODEL
# ============================================================

def train_model(
    X_train,
    y_train,
    model_name,
):

    header(
        f"TRAINING {model_name}"
    )

    print(
        "Algorithm: Random Forest"
    )

    print(
        f"Trees: {RF_PARAMS['n_estimators']}"
    )

    print(
        f"Minimum samples per leaf: "
        f"{RF_PARAMS['min_samples_leaf']}"
    )

    print(
        "Class weighting: balanced"
    )

    model = RandomForestClassifier(
        **RF_PARAMS
    )

    model.fit(
        X_train,
        y_train,
    )

    print(
        "Training complete."
    )

    return model


# ============================================================
# PREDICTIONS
# ============================================================

def predict_probabilities(
    model,
    X,
):

    probabilities = model.predict_proba(
        X
    )[:, 1]

    if not np.isfinite(
        probabilities
    ).all():

        raise ValueError(
            "Model produced non-finite probabilities."
        )

    return probabilities


# ============================================================
# METRICS
# ============================================================

def calculate_probability_metrics(
    y_true,
    probabilities,
):

    return {
        "pr_auc": float(
            average_precision_score(
                y_true,
                probabilities,
            )
        ),
        "roc_auc": float(
            roc_auc_score(
                y_true,
                probabilities,
            )
        ),
    }


# ============================================================
# THRESHOLD METRICS
# ============================================================

def calculate_threshold_metrics(
    y_true,
    probabilities,
    threshold,
):

    predictions = (
        probabilities
        >= threshold
    ).astype(
        np.uint8
    )

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        predictions,
        labels=[
            0,
            1,
        ],
    ).ravel()

    precision = precision_score(
        y_true,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_true,
        predictions,
        zero_division=0,
    )

    f1 = f1_score(
        y_true,
        predictions,
        zero_division=0,
    )

    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
        "predicted_positive": int(
            predictions.sum()
        ),
    }


# ============================================================
# SELECT VALIDATION THRESHOLD
# ============================================================

def select_validation_threshold(
    y_validation,
    validation_probabilities,
):

    header(
        "SELECTING VALIDATION THRESHOLD"
    )

    thresholds = np.arange(
        0.05,
        0.951,
        0.05,
    )

    rows = []

    for threshold in thresholds:

        metrics = calculate_threshold_metrics(
            y_validation,
            validation_probabilities,
            threshold,
        )

        rows.append(
            metrics
        )

    results = pd.DataFrame(
        rows
    )

    # --------------------------------------------------------
    # Threshold is selected ONLY from validation.
    # --------------------------------------------------------

    best_index = (
        results[
            "f1"
        ]
        .idxmax()
    )

    best = results.loc[
        best_index
    ]

    print(
        results.to_string(
            index=False
        )
    )

    print()

    print(
        "Selected validation threshold:"
    )

    print(
        f"Threshold = "
        f"{best['threshold']:.2f}"
    )

    print(
        f"Precision = "
        f"{best['precision']:.6f}"
    )

    print(
        f"Recall = "
        f"{best['recall']:.6f}"
    )

    print(
        f"F1 = "
        f"{best['f1']:.6f}"
    )

    return (
        float(
            best[
                "threshold"
            ]
        ),
        results,
    )


# ============================================================
# FINAL TEST EVALUATION
# ============================================================

def evaluate_test(
    model_name,
    model,
    y_test,
    test_probabilities,
    threshold,
):

    header(
        f"FINAL TEST EVALUATION — {model_name}"
    )

    probability_metrics = (
        calculate_probability_metrics(
            y_test,
            test_probabilities,
        )
    )

    threshold_metrics = (
        calculate_threshold_metrics(
            y_test,
            test_probabilities,
            threshold,
        )
    )

    print(
        "Probability metrics:"
    )

    print(
        f"PR-AUC:  "
        f"{probability_metrics['pr_auc']:.6f}"
    )

    print(
        f"ROC-AUC: "
        f"{probability_metrics['roc_auc']:.6f}"
    )

    print()

    print(
        "Threshold metrics:"
    )

    print(
        f"Threshold: "
        f"{threshold_metrics['threshold']:.2f}"
    )

    print(
        f"Precision: "
        f"{threshold_metrics['precision']:.6f}"
    )

    print(
        f"Recall: "
        f"{threshold_metrics['recall']:.6f}"
    )

    print(
        f"F1: "
        f"{threshold_metrics['f1']:.6f}"
    )

    print()

    print(
        "Confusion matrix:"
    )

    print(
        "                 Predicted"
    )

    print(
        "                 0       1"
    )

    print(
        f"Actual 0     "
        f"{threshold_metrics['true_negative']:7d}"
        f" "
        f"{threshold_metrics['false_positive']:7d}"
    )

    print(
        f"Actual 1     "
        f"{threshold_metrics['false_negative']:7d}"
        f" "
        f"{threshold_metrics['true_positive']:7d}"
    )

    return {
        **probability_metrics,
        **threshold_metrics,
    }


# ============================================================
# FEATURE IMPORTANCE
# ============================================================

def save_feature_importance(
    model,
    features,
    model_name,
):

    importance = pd.DataFrame(
        {
            "feature": features,
            "importance": model.feature_importances_,
        }
    )

    importance = importance.sort_values(
        "importance",
        ascending=False,
    ).reset_index(
        drop=True
    )

    print()

    print(
        "Feature importance:"
    )

    print(
        importance.to_string(
            index=False
        )
    )

    safe_name = (
        model_name
        .lower()
        .replace(
            " ",
            "_",
        )
    )

    output = (
        REPORT_DIR
        / f"{safe_name}_feature_importance.csv"
    )

    importance.to_csv(
        output,
        index=False,
    )

    return importance


# ============================================================
# SAVE MODEL
# ============================================================

def save_model(
    model,
    model_name,
    features,
):

    safe_name = (
        model_name
        .lower()
        .replace(
            " ",
            "_",
        )
    )

    path = (
        MODEL_DIR
        / f"{safe_name}.joblib"
    )

    payload = {
        "model": model,
        "features": features,
        "target": TARGET,
        "random_state": RANDOM_STATE,
        "algorithm": "RandomForestClassifier",
        "training_parameters": RF_PARAMS,
    }

    joblib.dump(
        payload,
        path,
    )

    print(
        f"Saved model: {path}"
    )

    return path


# ============================================================
# TRAIN ONE EXPERIMENT
# ============================================================

def run_experiment(
    dataset_path,
    model_name,
    features,
):

    header(
        f"EXPERIMENT: {model_name}"
    )

    df = load_dataset(
        dataset_path
    )

    (
        X_train,
        y_train,
        X_validation,
        y_validation,
        X_test,
        y_test,
    ) = prepare_splits(
        df,
        features,
    )

    model = train_model(
        X_train,
        y_train,
        model_name,
    )

    # --------------------------------------------------------
    # Validation probabilities.
    # --------------------------------------------------------

    validation_probabilities = (
        predict_probabilities(
            model,
            X_validation,
        )
    )

    validation_metrics = (
        calculate_probability_metrics(
            y_validation,
            validation_probabilities,
        )
    )

    print()

    print(
        "Validation PR-AUC:"
        f" {validation_metrics['pr_auc']:.6f}"
    )

    print(
        "Validation ROC-AUC:"
        f" {validation_metrics['roc_auc']:.6f}"
    )

    # --------------------------------------------------------
    # Select threshold using validation ONLY.
    # --------------------------------------------------------

    (
        threshold,
        threshold_table,
    ) = select_validation_threshold(
        y_validation,
        validation_probabilities,
    )

    # --------------------------------------------------------
    # Final test prediction.
    # --------------------------------------------------------

    test_probabilities = (
        predict_probabilities(
            model,
            X_test,
        )
    )

    test_metrics = evaluate_test(
        model_name,
        model,
        y_test,
        test_probabilities,
        threshold,
    )

    # --------------------------------------------------------
    # Feature importance.
    # --------------------------------------------------------

    importance = save_feature_importance(
        model,
        features,
        model_name,
    )

    # --------------------------------------------------------
    # Save model.
    # --------------------------------------------------------

    model_path = save_model(
        model,
        model_name,
        features,
    )

    # --------------------------------------------------------
    # Save threshold table.
    # --------------------------------------------------------

    safe_name = (
        model_name
        .lower()
        .replace(
            " ",
            "_",
        )
    )

    threshold_path = (
        REPORT_DIR
        / f"{safe_name}_validation_thresholds.csv"
    )

    threshold_table.to_csv(
        threshold_path,
        index=False,
    )

    # --------------------------------------------------------
    # Return summary.
    # --------------------------------------------------------

    return {
        "model": model_name,
        "features": len(features),
        "validation_pr_auc": validation_metrics[
            "pr_auc"
        ],
        "validation_roc_auc": validation_metrics[
            "roc_auc"
        ],
        "selected_threshold": threshold,
        "test_pr_auc": test_metrics[
            "pr_auc"
        ],
        "test_roc_auc": test_metrics[
            "roc_auc"
        ],
        "test_precision": test_metrics[
            "precision"
        ],
        "test_recall": test_metrics[
            "recall"
        ],
        "test_f1": test_metrics[
            "f1"
        ],
        "test_true_positive": test_metrics[
            "true_positive"
        ],
        "test_false_positive": test_metrics[
            "false_positive"
        ],
        "test_false_negative": test_metrics[
            "false_negative"
        ],
        "test_true_negative": test_metrics[
            "true_negative"
        ],
        "model_path": str(
            model_path
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main():

    header(
        "WAYANAD SPATIAL BASELINE MODEL TRAINING"
    )

    print(
        "Primary metric: PR-AUC / Average Precision"
    )

    print(
        "Algorithm: Random Forest"
    )

    print(
        "Class imbalance: class_weight='balanced'"
    )

    print(
        "Random state: 42"
    )

    # --------------------------------------------------------
    # Model A.
    # --------------------------------------------------------

    result_a = run_experiment(
        MODEL_A_FILE,
        "model_a_with_gsi",
        MODEL_A_FEATURES,
    )

    # --------------------------------------------------------
    # Model B.
    # --------------------------------------------------------

    result_b = run_experiment(
        MODEL_B_FILE,
        "model_b_without_gsi",
        MODEL_B_FEATURES,
    )

    # --------------------------------------------------------
    # Comparison.
    # --------------------------------------------------------

    header(
        "FINAL CONTROLLED COMPARISON"
    )

    results = pd.DataFrame(
        [
            result_a,
            result_b,
        ]
    )

    display_columns = [
        "model",
        "features",
        "validation_pr_auc",
        "validation_roc_auc",
        "selected_threshold",
        "test_pr_auc",
        "test_roc_auc",
        "test_precision",
        "test_recall",
        "test_f1",
    ]

    print(
        results[
            display_columns
        ].to_string(
            index=False
        )
    )

    # --------------------------------------------------------
    # Save comparison.
    # --------------------------------------------------------

    comparison_path = (
        REPORT_DIR
        / "spatial_baseline_model_comparison.csv"
    )

    results.to_csv(
        comparison_path,
        index=False,
    )

    # --------------------------------------------------------
    # Save JSON.
    # --------------------------------------------------------

    json_path = (
        REPORT_DIR
        / "spatial_baseline_model_comparison.json"
    )

    with open(
        json_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            [
                result_a,
                result_b,
            ],
            f,
            indent=2,
        )

    print()

    print(
        f"Comparison CSV: "
        f"{comparison_path}"
    )

    print(
        f"Comparison JSON: "
        f"{json_path}"
    )

    # --------------------------------------------------------
    # Important interpretation.
    # --------------------------------------------------------

    print()

    print(
        "=" * 90
    )

    print(
        "IMPORTANT INTERPRETATION"
    )

    print(
        "=" * 90
    )

    print(
        "Do not interpret a higher score by itself as proof "
        "that GSI is valid or leakage-free."
    )

    print(
        "The GSI provenance/methodology must still be considered."
    )

    print(
        "This experiment measures whether GSI adds predictive "
        "signal under the same spatial evaluation."
    )

    print()

    print(
        "TRAINING COMPLETE."
    )


if __name__ == "__main__":
    main()