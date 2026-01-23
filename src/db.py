import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = "outputs/cell_data.db"
CSV_PATH = "data/cell-count.csv"

CELL_COLS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA foreign_keys = ON;")

    conn.executescript(
        """
        DROP TABLE IF EXISTS cell_counts;
        DROP TABLE IF EXISTS samples;
        DROP TABLE IF EXISTS subjects;
        DROP TABLE IF EXISTS projects;

        CREATE TABLE projects (
            project_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project TEXT NOT NULL UNIQUE
        );

        CREATE TABLE subjects (
            subject_id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            condition TEXT,
            age INTEGER,
            sex TEXT,
            UNIQUE(project_id, subject),
            FOREIGN KEY(project_id) REFERENCES projects(project_id)
        );

        CREATE TABLE samples (
            sample TEXT PRIMARY KEY,
            subject_id INTEGER NOT NULL,
            treatment TEXT,
            response TEXT,
            sample_type TEXT,
            time_from_treatment_start REAL,
            FOREIGN KEY(subject_id) REFERENCES subjects(subject_id)
        );

        CREATE TABLE cell_counts (
            sample TEXT PRIMARY KEY,
            b_cell INTEGER NOT NULL,
            cd8_t_cell INTEGER NOT NULL,
            cd4_t_cell INTEGER NOT NULL,
            nk_cell INTEGER NOT NULL,
            monocyte INTEGER NOT NULL,
            FOREIGN KEY(sample) REFERENCES samples(sample)
        );

        CREATE INDEX idx_samples_treatment ON samples(treatment);
        CREATE INDEX idx_samples_sample_type ON samples(sample_type);
        CREATE INDEX idx_samples_time ON samples(time_from_treatment_start);
        CREATE INDEX idx_subjects_condition ON subjects(condition);
        CREATE INDEX idx_subjects_sex ON subjects(sex);
        """
    )


def load_csv_to_db(csv_path: str = CSV_PATH, db_path: str = DB_PATH) -> None:
    Path("outputs").mkdir(exist_ok=True)

    df = pd.read_csv(csv_path)

    required_cols = {
        "project",
        "subject",
        "condition",
        "age",
        "sex",
        "treatment",
        "response",
        "sample",
        "sample_type",
        "time_from_treatment_start",
        *CELL_COLS,
    }
    missing = sorted(required_cols - set(df.columns))
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df["age"] = pd.to_numeric(df["age"], errors="coerce")
    df["time_from_treatment_start"] = pd.to_numeric(df["time_from_treatment_start"], errors="coerce")

    conn = sqlite3.connect(db_path)
    try:
        init_db(conn)
        cur = conn.cursor()

        project_id_by_name: dict[str, int] = {}

        def get_project_id(project_name: str) -> int:
            if project_name in project_id_by_name:
                return project_id_by_name[project_name]
            cur.execute("INSERT OR IGNORE INTO projects(project) VALUES (?)", (project_name,))
            cur.execute("SELECT project_id FROM projects WHERE project = ?", (project_name,))
            pid = int(cur.fetchone()[0])
            project_id_by_name[project_name] = pid
            return pid

        subject_id_by_key: dict[tuple[int, str], int] = {}

        def get_subject_id(project_id: int, subject: str, condition, age, sex) -> int:
            key = (project_id, subject)
            if key in subject_id_by_key:
                return subject_id_by_key[key]

            cur.execute(
                """
                INSERT OR IGNORE INTO subjects(project_id, subject, condition, age, sex)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, subject, condition, age, sex),
            )
            cur.execute(
                "SELECT subject_id FROM subjects WHERE project_id = ? AND subject = ?",
                (project_id, subject),
            )
            sid = int(cur.fetchone()[0])
            subject_id_by_key[key] = sid
            return sid

        samples_rows = []
        counts_rows = []

        for _, r in df.iterrows():
            project = str(r["project"])
            subject = str(r["subject"])
            sample = str(r["sample"])

            pid = get_project_id(project)
            sid = get_subject_id(pid, subject, r.get("condition"), r.get("age"), r.get("sex"))

            samples_rows.append(
                (
                    sample,
                    sid,
                    r.get("treatment"),
                    r.get("response"),
                    r.get("sample_type"),
                    r.get("time_from_treatment_start"),
                )
            )

            counts_rows.append(
                (
                    sample,
                    int(r["b_cell"]),
                    int(r["cd8_t_cell"]),
                    int(r["cd4_t_cell"]),
                    int(r["nk_cell"]),
                    int(r["monocyte"]),
                )
            )

        cur.executemany(
            """
            INSERT OR REPLACE INTO samples(
                sample, subject_id, treatment, response, sample_type, time_from_treatment_start
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            samples_rows,
        )

        cur.executemany(
            """
            INSERT OR REPLACE INTO cell_counts(
                sample, b_cell, cd8_t_cell, cd4_t_cell, nk_cell, monocyte
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            counts_rows,
        )

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    load_csv_to_db()
    print(f"Loaded database at: {DB_PATH}")