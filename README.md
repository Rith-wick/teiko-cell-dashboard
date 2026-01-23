# Teiko Technical – Immune Cell Population Analysis

This project analyzes immune cell population data from a clinical trial to help understand how a drug candidate (miraclib) affects immune cell distributions and whether these distributions are associated with treatment response.

The solution:
- Loads the provided CSV into a relational SQLite database
- Computes per-sample immune cell relative frequencies
- Performs responder vs non-responder statistical analysis
- Explores a baseline (time = 0) subset
- Presents results in an interactive Streamlit dashboard

The scope is intentionally limited to **melanoma patients, PBMC samples, treated with miraclib**, exactly as specified in the assignment.

---

## Project Structure

```
.
├── app/
│   └── dashboard.py              # Streamlit dashboard (Parts 2–4)
├── src/
│   ├── db.py                     # Part 1: database schema + CSV loader
│   ├── analysis.py               # Part 2 & 3: summary table + statistics
│   └── part4.py                  # Part 4: baseline subset analysis
├── data/
│   └── cell-count.csv            # Input dataset
├── outputs/
│   ├── cell_data.db              # SQLite database (generated)
│   ├── summary_table.csv         # Part 2 output
│   ├── part3_stats.csv           # Part 3 statistical results
│   ├── part3_boxplots.html       # Optional exported visualization
│   ├── part4_baseline_samples.csv
│   ├── part4_samples_by_project.csv
│   ├── part4_subjects_by_response.csv
│   ├── part4_subjects_by_sex.csv
│   └── part4_avg_b_cell_male_responders_time0.txt
├── requirements.txt
└── README.md
```

---

## Setup and Execution (GitHub Codespaces or Local)

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Build database and generate outputs
Run the scripts in this order:

```bash
python src/db.py
python src/analysis.py
python src/part4.py
```

This will:
- Initialize the SQLite database
- Load all rows from `cell-count.csv`
- Generate all CSV and text outputs required by the assignment

### 3. Launch the dashboard
```bash
streamlit run app/dashboard.py
```

---

## Part 1: Data Management (Database Design)

### Schema Overview
The data is modeled using a normalized relational schema:

- **projects**
  - One row per project
- **subjects**
  - One row per subject
  - Linked to a project
  - Stores subject-level attributes (condition/indication, sex)
- **samples**
  - One row per biological sample
  - Linked to a subject
  - Stores sample metadata (treatment, response, sample type, time from treatment start)
- **cell_counts**
  - One row per sample
  - Stores the five immune cell population counts:
    - b_cell
    - cd8_t_cell
    - cd4_t_cell
    - nk_cell
    - monocyte

### Rationale and Scalability
- This design avoids duplication of project and subject metadata across samples.
- It scales naturally to hundreds of projects and thousands of samples.
- Additional analyses can be added by joining from samples to subjects/projects and to cell counts.
- If the immune panel expanded in the future, the schema could be extended or converted to a long-format cell count table without changing the overall design.

---

## Part 2: Initial Analysis – Relative Frequencies

For each sample:
- The total cell count is computed as the sum of the five immune populations.
- Relative frequency (%) is calculated as:
  
  ```
  population_count / total_count * 100
  ```

The resulting summary table contains:
- `sample`
- `total_count`
- `population`
- `count`
- `percentage`

This table is written to:
```
outputs/summary_table.csv
```
and displayed in the dashboard under **Part 2**.

---

## Part 3: Statistical Analysis – Responders vs Non-Responders

### Cohort Used
- Condition: melanoma
- Treatment: miraclib
- Sample type: PBMC
- Responses compared: yes vs no

### Analysis
- Relative frequencies are compared between responders and non-responders for each immune cell population.
- Visualization: boxplots stratified by response.
- Statistical test: Mann–Whitney U test (non-parametric).

Results are written to:
```
outputs/part3_stats.csv
```
and displayed alongside the boxplots in the dashboard under **Part 3**.

---

## Part 4: Baseline Subset Analysis (time = 0)

### Subset Definition
- Condition: melanoma
- Treatment: miraclib
- Sample type: PBMC
- Time from treatment start: 0 (baseline)

### Outputs
- All baseline samples:
  - `outputs/part4_baseline_samples.csv`
- Number of samples per project:
  - `outputs/part4_samples_by_project.csv`
- Number of subjects by response:
  - `outputs/part4_subjects_by_response.csv`
- Number of subjects by sex:
  - `outputs/part4_subjects_by_sex.csv`

### Required Metric
**Considering melanoma males, what is the average number of B cells for responders at time = 0?**

- Computed directly from the baseline subset
- Reported to two decimals
- Written to:
  ```
  outputs/part4_avg_b_cell_male_responders_time0.txt
  ```
- Displayed prominently in the dashboard under **Part 4**

---

## Dashboard

The Streamlit dashboard presents:
- Part 2 summary table
- Part 3 boxplots and statistical results
- Part 4 baseline subset tables and required aggregate

The dashboard is intentionally scoped to the assignment requirements.

### Live Dashboard Link
STREAMLIT CLOUD URL HERE

---

## Repository Link

GITHUB REPOSITORY LINK HERE
