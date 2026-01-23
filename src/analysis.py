import sqlite3
import pandas as pd
from scipy.stats import mannwhitneyu
import plotly.express as px

DB_PATH = "outputs/cell_data.db"
CELL_COLS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

def part2_summary(conn: sqlite3.Connection) -> pd.DataFrame:
    df = pd.read_sql(
        """
        SELECT
            s.sample,
            sub.condition,
            s.treatment,
            s.sample_type,
            s.time_from_treatment_start,
            s.response,
            c.b_cell,
            c.cd8_t_cell,
            c.cd4_t_cell,
            c.nk_cell,
            c.monocyte
        FROM samples s
        JOIN subjects sub ON s.subject_id = sub.subject_id
        JOIN cell_counts c ON s.sample = c.sample
        """,
        conn,
    )

    df["total_count"] = df[CELL_COLS].sum(axis=1)

    long_df = df.melt(
        id_vars=[
            "sample",
            "condition",
            "treatment",
            "sample_type",
            "time_from_treatment_start",
            "response",
            "total_count",
        ],
        value_vars=CELL_COLS,
        var_name="population",
        value_name="count",
    )

    long_df["percentage"] = (long_df["count"] / long_df["total_count"]) * 100
    return long_df

def run_part3():
    conn = sqlite3.connect(DB_PATH)

    long_df = part2_summary(conn)
    conn.close()

    subset = long_df[
        (long_df["condition"] == "melanoma")
        & (long_df["treatment"] == "miraclib")
        & (long_df["sample_type"] == "PBMC")
        & (long_df["response"].isin(["yes", "no"]))
    ].copy()

    subset["percentage"] = subset["percentage"].round(4)

    fig = px.box(
        subset,
        x="population",
        y="percentage",
        color="response",
        title="Melanoma PBMC (miraclib): Relative Frequencies by Response",
    )
    fig.write_html("outputs/part3_boxplots.html")

    results = []
    for pop in CELL_COLS:
        r = subset[(subset["population"] == pop) & (subset["response"] == "yes")]["percentage"]
        nr = subset[(subset["population"] == pop) & (subset["response"] == "no")]["percentage"]

        if len(r) >= 2 and len(nr) >= 2:
            stat, p = mannwhitneyu(r, nr, alternative="two-sided")
            results.append(
                {
                    "population": pop,
                    "n_responders": int(len(r)),
                    "n_nonresponders": int(len(nr)),
                    "p_value": float(p),
                }
            )
        else:
            results.append(
                {
                    "population": pop,
                    "n_responders": int(len(r)),
                    "n_nonresponders": int(len(nr)),
                    "p_value": None,
                }
            )

    stats_df = pd.DataFrame(results).sort_values("p_value", na_position="last")
    stats_df["p_value"] = stats_df["p_value"].round(6)
    stats_df.to_csv("outputs/part3_stats.csv", index=False)

    print("Created outputs/part3_boxplots.html")
    print("Created outputs/part3_stats.csv")

if __name__ == "__main__":
    run_part3()