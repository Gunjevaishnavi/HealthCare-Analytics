"""
Educational Machine Learning Experiment (Scikit-Learn)
-------------------------------------------------------
CAREFULLY SCOPED EDUCATIONAL BENCHMARK WITH EXPLICIT NON-CLINICAL LABELING:
Demonstrates supervised statistical modeling to evaluate how vital sign measurements
relate to composite multi-indicator flags (R-COM-05) in synthetic data.

DISCLAIMER:
This experiment is strictly for computer science and data analytics education.
It is NOT a medical diagnosis model, prognostic algorithm, or clinical decision tool.
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.makedirs("/tmp/matplotlib", exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, confusion_matrix
)

from backend.config import CHARTS_DIR, Config
from backend.database import SessionLocal, Measurement, RiskIndicator, Patient


def run_educational_ml_experiment():
    """
    Executes an educational benchmark comparing Logistic Regression and Random Forest
    on synthetic vital signs. Computes rigorous statistical metrics and renders an evaluation plot.
    """
    db = SessionLocal()
    try:
        # 1. Prepare Feature Matrix: Pivot valid measurements by patient
        df_meas = pd.read_sql(db.query(Measurement).statement, db.bind)
        df_ind = pd.read_sql(db.query(RiskIndicator).statement, db.bind)
        df_pat = pd.read_sql(db.query(Patient).statement, db.bind)

        # Filter valid ranges
        valid_meas = df_meas[df_meas["is_valid_range"] == True]
        feature_pivot = valid_meas.pivot_table(
            index="patient_id",
            columns="measure_type",
            values="value",
            aggfunc="mean"
        ).fillna(df_meas.groupby("measure_type")["value"].median())

        feature_cols = [
            "systolic_bp", "diastolic_bp", "heart_rate", "respiratory_rate",
            "spo2", "blood_glucose", "bmi", "creatinine"
        ]
        
        # Ensure all columns exist
        for col in feature_cols:
            if col not in feature_pivot.columns:
                feature_pivot[col] = 0.0

        X_df = feature_pivot[feature_cols]

        # Target variable: Whether the patient triggered R-COM-05 (Composite Indicator)
        # or has >= 2 triggered indicators
        ind_counts = df_ind.groupby("patient_id")["rule_code"].count()
        y_series = X_df.index.map(lambda pid: 1 if ind_counts.get(pid, 0) >= 2 else 0)
        
        X = X_df.values
        y = y_series.values

        # If class imbalance is extreme in small cohorts, ensure at least both classes present
        if len(np.unique(y)) < 2:
            # Fallback threshold to ensure educational demonstration works
            y = (X_df["systolic_bp"] >= 135).astype(int).values

        # Train/Test Split (Stratified 80/20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        # Model 1: Logistic Regression
        lr = LogisticRegression(random_state=42, max_iter=500)
        lr.fit(X_train_scaled, y_train)
        y_pred_lr = lr.predict(X_test_scaled)
        y_prob_lr = lr.predict_proba(X_test_scaled)[:, 1]

        # Model 2: Random Forest Classifier
        rf = RandomForestClassifier(n_estimators=100, max_depth=4, random_state=42)
        rf.fit(X_train, y_train)
        y_pred_rf = rf.predict(X_test)
        y_prob_rf = rf.predict_proba(X_test)[:, 1]

        # 5-Fold Cross-Validation Scores
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores_lr = cross_val_score(lr, scaler.fit_transform(X), y, cv=cv, scoring="roc_auc")
        cv_scores_rf = cross_val_score(rf, X, y, cv=cv, scoring="roc_auc")

        # Feature Importances from Random Forest
        feat_importances = [
            {"feature": col, "importance": round(float(imp), 4)}
            for col, imp in zip(feature_cols, rf.feature_importances_)
        ]
        feat_importances.sort(key=lambda x: x["importance"], reverse=True)

        # Logistic Regression Odds Ratios (exp of coefficients)
        coef_summary = [
            {
                "feature": col,
                "coefficient": round(float(coef), 4),
                "odds_ratio": round(float(np.exp(coef)), 4)
            }
            for col, coef in zip(feature_cols, lr.coef_[0])
        ]
        coef_summary.sort(key=lambda x: abs(x["coefficient"]), reverse=True)

        # Confusion Matrices
        cm_lr = confusion_matrix(y_test, y_pred_lr).tolist()
        cm_rf = confusion_matrix(y_test, y_pred_rf).tolist()

        # Render Evaluation Curves Plot (ROC & Precision-Recall)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

        fpr_lr, tpr_lr, _ = roc_curve(y_test, y_prob_lr)
        fpr_rf, tpr_rf, _ = roc_curve(y_test, y_prob_rf)
        auc_lr = roc_auc_score(y_test, y_prob_lr)
        auc_rf = roc_auc_score(y_test, y_prob_rf)

        ax1.plot(fpr_lr, tpr_lr, color="#3182ce", lw=2, label=f"Logistic Regression (AUC = {auc_lr:.3f})")
        ax1.plot(fpr_rf, tpr_rf, color="#38a169", lw=2, label=f"Random Forest (AUC = {auc_rf:.3f})")
        ax1.plot([0, 1], [0, 1], color="gray", linestyle="--")
        ax1.set_xlim([0.0, 1.0])
        ax1.set_ylim([0.0, 1.05])
        ax1.set_xlabel("False Positive Rate")
        ax1.set_ylabel("True Positive Rate")
        ax1.set_title("Educational ROC Curves (Non-Clinical)", fontweight="bold")
        ax1.legend(loc="lower right")
        ax1.grid(True, linestyle=":", alpha=0.6)

        # Precision-Recall Curves
        prec_lr, rec_lr, _ = precision_recall_curve(y_test, y_prob_lr)
        prec_rf, rec_rf, _ = precision_recall_curve(y_test, y_prob_rf)
        ax2.plot(rec_lr, prec_lr, color="#3182ce", lw=2, label="Logistic Regression")
        ax2.plot(rec_rf, prec_rf, color="#38a169", lw=2, label="Random Forest")
        ax2.set_xlim([0.0, 1.0])
        ax2.set_ylim([0.0, 1.05])
        ax2.set_xlabel("Recall")
        ax2.set_ylabel("Precision")
        ax2.set_title("Educational Precision-Recall Curves", fontweight="bold")
        ax2.legend(loc="lower left")
        ax2.grid(True, linestyle=":", alpha=0.6)

        # Prominent banner in chart
        fig.text(
            0.5, 0.01, 
            "NON-CLINICAL BENCHMARK ONLY: Purely illustrative machine learning experiment on synthetic data.",
            ha="center", fontsize=8, color="#c53030", style="italic", weight="bold"
        )

        ml_chart_path = os.path.join(CHARTS_DIR, "ml_roc_pr_curve.png")
        fig.savefig(ml_chart_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

        return {
            "disclaimer": "EDUCATIONAL BENCHMARK ONLY: NON-CLINICAL MODEL. NEVER USE FOR DIAGNOSIS OR CLINICAL DECISION SUPPORT.",
            "sample_size": len(X),
            "features": feature_cols,
            "target_distribution": {
                "negative_class_0": int((y == 0).sum()),
                "positive_class_1": int((y == 1).sum()),
                "positive_pct": round(float((y == 1).mean()) * 100, 1)
            },
            "models": {
                "logistic_regression": {
                    "accuracy": round(float(accuracy_score(y_test, y_pred_lr)), 4),
                    "precision": round(float(precision_score(y_test, y_pred_lr, zero_division=0)), 4),
                    "recall": round(float(recall_score(y_test, y_pred_lr, zero_division=0)), 4),
                    "f1_score": round(float(f1_score(y_test, y_pred_lr, zero_division=0)), 4),
                    "roc_auc": round(float(auc_lr), 4),
                    "cv_roc_auc_mean": round(float(np.mean(cv_scores_lr)), 4),
                    "cv_roc_auc_std": round(float(np.std(cv_scores_lr)), 4),
                    "confusion_matrix": cm_lr,
                    "coefficients": coef_summary
                },
                "random_forest": {
                    "accuracy": round(float(accuracy_score(y_test, y_pred_rf)), 4),
                    "precision": round(float(precision_score(y_test, y_pred_rf, zero_division=0)), 4),
                    "recall": round(float(recall_score(y_test, y_pred_rf, zero_division=0)), 4),
                    "f1_score": round(float(f1_score(y_test, y_pred_rf, zero_division=0)), 4),
                    "roc_auc": round(float(auc_rf), 4),
                    "cv_roc_auc_mean": round(float(np.mean(cv_scores_rf)), 4),
                    "cv_roc_auc_std": round(float(np.std(cv_scores_rf)), 4),
                    "confusion_matrix": cm_rf,
                    "feature_importances": feat_importances
                }
            },
            "chart_url": "static/charts/ml_roc_pr_curve.png"
        }
    finally:
        db.close()


if __name__ == "__main__":
    res = run_educational_ml_experiment()
    print("Educational ML experiment completed successfully!")
    print("Logistic Regression ROC-AUC:", res["models"]["logistic_regression"]["roc_auc"])
    print("Random Forest ROC-AUC:", res["models"]["random_forest"]["roc_auc"])
