"""
Healthcare Data Visualization Engine (Matplotlib)
--------------------------------------------------
Generates publication-quality operational analytics and measurement trend plots.
Saves rendered charts to static/charts/ for display in web dashboards and reports.
"""

import os
os.environ["MPLCONFIGDIR"] = "/tmp/matplotlib"
os.makedirs("/tmp/matplotlib", exist_ok=True)

import matplotlib
matplotlib.use("Agg") # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from backend.config import CHARTS_DIR
from backend.database import SessionLocal, Patient, Visit, Measurement, RiskIndicator, Department


def generate_all_charts():
    """Generates all operational analytics and trend figures."""
    db = SessionLocal()
    try:
        # Load DataFrames
        df_patients = pd.read_sql(db.query(Patient).statement, db.bind)
        df_visits = pd.read_sql(db.query(Visit).statement, db.bind)
        df_measurements = pd.read_sql(db.query(Measurement).statement, db.bind)
        df_indicators = pd.read_sql(db.query(RiskIndicator).statement, db.bind)
        df_depts = pd.read_sql(db.query(Department).statement, db.bind)

        # Matplotlib theme settings
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams.update({
            "font.family": "sans-serif",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "figure.autolayout": True
        })

        # Chart 1: Department Admissions & Admission Types (2 Subplots)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
        
        # Dept counts
        visits_merged = df_visits.merge(df_depts, on="department_id", how="left")
        dept_counts = visits_merged["department_name"].value_counts()
        colors = ["#2b6cb0", "#319795", "#38a169", "#d69e2e", "#e53e3e", "#805ad5", "#dd6b20", "#3182ce"]
        
        ax1.barh(dept_counts.index, dept_counts.values, color=colors[:len(dept_counts)], edgecolor="none")
        ax1.set_title("Total Admissions by Hospital Department (Synthetic)")
        ax1.set_xlabel("Number of Admissions")
        ax1.grid(axis="x", linestyle="--", alpha=0.7)

        # Admission types distribution pie
        adm_counts = df_visits["admission_type"].value_counts()
        ax2.pie(
            adm_counts.values, 
            labels=adm_counts.index, 
            autopct="%1.1f%%", 
            startangle=140,
            colors=["#e53e3e", "#3182ce", "#dd6b20", "#38a169"],
            wedgeprops=dict(width=0.6, edgecolor='w')
        )
        ax2.set_title("Admissions Breakdown by Triage/Type")

        chart1_path = os.path.join(CHARTS_DIR, "dept_admissions_trend.png")
        fig.savefig(chart1_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

        # Chart 2: Key Measurement Distributions & Physiological Reference Bands
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        measures_to_plot = [
            ("systolic_bp", "Systolic Blood Pressure (mmHg)", 90, 120, "#2b6cb0", axes[0, 0]),
            ("heart_rate", "Resting Heart Rate (bpm)", 60, 100, "#dd6b20", axes[0, 1]),
            ("blood_glucose", "Fasting Blood Glucose (mg/dL)", 70, 99, "#319795", axes[1, 0]),
            ("spo2", "Oxygen Saturation SpO2 (%)", 95, 100, "#38a169", axes[1, 1])
        ]

        for m_type, title, norm_min, norm_max, col, ax in measures_to_plot:
            vals = df_measurements[df_measurements["measure_type"] == m_type]["value"].dropna().to_numpy()
            # Trim extreme anomalies for clean distribution display
            p01, p99 = np.percentile(vals, [1, 99])
            filtered = vals[(vals >= p01) & (vals <= p99)]

            ax.hist(filtered, bins=25, color=col, alpha=0.7, edgecolor="black", density=True)
            # Highlight standard reference range
            ax.axvspan(norm_min, norm_max, color="green", alpha=0.15, label=f"Standard Reference [{norm_min}-{norm_max}]")
            ax.axvline(np.median(filtered), color="red", linestyle="--", linewidth=1.8, label=f"Median: {np.median(filtered):.1f}")
            ax.set_title(title, fontweight="bold")
            ax.set_ylabel("Density")
            ax.legend(loc="upper right", fontsize=8)
            ax.grid(True, linestyle=":", alpha=0.6)

        chart2_path = os.path.join(CHARTS_DIR, "measurement_distributions.png")
        fig.savefig(chart2_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

        # Chart 3: Risk Indicator Frequencies & Age-Band Distribution
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5))

        ind_counts = df_indicators["rule_code"].value_counts()
        rule_colors = {"R-VIT-01": "#e53e3e", "R-GLU-02": "#d69e2e", "R-RES-03": "#3182ce", "R-REN-04": "#805ad5", "R-COM-05": "#2d3748"}
        bar_colors = [rule_colors.get(c, "#4a5568") for c in ind_counts.index]
        
        ax1.bar(ind_counts.index, ind_counts.values, color=bar_colors, edgecolor="black", width=0.55)
        ax1.set_title("Trigger Counts by Illustrative Risk Rule")
        ax1.set_xlabel("Rule Code")
        ax1.set_ylabel("Flagged Instances")
        for i, v in enumerate(ind_counts.values):
            ax1.text(i, v + 2, str(v), ha="center", fontweight="bold")

        # Age band vs Indicators stacked
        merged_ind = df_indicators.merge(df_patients[["patient_id", "age_band"]], on="patient_id", how="left")
        crosstab = pd.crosstab(merged_ind["age_band"], merged_ind["rule_code"])
        crosstab.plot(kind="bar", stacked=True, ax=ax2, colormap="viridis", edgecolor="black", alpha=0.85)
        ax2.set_title("Risk Indicator Distribution Across Age Bands")
        ax2.set_xlabel("Age Band")
        ax2.set_ylabel("Number of Flags")
        ax2.legend(title="Rule Code", fontsize=8)
        ax2.grid(axis="y", linestyle="--", alpha=0.7)

        chart3_path = os.path.join(CHARTS_DIR, "indicator_distribution.png")
        fig.savefig(chart3_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

        # Chart 4: Correlation Matrix of Physiological Measurements
        fig, ax = plt.subplots(figsize=(8, 6.5))
        # Pivot measurements table to patient level (using mean of valid values per patient)
        pivoted = df_measurements[df_measurements["is_valid_range"] == True].pivot_table(
            index="patient_id", 
            columns="measure_type", 
            values="value", 
            aggfunc="mean"
        )
        
        corr = pivoted.corr()
        im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
        ax.set_xticks(range(len(corr.columns)))
        ax.set_yticks(range(len(corr.columns)))
        ax.set_xticklabels(corr.columns, rotation=45, ha="right")
        ax.set_yticklabels(corr.columns)
        
        # Annotate correlation numbers
        for i in range(len(corr.columns)):
            for j in range(len(corr.columns)):
                val = corr.iloc[i, j]
                if not np.isnan(val):
                    ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="black" if abs(val) < 0.6 else "white", fontsize=8)

        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="Pearson Correlation")
        ax.set_title("Correlation Heatmap: Synthetic Physiological Markers", fontweight="bold")

        chart4_path = os.path.join(CHARTS_DIR, "correlation_heatmap.png")
        fig.savefig(chart4_path, dpi=180, bbox_inches="tight")
        plt.close(fig)

        print("All 4 analytical charts generated successfully!")
        return {
            "dept_chart": "static/charts/dept_admissions_trend.png",
            "dist_chart": "static/charts/measurement_distributions.png",
            "indicator_chart": "static/charts/indicator_distribution.png",
            "corr_chart": "static/charts/correlation_heatmap.png"
        }
    finally:
        db.close()


if __name__ == "__main__":
    generate_all_charts()
