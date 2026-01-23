import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = "outputs/cell_data.db"

OUT_BASELINE_SAMPLES = "outputs/part4_baseline_samples.csv"
OUT_SAMPLES_BY_PROJECT = "outputs/part4_samples_by_project.csv"
OUT_SUBJECTS_BY_RESPONSE = "outputs/part4_subjects_by_response.csv"
OUT_SUBJECTS_BY_SEX = "outputs/part4_subjects_by_sex.csv"
OUT_AVG_BCELL = "outputs/part4_avg_b_cell_male_responders_time0.txt"


def run_part4():
    conn = sqlite3.connect(DB_PATH)

    baseline_where = """
        sub.condition = 'melanoma'
        AND s.sample_type = 'PBMC'
        AND s.treatment = 'miraclib'
        AND s.time_from_treatment_start = 0
    """

    baseline_samples = pd.read_sql(
        f"""
        SELECT
            p.project,
            sub.subject,
            s.sample,
            s.response,
            sub.sex,
            s.time_from_treatment_start
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        JOIN projects p ON sub.project_id = p.project_id
        WHERE {baseline_where}
        ORDER BY p.project, sub.subject, s.sample
        """,
        conn,
    )
    baseline_samples.to_csv(OUT_BASELINE_SAMPLES, index=False)

    samples_by_project = pd.read_sql(
        f"""
        SELECT
            p.project,
            COUNT(*) AS n_samples
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        JOIN projects p ON sub.project_id = p.project_id
        WHERE {baseline_where}
        GROUP BY p.project
        ORDER BY n_samples DESC, p.project
        """,
        conn,
    )
    samples_by_project.to_csv(OUT_SAMPLES_BY_PROJECT, index=False)

    subjects_by_response = pd.read_sql(
        f"""
        SELECT
            s.response,
            COUNT(DISTINCT s.subject_id) AS n_subjects
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        WHERE {baseline_where}
        GROUP BY s.response
        ORDER BY s.response
        """,
        conn,
    )
    subjects_by_response.to_csv(OUT_SUBJECTS_BY_RESPONSE, index=False)

    subjects_by_sex = pd.read_sql(
        f"""
        SELECT
            sub.sex,
            COUNT(DISTINCT sub.subject_id) AS n_subjects
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        WHERE {baseline_where}
        GROUP BY sub.sex
        ORDER BY sub.sex
        """,
        conn,
    )
    subjects_by_sex.to_csv(OUT_SUBJECTS_BY_SEX, index=False)

    # Average B cells for melanoma males who are responders at baseline (time=0)
    # Dataset may encode male as 'M' or 'male' (same idea for female).
    avg_b_cell_df = pd.read_sql(
        f"""
        SELECT
            AVG(c.b_cell) AS avg_b_cell
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        JOIN cell_counts c ON s.sample = c.sample
        WHERE {baseline_where}
            AND s.response = 'yes'
            AND LOWER(TRIM(sub.sex)) IN ('m', 'male')
        """,
        conn,
    )

    conn.close()

    avg_val = avg_b_cell_df.loc[0, "avg_b_cell"]
    formatted = "NA" if pd.isna(avg_val) else f"{avg_val:.2f}"
    Path(OUT_AVG_BCELL).write_text(formatted + "\n", encoding="utf-8")

    print(f"Created {OUT_BASELINE_SAMPLES}")
    print(f"Created {OUT_SAMPLES_BY_PROJECT}")
    print(f"Created {OUT_SUBJECTS_BY_RESPONSE}")
    print(f"Created {OUT_SUBJECTS_BY_SEX}")
    print(f"Created {OUT_AVG_BCELL}")
    print("Avg B cells (melanoma males, responders, time=0):", formatted)


if __name__ == "__main__":
    run_part4()