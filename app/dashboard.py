import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "outputs/cell_data.db"

OUTPUT_FILES = {
    "summary": "outputs/summary_table.csv",
    "p3_stats": "outputs/part3_stats.csv",
    "p4_samples": "outputs/part4_baseline_samples.csv",
    "p4_by_project": "outputs/part4_samples_by_project.csv",
    "p4_by_response": "outputs/part4_subjects_by_response.csv",
    "p4_by_sex": "outputs/part4_subjects_by_sex.csv",
    "p4_avg": "outputs/part4_avg_b_cell_male_responders_time0.txt",
}

CELL_COLS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

st.set_page_config(page_title="Teiko Immune Cell Dashboard", layout="wide")
st.title("Immune Cell Population Dashboard")
st.caption("Scoped to the assignment: melanoma + miraclib + PBMC")


def outputs_missing():
    missing = [p for p in OUTPUT_FILES.values() if not Path(p).exists()]
    return missing


@st.cache_data
def load_long_from_db() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT
            p.project,
            sub.subject,
            sub.condition,
            sub.sex,
            s.sample,
            s.treatment,
            s.response,
            s.sample_type,
            s.time_from_treatment_start,
            c.b_cell,
            c.cd8_t_cell,
            c.cd4_t_cell,
            c.nk_cell,
            c.monocyte
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        JOIN projects p ON sub.project_id = p.project_id
        JOIN cell_counts c ON s.sample = c.sample
        """,
        conn,
    )
    conn.close()

    df["total_count"] = df[CELL_COLS].sum(axis=1)

    long_df = df.melt(
        id_vars=[
            "project",
            "subject",
            "condition",
            "sex",
            "sample",
            "treatment",
            "response",
            "sample_type",
            "time_from_treatment_start",
            "total_count",
        ],
        value_vars=CELL_COLS,
        var_name="population",
        value_name="count",
    )
    long_df["percentage"] = (long_df["count"] / long_df["total_count"]) * 100
    return long_df


missing = outputs_missing()
if missing:
    st.warning(
        "Some required output files are missing. Run these commands first:\n\n"
        "1) python src/db.py\n"
        "2) python src/analysis.py\n"
        "3) python src/part4.py\n"
    )
    st.write("Missing files:")
    for p in missing:
        st.write("-", p)
    st.stop()

long_df = load_long_from_db()

# Hard scope exactly to the assignment
SCOPED = long_df[
    (long_df["condition"] == "melanoma")
    & (long_df["treatment"] == "miraclib")
    & (long_df["sample_type"] == "PBMC")
].copy()

k1, k2, k3 = st.columns(3)
k1.metric("Condition", "melanoma")
k2.metric("Treatment", "miraclib")
k3.metric("Sample type", "PBMC")

tabs = st.tabs(["Part 2: Summary Table", "Part 3: Response Analysis", "Part 4: Baseline Subset"])

# -------------------------
# Part 2
# -------------------------
with tabs[0]:
    st.subheader("Part 2: Relative frequency of each cell type in each sample")

    summary = pd.read_csv(OUTPUT_FILES["summary"])
    st.dataframe(summary, use_container_width=True)

    st.download_button(
        "Download summary_table.csv",
        data=summary.to_csv(index=False).encode("utf-8"),
        file_name="summary_table.csv",
        mime="text/csv",
    )

# -------------------------
# Part 3
# -------------------------
with tabs[1]:
    st.subheader("Part 3: Responders vs Non-Responders (melanoma PBMC on miraclib)")

    resp_filter = st.multiselect("Include responses", ["yes", "no"], default=["yes", "no"])
    p3 = SCOPED[SCOPED["response"].isin(resp_filter)].copy()

    left, right = st.columns([2, 1])

    with left:
        fig = px.box(
            p3,
            x="population",
            y="percentage",
            color="response",
            title="Relative Frequencies by Response (boxplots)",
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        stats = pd.read_csv(OUTPUT_FILES["p3_stats"])
        st.markdown("**Statistical results (Mann–Whitney U):**")
        st.dataframe(stats, use_container_width=True)

        sig = stats.dropna(subset=["p_value"]).query("p_value < 0.05")
        st.markdown("**Significant (p < 0.05):**")
        st.dataframe(sig if len(sig) else pd.DataFrame({"message": ["None at p < 0.05"]}), use_container_width=True)

# -------------------------
# Part 4
# -------------------------
with tabs[2]:
    st.subheader("Part 4: Baseline subset (time_from_treatment_start = 0)")

    st.caption("Fixed at baseline (time = 0) per the assignment.")
    avg_val = Path(OUTPUT_FILES["p4_avg"]).read_text(encoding="utf-8").strip()
    st.metric("Avg B cells (melanoma males, responders, time=0)", avg_val)

    colA, colB = st.columns(2)

    with colA:
        by_project = pd.read_csv(OUTPUT_FILES["p4_by_project"])
        st.markdown("**How many samples from each project**")
        st.dataframe(by_project, use_container_width=True)

        by_resp = pd.read_csv(OUTPUT_FILES["p4_by_response"])
        st.markdown("**How many subjects were responders/non-responders**")
        st.dataframe(by_resp, use_container_width=True)

    with colB:
        by_sex = pd.read_csv(OUTPUT_FILES["p4_by_sex"])
        st.markdown("**How many subjects were males/females**")
        st.dataframe(by_sex, use_container_width=True)

        baseline_samples = pd.read_csv(OUTPUT_FILES["p4_samples"])
        st.markdown("**Baseline sample list (melanoma PBMC on miraclib at time=0)**")
        st.dataframe(baseline_samples, use_container_width=True)