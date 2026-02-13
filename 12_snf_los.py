import pandas as pd

# =======================
# CONFIG (edit if needed)
# =======================
ID = 'individual_id'          # or 'member_id'
COHORT = 'cohort_type'
TARG_DT = 'targeted_date'
INDEX_DT = 'index_date'

ENG_CTRL = 'ENGAGED_CONTROL'
ENG_TRT  = 'engaged_treatment'
TARG_TRT = 'targeted_treatment'

# =======================
# 0) (Recommended) ensure date types match
# =======================
for c in [TARG_DT, INDEX_DT]:
    df[c] = pd.to_datetime(df[c]).dt.date

# =======================
# 1) Keep only engaged_control + engaged_treatment
# =======================
eng_eval = df[df[COHORT].isin([ENG_CTRL, ENG_TRT])].copy()

# =======================
# 2) Targeted snapshot rows (index_date == targeted_date) for targeted_treatment
#    If you can have multiple rows per (ID, targeted_date), keep the first/last deterministically
# =======================
targ = df[
    (df[COHORT].eq(TARG_TRT)) &
    (pd.to_datetime(df[INDEX_DT]).dt.date == pd.to_datetime(df[TARG_DT]).dt.date)
].copy()

# Deduplicate targeted snapshots per (ID, targeted_date) to avoid ambiguous overwrites
# Prefer the last row as it appears in df; if you have another tie-breaker, swap it in here.
targ = targ.drop_duplicates([ID, TARG_DT], keep='last')

# =======================
# 3) Decide which columns are "features" to overwrite
# =======================
exclude = {
    ID, 'member_id',
    COHORT, 'treatment_grp',
    INDEX_DT, 'index_month',
    TARG_DT, 'engaged_date',
    'prev_6m', 'post_6m'
}
feature_cols = [c for c in df.columns if c not in exclude]

# =======================
# 4) Index both frames and overwrite engaged_treatment rows IN-PLACE (no extra columns)
# =======================
eng_idx  = eng_eval.set_index([ID, TARG_DT])
targ_idx = targ.set_index([ID, TARG_DT])

mask = eng_idx[COHORT].eq(ENG_TRT)

# only overwrite where a targeted snapshot exists
valid_idx = eng_idx[mask].index.intersection(targ_idx.index)

print("Engaged treatment rows:", int(mask.sum()))
print("Matched targeted snapshot rows:", int(len(valid_idx)))
print("Unmatched engaged_treatment rows (no targeted snapshot):", int(mask.sum() - len(valid_idx)))

# IMPORTANT: assign without .values (keeps index alignment; avoids broadcasting error)
eng_idx.loc[valid_idx, feature_cols] = targ_idx.loc[valid_idx, feature_cols]

# =======================
# 5) Anchor index_date to targeted_date (ITT-style anchor for windows/outcomes)
# =======================
eng_idx[INDEX_DT] = eng_idx.index.get_level_values(TARG_DT)

# back to a normal dataframe
eng_eval_swapped = eng_idx.reset_index()

# =======================
# 6) (Optional) quickly list unmatched members for debugging
# =======================
unmatched_idx = eng_idx[mask].index.difference(targ_idx.index)
if len(unmatched_idx) > 0:
    unmatched = pd.DataFrame(unmatched_idx.tolist(), columns=[ID, TARG_DT])
    print("\nSample unmatched (showing up to 20):")
    print(unmatched.head(20))

# RESULT:
# eng_eval_swapped has ENGAGED_CONTROL + engaged_treatment rows,
# and engaged_treatment rows now carry targeted-date features + index_date=targeted_date





import pandas as pd

# ---- CONFIG ----
ID = 'individual_id'      # or 'member_id'
COHORT = 'cohort_type'
TARG_DT = 'targeted_date'
INDEX_DT = 'index_date'

ENG_CTRL = 'ENGAGED_CONTROL'
ENG_TRT  = 'engaged_treatment'
TARG_TRT = 'targeted_treatment'
# ----------------

# 1) Keep only engaged_control + engaged_treatment
eng_eval = df[df[COHORT].isin([ENG_CTRL, ENG_TRT])].copy()

# 2) Get targeted snapshot rows (where index_date == targeted_date)
targ = df[
    (df[COHORT] == TARG_TRT) &
    (df[INDEX_DT] == df[TARG_DT])
].copy()

# 3) Define feature columns to overwrite (exclude IDs/dates/meta)
exclude = {
    ID, 'member_id',
    COHORT, 'treatment_grp',
    INDEX_DT, 'index_month',
    TARG_DT, 'engaged_date',
    'prev_6m', 'post_6m'
}
feature_cols = [c for c in df.columns if c not in exclude]

# 4) Set multi-index for clean substitution
eng_idx = eng_eval.set_index([ID, TARG_DT])
targ_idx = targ.set_index([ID, TARG_DT])

# 5) Identify engaged_treatment rows
mask = eng_idx[COHORT] == ENG_TRT

# Only overwrite where targeted snapshot exists
keys = eng_idx.index[mask].intersection(targ_idx.index)

eng_idx.loc[keys, feature_cols] = targ_idx.loc[keys, feature_cols].values

# 6) Anchor index_date to targeted_date (ITT style)
eng_idx[INDEX_DT] = eng_idx.index.get_level_values(TARG_DT)

eng_eval = eng_idx.reset_index()

print(f"Substituted targeted features for {len(keys):,} engaged_treatment rows.")








Subject: PCR Follow-up: Vendor–Internal CM Overlap and PCR Denominator View

Hi all,

Per Yiwei’s feedback, I reviewed the PCR population focusing on (1) vendor engagement overlap with internal CM (RAP and non-RAP) and (2) targeted and engaged rates as a share of the total PCR denominator. I’ve attached slides with the summary results.

Across vendors, overlap patterns with internal CM are consistent, with RAP/PCR CM accounting for most of the overlap and non-RAP CM contributing a smaller but steady share. Viewing metrics at the full PCR denominator level provides a clearer picture of overall reach and engagement.

Importantly, outcomes show greater readmission reduction when Galileo engagement overlaps with internal CM compared to Galileo-only engagement. This suggests that allowing overlap may drive higher overall impact, and it may be worth revisiting the current RAP suppression approach for Galileo.

Happy to discuss further.

Thanks,  
Chakradhar

---

If you want, I can make an even tighter 4–5 sentence version or tune it for a readout deck cover email.









-- Replace project.dataset.table and your key columns as needed
WITH base AS (
  SELECT
    individual_id,
    pme_reference_no,

    -- normalize (case/extra spaces)
    LOWER(TRIM(REGEXP_REPLACE(first_program_track, r'\s+', ' '))) AS fpt_norm,
    LOWER(TRIM(REGEXP_REPLACE(program_referral,   r'\s+', ' '))) AS pr_norm
  FROM `project.dataset.table`
),

long AS (
  -- stack both cols into one "feature" column
  SELECT
    individual_id,
    pme_reference_no,
    CONCAT('fpt__', REPLACE(fpt_norm, ' ', '_')) AS feature,
    1 AS val
  FROM base
  WHERE fpt_norm IS NOT NULL AND fpt_norm != ''

  UNION ALL

  SELECT
    individual_id,
    pme_reference_no,
    CONCAT('pr__', REPLACE(pr_norm, ' ', '_')) AS feature,
    1 AS val
  FROM base
  WHERE pr_norm IS NOT NULL AND pr_norm != ''
)

SELECT *
FROM long
PIVOT (
  MAX(val) FOR feature IN (
    -- first_program_track (prefix fpt__)
    'fpt__social_services',
    'fpt__rap',
    'fpt__behavioral_health',
    'fpt__short_term_referral',
    'fpt__dedicated_group_triggers',
    'fpt__accp',
    'fpt__medium',
    'fpt__high',
    'fpt__healthy_heart',
    'fpt__low',

    -- program_referral (prefix pr__)
    'pr__admission_avoidance',
    'pr__care_needs',
    'pr__complex_care_needs',
    'pr__er_predictive',
    'pr__healthy_heart_program',
    'pr__manual',
    'pr__post_discharge',
    'pr__pre_admission',
    'pr__provider_collaboration',
    'pr__provider_outreach',
    'pr__risk_stratification'
  )
);





Hi Amanda,

Thank you for the update.

I have completed the electronic questionnaire and uploaded all the requested documents to my VisaTrax profile. Please let me know if anything additional is required from my end to proceed.

I look forward to moving ahead with the filing of the I-140 petition at your earliest convenience.

Thank you for your support.

Best regards,  
Chakradhar Reddy





import numpy as np

pmpm_cols = [
    "er_pmpm_pre", "ip_pmpm_pre", "allowed_pmpm_pre", "paid_pmpm_pre",
    "er_pmpm_post", "ip_pmpm_post", "allowed_pmpm_post", "paid_pmpm_post"
]

df[pmpm_cols] = df[pmpm_cols].replace([np.inf, -np.inf], 0).fillna(0)





# BEFORE PMPM (pre-period)
df["er_pmpm_pre"]      = df["bfr_ut_er_visits_6_mth"] / df["med_mths_pre"]
df["ip_pmpm_pre"]      = df["bfr_ut_ip_visits_6_mth"] / df["med_mths_pre"]
df["allowed_pmpm_pre"] = df["bfr_allowed_amt_6_mth"] / df["med_mths_pre"]
df["paid_pmpm_pre"]    = df["bfr_paid_amt_6_mth"] / df["med_mths_pre"]

# AFTER PMPM (post-period)
df["er_pmpm_post"]      = df["aft_ut_er_visits_6_mth"] / df["med_mths_post"]
df["ip_pmpm_post"]      = df["aft_ut_ip_visits_6_mth"] / df["med_mths_post"]
df["allowed_pmpm_post"] = df["aft_allowed_amt_6_mth"] / df["med_mths_post"]
df["paid_pmpm_post"]    = df["aft_paid_amt_6_mth"] / df["med_mths_post"]








m# ---- FIX cobra import to use cobra-flow-gcp repo ----
import sys

# Path that contains src/cobra/...
COBRA_SRC = "/home/jupyter/zip_files/cobra-flow-gcp-master/src"

if COBRA_SRC not in sys.path:
    sys.path.insert(0, COBRA_SRC)

# Verify correct cobra is loaded
import cobra
print("cobra loaded from:", cobra.__file__)

# Now these WILL work
from cobra.data.check import CobraDataCheck
from cobra.data.prep import CobraDataPrep
from cobra.flow.subgroup import AutoEval
# ----------------------------------------------------









import sys, os, cobra
print("cobra imported from:", cobra.__file__)
print("cwd:", os.getcwd())

# show if local cobra exists relative to cwd
print("local cobra folder exists:", os.path.isdir("cobra"))
print("local cobra/data/check.py exists:", os.path.exists("cobra/data/check.py"))

print("top sys.path entries:")
print("\n".join(sys.path[:5]))






# Step 1: High utilizers
tdf_hi = tdf[tdf['bfr_ut_er_visits_6_mth'] > 4]

# Step 2: Remove extreme outliers (global rule)
upper = tdf_hi['bfr_ut_er_visits_6_mth'].quantile(0.99)
lower = tdf_hi['bfr_ut_er_visits_6_mth'].quantile(0.01)

tdf_final = tdf_hi[
    (tdf_hi['bfr_ut_er_visits_6_mth'] >= lower) &
    (tdf_hi['bfr_ut_er_visits_6_mth'] <= upper)
]





Hi [Team / Name],

We wanted to give you a heads-up on an upcoming enhancement to the RAP identification logic and confirm alignment before moving forward—especially given the timing at the end of the year.

What’s changing
	•	Going forward, RAP cases will be identified based on the predicted discharge date (using historical LOS patterns), rather than identifying all cases as soon as an authorization is received.
	•	Identification will focus on cases on or after the predicted discharge date, within the existing post-discharge window.

What this means operationally
	•	You may see a slightly lower volume of newly identified cases compared to the current process.
	•	This is expected because:
	•	Some cases were previously identified too early (well before discharge).
	•	Some cases were already sent earlier in the stay and will no longer be re-surfaced.
	•	A small subset of cases will be intentionally suppressed until they are closer to (or past) the predicted discharge date, improving timing relevance.

Why we’re making this change
	•	Improves alignment with true post-discharge RAP opportunity.
	•	Reduces early or premature identification during inpatient stays.
	•	Keeps missed opportunity rates unchanged while improving timing precision.

Given that this is the last two weeks of December, we wanted to check:
	•	Are you comfortable with the expected short-term volume reduction?
	•	Do you anticipate any concerns related to year-end volume goals or reporting?

Happy to walk through the details or share recent analysis if helpful. We want to make sure this change supports both clinical effectiveness and operational needs.

Thanks,
Chakradhar










-- full combo: diagnosis group + service type + admission status
`anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_FULL_COMBO`
  (icd9_dx_group_nbr, tum_stay_srv_type_cd, SAAdmissionStatusType, median_los_all)

-- diagnosis-group only
`anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GRP`
  (icd9_dx_group_nbr, median_los_grp)

-- diagnosis-category only
`anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_CTG`
  (icd9_dx_ctg_cd, median_los_ctg)

-- global median (single row)
`anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GLOBAL`
  (global_median_los)


CREATE OR REPLACE TABLE
  `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_03_apply_los_prediction`
AS
WITH global_los AS (
  SELECT global_median_los
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GLOBAL`
),

auth_base AS (
  SELECT
    pme_reference_no,
    SAAdmissionStatusType,
    aServiceLineServiceTypeCd,
    DiagnosisCode,
    admit_dt,
    discharge_dt,
    icd9_dx_group_nbr,
    icd9_dx_ctg_cd
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_02_get_diagnosis_category_and_group`
)

SELECT
  ab.pme_reference_no,
  ab.SAAdmissionStatusType,
  ab.aServiceLineServiceTypeCd AS tum_stay_srv_type_cd,
  ab.DiagnosisCode,
  ab.icd9_dx_group_nbr,
  ab.icd9_dx_ctg_cd,
  ab.admit_dt,
  ab.discharge_dt,

  -- raw medians from each level
  f.median_los_all,
  g.median_los_grp,
  c.median_los_ctg,
  gl.global_median_los,

  -- final predicted LOS (days) using fallback chain:
  -- full combo -> group -> category -> global
  COALESCE(
    f.median_los_all,
    g.median_los_grp,
    c.median_los_ctg,
    gl.global_median_los
  ) AS predicted_los_days,

  -- predicted discharge date from admit date
  DATE_ADD(
    ab.admit_dt,
    INTERVAL COALESCE(
      f.median_los_all,
      g.median_los_grp,
      c.median_los_ctg,
      gl.global_median_los
    ) DAY
  ) AS predicted_discharge_dt,

  -- **effective discharge date for scoring**:
  -- use actual discharge if populated, otherwise predicted
  COALESCE(
    ab.discharge_dt,
    DATE_ADD(
      ab.admit_dt,
      INTERVAL COALESCE(
        f.median_los_all,
        g.median_los_grp,
        c.median_los_ctg,
        gl.global_median_los
      ) DAY
    )
  ) AS effective_discharge_dt

FROM auth_base ab
LEFT JOIN `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_FULL_COMBO` f
  ON  ab.icd9_dx_group_nbr     = f.icd9_dx_group_nbr
  AND ab.aServiceLineServiceTypeCd = f.tum_stay_srv_type_cd
  AND ab.SAAdmissionStatusType = f.SAAdmissionStatusType
LEFT JOIN `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GRP` g
  ON  ab.icd9_dx_group_nbr     = g.icd9_dx_group_nbr
LEFT JOIN `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_CTG` c
  ON  ab.icd9_dx_ctg_cd        = c.icd9_dx_ctg_cd
CROSS JOIN global_los gl;


-- Median LOS by diagnosis group + admission status (no service type)
CREATE OR REPLACE TABLE
  `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GRP_ADMSTATUS` AS
WITH los_train_base AS (
  SELECT
    icd9_dx_group_nbr,
    icd9_dx_ctg_cd,
    SAAdmissionStatusType,
    tum_act_los_day_cnt
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_IP_LOS_HIST`   -- your curated hist table
  WHERE include_in_los_training = TRUE
    AND lob = 'Medicare'
    AND train_year = 2024
    AND tum_act_los_day_cnt IS NOT NULL
)
SELECT
  icd9_dx_group_nbr,
  SAAdmissionStatusType,
  CAST(APPROX_QUANTILES(tum_act_los_day_cnt, 100)[OFFSET(50)] AS INT64) AS median_los_grp_adm
FROM los_train_base
GROUP BY 1, 2;

-- Median LOS by diagnosis group
CREATE OR REPLACE TABLE
  `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GRP` AS
WITH los_train_base AS (
  SELECT
    icd9_dx_group_nbr,
    tum_act_los_day_cnt
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_IP_LOS_HIST`
  WHERE include_in_los_training = TRUE
    AND lob = 'Medicare'
    AND train_year = 2024
    AND tum_act_los_day_cnt IS NOT NULL
)
SELECT
  icd9_dx_group_nbr,
  CAST(APPROX_QUANTILES(tum_act_los_day_cnt, 100)[OFFSET(50)] AS INT64) AS median_los_grp
FROM los_train_base
GROUP BY 1;


-- Median LOS by diagnosis category
CREATE OR REPLACE TABLE
  `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_CTG` AS
WITH los_train_base AS (
  SELECT
    icd9_dx_ctg_cd,
    tum_act_los_day_cnt
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_IP_LOS_HIST`
  WHERE include_in_los_training = TRUE
    AND lob = 'Medicare'
    AND train_year = 2024
    AND tum_act_los_day_cnt IS NOT NULL
)
SELECT
  icd9_dx_ctg_cd,
  CAST(APPROX_QUANTILES(tum_act_los_day_cnt, 100)[OFFSET(50)] AS INT64) AS median_los_ctg
FROM los_train_base
GROUP BY 1;


-- Global median LOS
CREATE OR REPLACE TABLE
  `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GLOBAL` AS
WITH los_train_base AS (
  SELECT
    tum_act_los_day_cnt
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_IP_LOS_HIST`
  WHERE include_in_los_training = TRUE
    AND lob = 'Medicare'
    AND train_year = 2024
    AND tum_act_los_day_cnt IS NOT NULL
)
SELECT
  CAST(APPROX_QUANTILES(tum_act_los_day_cnt, 100)[OFFSET(50)] AS INT64) AS global_median_los;



CREATE OR REPLACE TABLE
  `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_03_apply_los_prediction` AS
WITH global_los AS (
  SELECT global_median_los
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GLOBAL`
),

auth_base AS (
  SELECT
    pme_reference_no,
    SAAdmissionStatusType,
    aServiceLineServiceTypeCd,     -- kept for reference, not used in LOS join
    DiagnosisCode,
    admit_dt,
    discharge_dt,
    icd9_dx_group_nbr,
    icd9_dx_ctg_cd
  FROM `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_02_get_diagnosis_category_and_group`
)

SELECT
  ab.pme_reference_no,
  ab.SAAdmissionStatusType,
  ab.aServiceLineServiceTypeCd,
  ab.DiagnosisCode,
  ab.icd9_dx_group_nbr,
  ab.icd9_dx_ctg_cd,
  ab.admit_dt,
  ab.discharge_dt,

  -- medians from each level
  f.median_los_grp_adm,
  g.median_los_grp,
  c.median_los_ctg,
  gl.global_median_los,

  -- final predicted LOS (days) with fallback:
  -- group+admission_status → group → category → global
  COALESCE(
    f.median_los_grp_adm,
    g.median_los_grp,
    c.median_los_ctg,
    gl.global_median_los
  ) AS predicted_los_days,

  -- predicted discharge date from admit date
  DATE_ADD(
    ab.admit_dt,
    INTERVAL COALESCE(
      f.median_los_grp_adm,
      g.median_los_grp,
      c.median_los_ctg,
      gl.global_median_los
    ) DAY
  ) AS predicted_discharge_dt,

  -- EFFECTIVE discharge date for scoring:
  --   actual if available, else predicted
  COALESCE(
    ab.discharge_dt,
    DATE_ADD(
      ab.admit_dt,
      INTERVAL COALESCE(
        f.median_los_grp_adm,
        g.median_los_grp,
        c.median_los_ctg,
        gl.global_median_los
      ) DAY
    )
  ) AS effective_discharge_dt

FROM auth_base ab
LEFT JOIN `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GRP_ADMSTATUS` f
  ON  ab.icd9_dx_group_nbr     = f.icd9_dx_group_nbr
  AND ab.SAAdmissionStatusType = f.SAAdmissionStatusType
LEFT JOIN `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_GRP` g
  ON  ab.icd9_dx_group_nbr     = g.icd9_dx_group_nbr
LEFT JOIN `anbc-hcb-dev.clin_analytics_hcb_dev.DE_RAP_DSCHG_LOS_CTG` c
  ON  ab.icd9_dx_ctg_cd        = c.icd9_dx_ctg_cd
CROSS JOIN global_los gl;



The LOS rule is now:

median LOS by (diagnosis group + admission status) →
then by diagnosis group →
then by diagnosis category →
then global median.


























import pandas as pd
import numpy as np

# ============================================================
# 0. EXPECTED INPUTS
# ============================================================
# hist_df: historical inpatient stays used to learn LOS patterns
# auth_df: current authorizations where we want to predict LOS / discharge
#
# Required columns in hist_df:
#   'icd9_dx_group_nbr'
#   'icd9_dx_ctg_cd'
#   'tum_stay_srv_type_cd'
#   'SAAdmissionStatusType'
#   'tum_act_los_day_cnt'        # actual LOS in days (numeric)
#
# Required columns in auth_df:
#   'authorization_id'
#   'tum_actual_admit_dt'        # admit date (datetime or string)
#   'tum_actual_dischg_dt'       # actual discharge date, may be NULL (datetime or string)
#   'icd9_dx_group_nbr'
#   'icd9_dx_ctg_cd'
#   'tum_stay_srv_type_cd'
#   'SAAdmissionStatusType'
#
# NOTE: you can subset hist_df to only 2024 Medicare, etc., BEFORE calling the functions below.


# ============================================================
# 1. UTILITIES – BUILD LOS REFERENCE TABLES FROM HISTORICAL DATA
# ============================================================

def build_los_reference_tables(hist_df: pd.DataFrame):
    """
    Build LOS reference tables (median LOS) from historical IP stays.
    Returns:
      los_by_full_combo, los_by_diag_group, los_by_diag_ctg, global_median_los
    """
    # Ensure LOS is numeric
    df = hist_df.copy()
    df['tum_act_los_day_cnt'] = pd.to_numeric(df['tum_act_los_day_cnt'], errors='coerce')

    # Drop rows with missing LOS
    df = df[df['tum_act_los_day_cnt'].notna()]

    # A) Full combo: (diagnosis group, stay service type, admission status)
    los_by_full_combo = (
        df
        .groupby(['icd9_dx_group_nbr', 'tum_stay_srv_type_cd', 'SAAdmissionStatusType'])['tum_act_los_day_cnt']
        .median()
        .reset_index()
        .rename(columns={'tum_act_los_day_cnt': 'median_los_all'})
    )

    # B) Diagnosis group level
    los_by_diag_group = (
        df
        .groupby('icd9_dx_group_nbr')['tum_act_los_day_cnt']
        .median()
        .reset_index()
        .rename(columns={'tum_act_los_day_cnt': 'median_los_grp'})
    )

    # C) Diagnosis category level
    los_by_diag_ctg = (
        df
        .groupby('icd9_dx_ctg_cd')['tum_act_los_day_cnt']
        .median()
        .reset_index()
        .rename(columns={'tum_act_los_day_cnt': 'median_los_ctg'})
    )

    # D) Global median LOS (final fallback)
    global_median_los = df['tum_act_los_day_cnt'].median()

    print(f"[INFO] Global median LOS (for final fallback): {global_median_los:.2f} days")

    return los_by_full_combo, los_by_diag_group, los_by_diag_ctg, global_median_los


# ============================================================
# 2. APPLY LOS TABLES TO AUTHORIZATIONS (PREDICTED LOS & DISCHARGE)
# ============================================================

def apply_los_prediction_to_auth(
    auth_df: pd.DataFrame,
    los_by_full_combo: pd.DataFrame,
    los_by_diag_group: pd.DataFrame,
    los_by_diag_ctg: pd.DataFrame,
    global_median_los: float
) -> pd.DataFrame:
    """
    Merge LOS reference tables into auth_df and compute:
      - predicted_los_days (with fallback)
      - predicted_discharge_dt
      - effective_discharge_dt (actual if available, else predicted)

    Returns a new DataFrame with these additional columns.
    """
    df = auth_df.copy()

    # Ensure dates are datetime
    df['tum_actual_admit_dt'] = pd.to_datetime(df['tum_actual_admit_dt'], errors='coerce')
    if 'tum_actual_dischg_dt' in df.columns:
        df['tum_actual_dischg_dt'] = pd.to_datetime(df['tum_actual_dischg_dt'], errors='coerce')
    else:
        df['tum_actual_dischg_dt'] = pd.NaT

    # Merge full combo medians
    df = df.merge(
        los_by_full_combo,
        on=['icd9_dx_group_nbr', 'tum_stay_srv_type_cd', 'SAAdmissionStatusType'],
        how='left'
    )

    # Merge diagnosis group medians
    df = df.merge(
        los_by_diag_group,
        on='icd9_dx_group_nbr',
        how='left'
    )

    # Merge diagnosis category medians
    df = df.merge(
        los_by_diag_ctg,
        on='icd9_dx_ctg_cd',
        how='left'
    )

    # ------------------------------
    # Fallback chain for LOS:
    # median_los_all -> median_los_grp -> median_los_ctg -> global_median_los
    # ------------------------------
    pred_los = df['median_los_all'].copy()

    missing_all = pred_los.isna()
    pred_los[missing_all] = df.loc[missing_all, 'median_los_grp']

    missing_grp = pred_los.isna()
    pred_los[missing_grp] = df.loc[missing_grp, 'median_los_ctg']

    missing_ctg = pred_los.isna()
    pred_los[missing_ctg] = global_median_los

    df['predicted_los_days'] = pred_los

    # Diagnostics on fallback usage (optional)
    n_total = len(df)
    print("=== Fallback usage on auth_df ===")
    print(f"Rows without full combo (used grp/ctg/global): {missing_all.sum()} "
          f"({missing_all.sum() / n_total:.2%})")
    print(f"Rows still missing after grp (used ctg/global): {missing_grp.sum()} "
          f"({missing_grp.sum() / n_total:.2%})")
    print(f"Rows still missing after ctg (used global): {missing_ctg.sum()} "
          f"({missing_ctg.sum() / n_total:.2%})")

    # ------------------------------
    # Predicted discharge date
    # ------------------------------
    df['predicted_discharge_dt'] = df['tum_actual_admit_dt'] + pd.to_timedelta(
        df['predicted_los_days'].astype(float),
        unit='D'
    )

    # ------------------------------
    # Effective discharge date for scoring:
    #   If actual discharge exists -> use actual
    #   Else -> use predicted
    # ------------------------------
    df['effective_discharge_dt'] = df['tum_actual_dischg_dt'].where(
        df['tum_actual_dischg_dt'].notna(),
        df['predicted_discharge_dt']
    )

    return df


# ============================================================
# 3. END-TO-END EXAMPLE USAGE
# ============================================================

# Example:
# hist_df = ...  # load your historical IP data (e.g., 2024 Medicare)
# auth_df = ...  # load your current auth data to be scored

# 1) Build LOS reference tables from historical data
# los_full, los_grp, los_ctg, global_med = build_los_reference_tables(hist_df)

# 2) Apply LOS prediction & effective discharge date to authorizations
# auth_with_pred = apply_los_prediction_to_auth(auth_df, los_full, los_grp, los_ctg, global_med)

# 3) auth_with_pred now contains:
#    - 'predicted_los_days'
#    - 'predicted_discharge_dt'
#    - 'effective_discharge_dt' (actual if available, else predicted)
#
# You can then plug 'effective_discharge_dt' into your RAP pipeline logic
# to decide when to release cases for scoring.






















Demonstrated Put People First by designing RAP timing and monitoring changes around care manager workflow and member reachability, so referrals arrive when outreach is more meaningful. Rose to the Challenge by taking ownership of RAP identification and SHJ issues, investigating root causes and proposing practical, data-driven fixes. Joined Forces with Clinical DS, Product, SHJ, and DE partners on RAP monitoring, SNF LOS, and ER Diversion work, sharing interim results and incorporating feedback so solutions worked across teams. Created Simplicity by standardizing key metrics and using transparent, rule-based logic so reports and dashboards are easier for stakeholders to understand and trust.





Great Lakes ER Diversion Evaluation – Helped design the study/control cohorts and led analytic methods (overlap weighting, matching) to balance groups and get cleaner impact estimates. Added key context flags (SDOH, VBC/non-VBC, PCP attribution, rural/urban) and translated results and feedback into clear recommendations for refining the ER Diversion strategy.





Over the course of 2025, I continued to strengthen the Readmission Avoidance Program analytics foundation while improving how RAP models are monitored and operationalized. In the first half of the year, I led the development of Medicare RAP model monitoring by partnering with DE to productionize the RAP model-metrics collection DAG and stand up core dashboards in near real time. I facilitated multiple model workgroup sessions with Clinical DS and DE to standardize key monitoring metrics, curated the code base for those metrics, and laid the groundwork for intelligent monitoring by defining checks on score distributions, feature quality, data drift, and model performance. During the second half of the year, I focused on optimizing when members are identified for RAP by designing a LOS-based predicted discharge approach and refining discharge-date/identification logic. This work helps shift referrals from “early” inpatient cases toward the early post-discharge window, when members are more reachable, so that CM receives cases at a more actionable time, improving CM workflow and increasing CM efficiency and member engagement, while simultaneously reducing low-yield outreach and UTR rates.

In parallel, I supported high-impact adhoc and evaluation work across programs. I contributed to the SNF Length of Stay analysis and related post-acute work, helping to interpret results and highlight implications on the feasibility of how the SNF Risk Score can be used as a proxy for LOS estimation. I partnered with Clinical and Product teams on the Great Lakes ER Diversion Evaluation study and follow-up action items, translating analytical findings into clear recommendations for program refinement. On the innovation side, I mentored a summer intern on RAP model enhancement using clinical notes and GenAI/LLM techniques, guiding her through problem framing, feature engineering, and model evaluation while ensuring alignment with team goals. I additionally collaborated with DE on evolving the RAP monitoring work into a broader MLOps framework, including discussions on standard pipelines and scheduling monitoring jobs in the cloud environment. Overall, I focused on delivering reliable analytics products, improving operational timeliness and usability of RAP outputs for CM, and fostering strong collaboration across clinical, product, SHJ, and engineering partners.

In addition to the above, I:
	•	Collaborated with the Data Engineering team to establish more standardized and scalable processes for RAP data pipelines and monitoring.
	•	Supported the post-SHJ transition by updating RAP/SNF reporting to point to the SHJ engine and refining reporting logic for key metrics such as Engaged, Targeted, and Unique Individuals, ensuring consistency between routing and reporting.
	•	Performed RAP dashboard QC in partnership with Rich, reviewing underlying logic, correcting code issues, and validating metrics to strengthen confidence in RAP reporting.
	•	Investigated several SHJ operational issues, including denied service auths being identified too late due to missing discharge dates, and worked with the SHJ team to implement a solution that censors RAP scores for members with >30 days since admit.
	•	Analyzed the SHJ/RAP API prioritization of Service Auth to better understand how service authorizations are ranked and how RAP scores can be used most effectively for case selection.
	
	
	








Over the course of 2025, I continued to strengthen the Readmission Avoidance Program analytics foundation while improving how RAP models are monitored and operationalized. In the first half of the year, I led the development of Medicare RAP model monitoring by partnering with DE to productionize the RAP model-metrics collection DAG and stand up core dashboards in near real time. I facilitated multiple model workgroup sessions with Clinical DS and DE to standardize key monitoring metrics, curated the code base for those metrics, and laid the groundwork for intelligent monitoring by defining checks on score distributions, feature quality, data drift and model performance. During the second half of the year I focused on optimizing when members are identified for RAP by designing a LOS-based predicted discharge approach and refining discharge-date/identification logic. This work helps shift referrals from “early” inpatient cases toward the early post-discharge window, when members are more reachable, so that CM receives cases at a more actionable time, improving CM workflow and increasing CM efficiency and member engagement, while simultaneously reducing low-yield outreach and UTR rates.

In parallel, I supported high-impact adhoc and evaluation work across programs. I contributed to the SNF Length of Stay analysis and related post-acute work, helping to interpret results and highlight implications on the feasibility of how SNF Risk Score can be used as a proxy for LOS estimation. I partnered with Clinical and Product teams on the Great Lakes ER Diversion Evaluation study and follow-up action items, translating analytical findings into clear recommendations for program refinement. On the innovation side, I mentored a summer intern on RAP model enhancement using clinical notes and GenAI/LLM techniques, guiding her through problem framing, feature engineering, and model evaluation while ensuring alignment with team goals. I additionally collaborated with DE on evolving the RAP monitoring work into a broader MLOps framework, including discussions on standard pipelines and scheduling monitoring jobs in the cloud environment. Overall, I focused on delivering reliable analytics products, improving operational timeliness and usability of RAP outputs for CM, and fostering strong collaboration across clinical, product, SHJ, and engineering partners.

Additional work this year included:
	•	Collaborate with the Data Engineering team to establish a standardized and scalable process.
	•	Post SHJ : we need to change the reporting to point to SHJ engine. Update the RAP/SNF Reporting logic like #Engaged, #Targeted  #Unique_Individuals, etc.
	•	RAP Dashboard QC on Metrics: Worked with Rich in finding RAP Dashboard logic review, code correction and QC Check.
	•	Various Investigation around SHJ Operations : 1. Some of Denied Service Auth’s were identified too late in the system because of missing discharge date; implemented a solution working with SHJ team – proposed approach to censor RAP scores for members with >30 days since admit.
	•	SHJ/ RAP API : Investigate prioritization of Service Auth.








Over the course of 2025, I continued to strengthen the Readmission Avoidance Program analytics foundation while improving how RAP models are monitored and operationalized. In the first half of the year, I led the development of Medicare RAP model monitoring by partnering with DE to productionize the RAP model-metrics collection DAG and stand up core dashboards in near real time. I facilitated multiple model workgroup sessions with Clinical DS and DE to standardize key monitoring metrics, curated the code base for those metrics, and laid the groundwork for intelligent monitoring by defining checks on score distributions, feature stability, and model performance. Building on this, in the second half of the year I focused on optimizing when members are identified for RAP by designing a LOS-based predicted discharge approach and refining discharge-date/identification logic. This work helps shift referrals from “too-early” inpatient cases toward the early post-discharge window so that CM receives cases at a more actionable time, improving referral quality and workflow.

In parallel, I supported high-impact adhoc and evaluation work across programs. I contributed to the SNF Length of Stay analysis and related post-acute work, helping to interpret results and highlight implications for how SNF and acute programs complement each other. I also partnered with Clinical and Product teams on the Great Lakes ER Diversion Evaluation study and follow-up action items, translating analytical findings into clear recommendations for program refinement. On the innovation side, I mentored a summer intern on RAP model enhancement using clinical notes and GenAI/LLM techniques, guiding her through problem framing, feature engineering, and model evaluation while ensuring alignment with enterprise goals. I additionally collaborated with DE on evolving the RAP monitoring work into a broader MLOps framework, including discussions on standard pipelines and scheduling monitoring jobs in the cloud environment. Overall, I focused on delivering reliable analytics products, improving operational timeliness and usability of RAP outputs for CM, and fostering strong collaboration across clinical, product, SHJ, and engineering partners.











Readmission Avoidance Program (RAP) Initiatives

RAP Scoring Timing Optimization – LOS-Based Predicted Discharge
	•	Identified an operational gap in when Medicare IP members are first scored for RAP relative to discharge.
	•	Designed a simple LOS-based predicted discharge framework and showed how re-anchoring scoring around predicted discharge shifts referrals from “too-early” inpatient cases to early post-discharge, when members are more reachable.
	•	Framed the work as a timing optimization (no model change), translated results into an executive-ready story, and recommended a pilot to Medicare CM leadership to improve referral quality and CM workflow.

RAP Model Monitoring and Intelligent Monitoring Foundation
	•	Led the buildout of a standardized Medicare RAP model monitoring framework in partnership with Data Engineering, including metric definitions, collection logic, and near real-time dashboards.
	•	Facilitated workgroup sessions with Clinical DS and DE to align on key monitoring metrics and ensure consistency between models and reporting.
	•	Laid the groundwork for intelligent monitoring by defining logic to track score distributions, feature stability, and outreach performance, enabling earlier detection of issues post-deployment.

RAP–SHJ Integration and Identification Logic
	•	Collaborated with the SHJ team to refine how RAP scores are consumed in the SHJ engine so that case routing better reflects nurse capacity, program goals, and engagement rules.
	•	Streamlined RAP identification logic to be more consistent with program identification, improving transparency for partners on which members are flagged and why.
	•	Conducted discharge-date investigations and follow-up analyses to ensure that identification timing aligns with actual discharge and avoids missed or premature referrals.

⸻

Post-Acute / SNF and Transitions of Care Analytics

SNF Length of Stay and Post-Acute Performance vs. RAP Acute
	•	Conducted analyses comparing SNF program performance to RAP acute, focusing on measures such as length of stay, readmissions, and engagement.
	•	Evaluated how SNF risk scores help identify long-stay or high-need SNF admissions and where they add unique value beyond acute RAP models.
	•	Summarized findings for clinical and product partners to inform future direction of post-acute programs and Transitions of Care product roadmaps.

Data Quality and Pipeline Refinements for Acute and Post-Acute Metrics
	•	Worked with DE to remove transplant IP cases from the ACC/RAP pipeline where clinical pathways differ, improving the relevance of model outputs and reporting.
	•	Performed QC checks on RAP dashboards to ensure alignment between metric definitions, filters, and pipeline logic, strengthening stakeholder trust in reported performance.

⸻

ER Diversion Evaluation and Program Insights

Great Lakes ER Diversion – Evaluation Study and Action Items
	•	Partnered with Clinical and Product teams on the Great Lakes ER Diversion evaluation, helping define metrics, refine the design, and interpret program performance.
	•	Translated analytical findings into clear recommendations and action items, supporting refinement of ER diversion strategy and prioritization of next steps.

⸻

Advanced Methods, Risk Adjustment, and Ad-Hoc Analytics

Propensity and Matching Methods for Program Evaluation
	•	Implemented and supported propensity-based matching and weighting methods to better align treatment and comparison groups in evaluations.
	•	Helped teams interpret results and understand the trade-offs of different approaches, improving the rigor and credibility of program impact estimates.

Enhanced Context and Risk-Adjustment Flags
	•	Added and validated new context flags (VBC vs. non-VBC, PCP attribution, SDOH-related indicators, rural/urban and accessibility flags) to strengthen risk adjustment and segmentation.
	•	Enabled more nuanced reporting and evaluation by giving stakeholders the ability to slice results by provider type, social risk, and geography.

⸻

Innovation Pilot, MLOps, and Mentorship

LLM / GenAI-Enabled RAP Enhancements and Intern Mentorship
	•	Piloted the use of LLM/GenAI and clinical notes to enhance RAP models, exploring how unstructured data can improve prediction and member stratification.
	•	Mentored a summer intern on Commercial RAP model enhancement using clinical notes and GenAI/LLM techniques, guiding them through problem framing, feature engineering, evaluation, and alignment with enterprise goals.

MLOps Framework and Collaboration with Data Engineering
	•	Partnered with DE to evolve the RAP monitoring work into a broader MLOps framework, including discussions on standard pipelines, scheduling of monitoring jobs in the cloud environment, and how to scale the approach across models.
	•	Helped bridge analytics and engineering perspectives, ensuring that monitoring solutions are both technically sound and practically useful for clinical and CM stakeholders.











Slide 4 – Proposed Change & Pilot Plan

Title:

Pilot LOS-Anchored RAP Scoring for Medicare

Bullets:
	•	Proposed change
	•	Anchor Medicare RAP identification to predicted discharge date (0-day shift).
	•	When actual discharge date arrives earlier in auth data, use that instead of prediction.
	•	No change to RAP risk scores or thresholds – only the timing of first identification.
	•	Expected impact
	•	Increase first scores in the 0–4 day post-discharge window from 28% → 57%.
	•	Reduce inpatient/too-early scoring from 69% → 41% and on/before admit from 24% → 6%.
	•	Maintain capture within 4 days of discharge at ~98%.
	•	Pilot & measure
	•	Run a time-boxed pilot for Medicare RAP.
	•	Track: % in 0–4 days, engagement/UTR, CM feedback on workload.
	•	Use results to decide on scaling and whether to extend to other LOBs.






import pandas as pd

# (optional) tag them if not already tagged
train_feat = train_feat.copy()
test_feat  = test_feat.copy()

train_feat['set'] = 'train'
test_feat['set']  = 'test'

# Combine
full_feat = pd.concat([train_feat, test_feat], axis=0)

# Keep original row order if you care about it
full_feat = full_feat.sort_index()

# Now you can do:
# full_feat[full_feat['set'] == 'test']  -> test rows
# full_feat[full_feat['set'] == 'train'] -> train rows









import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error

# ======================
# 1) Train / test split
# ======================
train_df, test_df = train_test_split(df2, test_size=0.3, random_state=42)

# Global median LOS from TRAIN only (last fallback)
global_median_los = train_df['tum_act_los_day_cnt'].median()

# ============================================
# 2) Build LOS stats FROM TRAIN DATA ONLY
# ============================================

# a) By diagnosis group
los_stats_grp = (
    train_df
      .groupby('icd9_dx_group_nbr')['tum_act_los_day_cnt']
      .agg(['mean', 'median'])
      .reset_index()
)
los_stats_grp.columns = ['icd9_dx_group_nbr', 'avg_los_grp', 'median_los_grp']

# b) By diagnosis category
los_stats_ctg = (
    train_df
      .groupby('icd9_dx_ctg_cd')['tum_act_los_day_cnt']
      .agg(['mean', 'median'])
      .reset_index()
)
los_stats_ctg.columns = ['icd9_dx_ctg_cd', 'avg_los_ctg', 'median_los_ctg']

# c) By diag + service type + admission status
los_stats_all = (
    train_df
      .groupby(['icd9_dx_group_nbr', 'tum_stay_srv_type_cd', 'SAAdmissionStatusType'])['tum_act_los_day_cnt']
      .agg(['mean', 'median'])
      .reset_index()
)
los_stats_all.columns = [
    'icd9_dx_group_nbr', 'tum_stay_srv_type_cd', 'SAAdmissionStatusType',
    'avg_los_all', 'median_los_all'
]

# ============================================
# 3) Merge stats into train & test
# ============================================

def add_los_features(df):
    df = df.copy()
    df = df.merge(los_stats_grp, on='icd9_dx_group_nbr', how='left')
    df = df.merge(los_stats_ctg, on='icd9_dx_ctg_cd', how='left')
    df = df.merge(
        los_stats_all,
        on=['icd9_dx_group_nbr', 'tum_stay_srv_type_cd', 'SAAdmissionStatusType'],
        how='left'
    )
    return df

train_feat = add_los_features(train_df)
test_feat  = add_los_features(test_df)

# ============================================
# 4) Backfill logic for predicted LOS
#     median_los_all -> median_los_grp -> median_los_ctg -> global median
# ============================================

def build_rule_based_pred(df):
    df = df.copy()
    # start with the most granular median
    pred = df['median_los_all'].copy()

    # record where each fallback kicks in (for diagnostics)
    missing_all = pred.isna()                            # no all-level median
    pred[missing_all] = df.loc[missing_all, 'median_los_grp']

    missing_grp = pred.isna()                            # still NaN after grp
    pred[missing_grp] = df.loc[missing_grp, 'median_los_ctg']

    missing_ctg = pred.isna()                            # still NaN after ctg
    pred[missing_ctg] = global_median_los                # final fallback

    df['pred_los_rule'] = pred
    df['_missing_all'] = missing_all
    df['_missing_grp'] = missing_grp
    df['_missing_ctg'] = missing_ctg
    return df

train_feat = build_rule_based_pred(train_feat)
test_feat  = build_rule_based_pred(test_feat)

# ============================================
# 5) Check if backfilling was used (TEST ONLY)
# ============================================

print("=== Backfill usage on TEST set ===")
n_test = len(test_feat)

n_missing_all = test_feat['_missing_all'].sum()
n_missing_grp = test_feat['_missing_grp'].sum()
n_missing_ctg = test_feat['_missing_ctg'].sum()

print(f"Rows with NO median_los_all (needed grp/ctg/global fallback): {n_missing_all} "
      f"({n_missing_all / n_test:.2%})")
print(f"Rows still missing after grp fallback (needed ctg/global):   {n_missing_grp} "
      f"({n_missing_grp / n_test:.2%})")
print(f"Rows still missing after ctg fallback (used global median):  {n_missing_ctg} "
      f"({n_missing_ctg / n_test:.2%})")

# You can also see whether any backfilling happened at all:
used_any_backfill = n_missing_all > 0
print(f"\nDid we use any backfilling on test? {'YES' if used_any_backfill else 'NO'}")

# ============================================
# 6) Optional: evaluate rule-based predictor on TEST
# ============================================
y_test = test_feat['tum_act_los_day_cnt']
mae = mean_absolute_error(y_test, test_feat['pred_los_rule'])
mse = mean_squared_error(y_test, test_feat['pred_los_rule'])
print(f"\nRule-based LOS predictor (with backfill) on TEST: MAE={mae:.4f}, MSE={mse:.4f}")





import numpy as np
import matplotlib.pyplot as plt

def plot_lag_hist_pretty(lag_series, title, x_min=-10, x_max=10):
    """
    Clean histogram + cumulative percent plot for lag distribution.
    Adds:
      - % label on each histogram bar
      - cumulative % curve with labels
    """

    # Clean / clip
    lag = lag_series.dropna().astype(int)
    lag_clipped = lag.clip(lower=x_min, upper=x_max)

    # Integer bins
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)
    counts, edges = np.histogram(lag_clipped, bins=bins)
    centers = np.arange(x_min, x_max + 1)

    # Cumulative %
    cum_pct = np.cumsum(counts) / counts.sum() * 100
    # Per-bin %
    bin_pct = counts / counts.sum() * 100

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Histogram bars
    bars = ax1.bar(
        centers,
        counts,
        width=0.8,
        edgecolor="black",
        linewidth=0.5,
        alpha=0.7,
    )

    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)
    ax1.set_xlim(x_min - 0.5, x_max + 0.5)
    ax1.set_xticks(np.arange(x_min, x_max + 1))

    # ==== NEW: % LABELS ON TOP OF EACH BAR ====
    for x, h, p in zip(centers, counts, bin_pct):
        if h == 0:
            continue  # skip empty bins
        ax1.text(
            x,
            h,
            f"{p:.0f}%",        # e.g., 24%
            ha="center",
            va="bottom",
            fontsize=8,
        )

    # Cumulative % line
    ax2 = ax1.twinx()
    ax2.plot(
        centers,
        cum_pct,
        marker="o",
        linewidth=2,
    )
    ax2.set_ylabel("Cumulative % of cases")
    ax2.set_ylim(0, 105)

    # Labels on cumulative line
    for x, y in zip(centers, cum_pct):
        ax2.text(
            x,
            y + 1,
            f"{int(y)}%",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    plt.tight_layout()
    plt.show()
    
    
plot_lag_hist_pretty(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge"
)









Medicare RAP Timing Proposal — Slides + Extra Talking Points (Text Version)

--------------------------------------------------
Slide 1: Current RAP Timing for Medicare Inpatient (IP)
--------------------------------------------------

Main Points:
• RAP currently scores Medicare inpatient members as soon as an authorization is received.
• In the 2025 Medicare sample:
  - 69% of identifications occur before the discharge date.
  - 28% occur in the 0–4 days post-discharge window.
  - About 2% occur 5 or more days after discharge.

Extra Talking Points:
• Highlight that these are descriptive statistics, not a judgment on the current process.
• Note that the 0–4 day post-discharge window is generally a more actionable period for outreach.
• Mention that the purpose of the work is to understand timing patterns and explore improvements.

--------------------------------------------------
Slide 2: Using Predicted Discharge Date to Shift RAP Timing
--------------------------------------------------

Main Points:
• We simulated using a simple LOS-based predicted discharge date instead of scoring at authorization.
• Comparison of timing of first RAP identification:
  - Current: 69% before discharge, 28% in 0–4 days post-discharge, ~2% at 5+ days.
  - Proposed: 41% before discharge, 57% in 0–4 days post-discharge, ~2–3% at 5+ days.
• Under the proposed approach, more members are first identified in the immediate post-discharge window, where outreach can be more impactful.

Extra Talking Points:
• Clarify that the simulation used actual historical data, not assumptions.
• Emphasize that late identifications remain relatively stable while timing shifts toward the post-discharge period.
• Note that this is an adjustment to timing, not a change in who is eligible for RAP.

--------------------------------------------------
Slide 3: Cumulative Capture of RAP Identifications by Days Since Discharge
--------------------------------------------------

Main Points:
• We examined cumulative capture of first RAP identification by days since discharge.
• For both the current and proposed approaches, approximately 97–98% of members are captured by 4 days post-discharge.
• The proposed approach shifts more first identifications into the 0–4 day post-discharge window rather than before discharge.

Extra Talking Points:
• Use this slide to reassure stakeholders that overall coverage remains similar across approaches.
• Explain that the key difference is the distribution of when first contact becomes possible.
• You can reference the shaded 0–4 day window on the chart as the key opportunity zone.

--------------------------------------------------
Slide 4: Member Journey and Recommended Change for Medicare RAP
--------------------------------------------------

Main Points:
• Conceptually, the current process tends to identify members closer to the admission portion of the stay.
• The proposed process shifts identification closer to discharge and the first few days after members return home.
• Recommendation for Medicare RAP:
  - Use a predicted discharge date (LOS-based) as the anchor for RAP identification timing.
  - When the actual discharge date is available earlier in the auth system, use that date instead.
  - Start with a pilot and monitor engagement, UTR, and the share of identifications in the 0–4 day post-discharge window.

Extra Talking Points:
• Narrate a simple patient story to illustrate the difference between being contacted while inpatient versus shortly after returning home.
• Note that the recommendation is to pilot and measure impact, not to immediately enforce a system-wide change.
• Highlight alignment with CM workflow: more contacts aligned with discharge and early recovery.

--------------------------------------------------
Slide 5: How We Estimate Discharge Date Using Rule-Based LOS
--------------------------------------------------

Main Points:
• We use a simple, transparent, rule-based approach to estimate discharge timing, not a black-box ML model.
• Historical development data:
  - 2024 Medicare inpatient stays used to derive LOS patterns.
  - 2025 data used to evaluate accuracy.
• Grouping dimensions for LOS estimation:
  - Diagnosis group.
  - Stay service type (e.g., Medical / Surgical).
  - Admission status (e.g., Emergency / Elective / Urgent).
• For each (diagnosis group, stay service type, admission status) combination, we compute median LOS as the primary predictor.
• We also evaluated average LOS and simpler diagnosis-only groupings for comparison.
• Prediction rule used in the simulation:
  - Predicted LOS = median LOS for the matching group.
  - Predicted discharge date = admit date + predicted LOS (in days).
• Performance on 2025 Medicare data:
  - Mean Absolute Error (MAE) ≈ 2.2 days.
  - Enhanced grouping improves MAE versus diagnosis-only.
• Operational takeaway:
  - This level of accuracy is sufficient to move RAP timing closer to discharge while maintaining coverage.
  - The approach is easy to explain to clinicians, auditable, and straightforward to maintain.

Extra Talking Points:
• If asked whether this is “AI,” clarify that it is a rule-based approach derived from historical patterns.
• Reassure stakeholders that the method is interpretable and can be adjusted if clinical feedback suggests refinements.
• Mention that if needed in the future, more advanced models could be explored, but the current rule-based solution already delivers meaningful timing improvements.







import numpy as np
import matplotlib.pyplot as plt

def plot_lag_hist_pretty(lag_series, title, x_min=-10, x_max=10, y_max=None):
    """
    Pretty histogram + correct cumulative capture curve (0–x days only).
    Early days (<0) do NOT contribute to cumulative capture.
    """

    # Drop NA & convert to int
    lag = lag_series.dropna().astype(int)

    # Clip extreme values to range
    lag_clip = lag.clip(lower=x_min, upper=x_max)

    # Build integer bins
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)
    counts, edges = np.histogram(lag_clip, bins=bins)
    centers = np.arange(x_min, x_max + 1)

    total = counts.sum()

    # ----- CORRECT cumulative capture: only count days >= 0 -----
    post_counts = np.where(centers >= 0, counts, 0)
    cum_capture = np.cumsum(post_counts) / total * 100

    # ==== PLOT ====
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Histogram
    ax1.bar(
        centers,
        counts,
        width=0.8,
        alpha=0.7,
        color="#7BAAF7",
        edgecolor="black"
    )

    if y_max:
        ax1.set_ylim(0, y_max)

    ax1.set_xlim(x_min - 0.5, x_max + 0.5)
    ax1.set_xticks(centers)
    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)

    # Cumulative curve on second axis
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_capture, color="darkred", marker="o")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative % (0–x days only)")

    # Label only for days >= 0
    for x, y in zip(centers, cum_capture):
        if x >= 0:
            ax2.text(x, y + 1, f"{int(y)}%", ha="center", fontsize=9)

    # Vertical guideline at day 4
    ax2.axvline(4, color="gray", ls="--")

    # Print capture rate on graph
    capture_0_4 = post_counts[(centers >= 0) & (centers <= 4)].sum() / total * 100
    ax2.text(4, capture_0_4 + 5,
             f"0–4 Day Capture = {capture_0_4:.2f}%",
             ha="center", fontsize=10, color="black")

    plt.show()
    
    

global_max = max(lag_current.value_counts().max(),
                 lag_pred.value_counts().max())

plot_lag_hist_pretty(
    lag_current,
    "Current Scoring Lag vs Actual Discharge",
    y_max=global_max
)

plot_lag_hist_pretty(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge",
    y_max=global_max
)









def compute_capture_cum(centers, counts):
    """
    Correct cumulative capture curve: 
    Includes only days >= 0 and <= x.
    Early days contribute ZERO.
    """
    total = counts.sum()
    
    # Zero out early days
    post_counts = np.where(centers >= 0, counts, 0)

    # Cumulative ONLY from 0 upward
    cum = np.cumsum(post_counts)

    cum_pct = cum / total * 100
    return cum_pct
    
    

def plot_correct_capture(lag_series, title, x_min=-10, x_max=10, y_max=None):
    lag = lag_series.dropna().astype(int)
    lag_clip = lag.clip(lower=x_min, upper=x_max)

    # Build integer bins
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)
    counts, edges = np.histogram(lag_clip, bins=bins)
    centers = np.arange(x_min, x_max + 1)

    total = counts.sum()

    # ----- CORRECT cumulative (capture only: 0–4 days) -----
    post_counts = np.where(centers >= 0, counts, 0)
    cum_post = np.cumsum(post_counts) / total * 100

    # capture rate EXACTLY matches your summary table
    capture_rate = post_counts[(centers >= 0) & (centers <= 4)].sum() / total * 100

    # ========== PLOT ==========
    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Histogram
    ax1.bar(
        centers, counts,
        width=0.8, alpha=0.7,
        color="#7BAAF7", edgecolor="black"
    )

    if y_max:
        ax1.set_ylim(0, y_max)

    ax1.set_xlim(x_min - 0.5, x_max + 0.5)
    ax1.set_xticks(centers)
    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)

    # Cumulative curve showing CAPTURE ONLY
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_post, color="darkred", marker="o")
    ax2.set_ylim(0, 105)
    ax2.set_ylabel("Cumulative % (0–x days only)")

    # Label
    for x, y in zip(centers, cum_post):
        if x >= 0:
            ax2.text(x, y+1, f"{int(y)}%", ha="center")

    # Vertical line at 4 days
    ax2.axvline(4, color="gray", ls="--")
    ax2.text(4, capture_rate+3, f"Capture 0–4 days = {capture_rate:.2f}%", 
             ha="center", fontsize=10)

    plt.show()
    
    
    




















import numpy as np
import matplotlib.pyplot as plt

def plot_lag_hist_pretty_capture(lag_series, title, x_min=-10, x_max=10, y_max=None):
    lag = lag_series.dropna().astype(int)
    lag_clipped = lag.clip(lower=x_min, upper=x_max)

    # integer bins
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)
    counts, edges = np.histogram(lag_clipped, bins=bins)
    centers = np.arange(x_min, x_max + 1)  # -10 .. 10

    total = counts.sum()

    # ----- cumulative for ALL cases (P(lag <= x)) -----
    cum_pct_all = np.cumsum(counts) / total * 100

    # ----- cumulative for POST-DISCHARGE ONLY (P(0 <= lag <= x)) -----
    counts_post = counts.copy()
    counts_post[centers < 0] = 0           # zero out early bins
    cum_pct_post = np.cumsum(counts_post) / total * 100

    # capture rate = P(0 <= lag <= 4)
    capture_mask = (centers >= 0) & (centers <= 4)
    capture_rate = counts_post[capture_mask].sum() / total * 100

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Histogram
    ax1.bar(
        centers,
        counts,
        width=0.8,
        color="#7BAAF7",
        edgecolor="black",
        linewidth=0.5,
        alpha=0.7
    )
    if y_max is not None:
        ax1.set_ylim(0, y_max)

    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)
    ax1.set_xlim(x_min - 0.5, x_max + 0.5)
    ax1.set_xticks(np.arange(x_min, x_max + 1))

    # Cumulative %: POST-DISCHARGE ONLY (this is what you care about)
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_pct_post, marker="o", color="#B71C1C", linewidth=2, label="Cum % (0+ days)")
    ax2.set_ylabel("Cumulative % of cases")
    ax2.set_ylim(0, 105)

    # Label curve
    for x, y in zip(centers, cum_pct_post):
        if x >= 0:  # label only non-negative days to avoid clutter
            ax2.text(x, y + 1, f"{int(y)}%", ha="center", va="bottom", fontsize=8)

    # Mark capture at 4 days explicitly
    ax2.axvline(4, color="gray", linestyle="--", linewidth=1)
    ax2.text(4, capture_rate + 3, f"Capture 0–4d: {capture_rate:.0f}%", 
             ha="center", va="bottom", fontsize=9, color="black")

    plt.tight_layout()
    plt.show()
    
    
global_max = max(lag_current.value_counts().max(),
                 lag_pred.value_counts().max())

plot_lag_hist_pretty_capture(
    lag_current,
    "Current Scoring Lag vs Actual Discharge (−10 to +10)",
    x_min=-10, x_max=10, y_max=global_max
)

plot_lag_hist_pretty_capture(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge (−10 to +10)",
    x_min=-10, x_max=10, y_max=global_max
)









# compute shared Y-axis limit
global_max = max(lag_current.value_counts().max(),
                 lag_pred.value_counts().max())

plot_lag_hist_pretty(
    lag_current,
    "Current Scoring Lag vs Actual Discharge (−10 to +10)",
    y_max=global_max
)

plot_lag_hist_pretty(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge (−10 to +10)",
    y_max=global_max
)





global_max = max(lag_current.value_counts().max(),
                 lag_pred.value_counts().max())
                
                
                
def plot_lag_hist_pretty(lag_series, title, x_min=-10, x_max=10, y_max=None):
    lag = lag_series.dropna().astype(int)
    lag_clipped = lag.clip(lower=x_min, upper=x_max)

    # integer bins
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)
    counts, edges = np.histogram(lag_clipped, bins=bins)
    centers = np.arange(x_min, x_max + 1)

    cum_pct = np.cumsum(counts) / counts.sum() * 100

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Histogram
    ax1.bar(
        centers,
        counts,
        width=0.8,
        color="#7BAAF7",
        edgecolor="black",
        linewidth=0.5,
        alpha=0.7
    )

    # FORCE SAME Y-LIMIT FOR ALL PLOTS
    if y_max is not None:
        ax1.set_ylim(0, y_max)

    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)
    ax1.set_xlim(x_min - 0.5, x_max + 0.5)
    ax1.set_xticks(np.arange(x_min, x_max + 1))

    # cumulative % line
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_pct, marker="o", color="#B71C1C", linewidth=2)
    ax2.set_ylabel("Cumulative % of cases")
    ax2.set_ylim(0, 105)

    for x, y in zip(centers, cum_pct):
        ax2.text(x, y + 1, f"{int(y)}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.show()









import numpy as np
import matplotlib.pyplot as plt

def plot_lag_hist_pretty(lag_series, title, x_min=-10, x_max=10):
    """
    Clean histogram + cumulative percent plot for lag distribution.
    """
    lag = lag_series.dropna().astype(int)

    # Clip extreme values into visible range
    lag_clipped = lag.clip(lower=x_min, upper=x_max)

    # Integer bins
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)

    counts, edges = np.histogram(lag_clipped, bins=bins)

    # Centers for bars & cumulative points
    centers = np.arange(x_min, x_max + 1)

    # cumulative %
    cum_pct = np.cumsum(counts) / counts.sum() * 100

    fig, ax1 = plt.subplots(figsize=(12, 7))

    # Clean histogram
    ax1.bar(
        centers,
        counts,
        width=0.8,
        color="#7BAAF7",
        edgecolor="black",
        linewidth=0.5,
        alpha=0.7
    )

    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)

    ax1.set_xlim(x_min - 0.5, x_max + 0.5)
    ax1.set_xticks(np.arange(x_min, x_max + 1))

    # Cumulative line (clean)
    ax2 = ax1.twinx()
    ax2.plot(
        centers,
        cum_pct,
        marker="o",
        color="#B71C1C",
        linewidth=2
    )
    ax2.set_ylabel("Cumulative % of cases")
    ax2.set_ylim(0, 105)

    # Add labels on curve
    for x, y in zip(centers, cum_pct):
        ax2.text(x, y + 1, f"{int(y)}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.show()


# ===== CALLS =====

plot_lag_hist_pretty(
    lag_current,
    "Current Scoring Lag vs Actual Discharge (–10 to +10)"
)

plot_lag_hist_pretty(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge (–10 to +10)"
)










import numpy as np
import matplotlib.pyplot as plt

def plot_lag_hist_with_cum(lag_series, title, x_min=-10, x_max=10):
    """
    lag_series: Series of ints/floats in days.
    x_min, x_max: integer range to display on x-axis.
    Values < x_min and > x_max are clipped into the edge bins.
    """
    lag = lag_series.dropna().astype(int)

    # clip extreme values into visible range
    lag_clipped = lag.clip(lower=x_min, upper=x_max)

    # integer-day bins: [x_min, x_min+1, ..., x_max+1]
    # each bar is 1 day wide, starting at the integer
    bins = np.arange(x_min, x_max + 2, 1)  # +2 so last bin is [x_max, x_max+1)

    counts, edges = np.histogram(lag_clipped, bins=bins)

    # bar positions: left edges are integers
    left_edges = edges[:-1]  # x_min .. x_max
    centers = left_edges + 0.5  # for cumulative line

    total = counts.sum()
    cum_counts = np.cumsum(counts)
    cum_pct = cum_counts / total * 100

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # histogram: one bar per integer day
    ax1.bar(left_edges, counts, width=1.0, align="edge", color="#4a90e2", alpha=0.7)
    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)

    # show only integer days from x_min to x_max
    ax1.set_xlim(x_min, x_max + 1)
    ax1.set_xticks(range(x_min, x_max + 1))

    # cumulative % line
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_pct, marker="o", color="darkred")
    ax2.set_ylabel("Cumulative % of cases")
    ax2.set_ylim(0, 105)

    # labels on cumulative points
    for x, y in zip(centers, cum_pct):
        ax2.text(x, y, f"{y:.0f}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.show()


# ===== Reuse your lag_current and lag_pred from before =====

plot_lag_hist_with_cum(
    lag_current,
    "Current Scoring Lag vs Actual Discharge Date (−10 to +10)",
    x_min=-10,
    x_max=10
)

plot_lag_hist_with_cum(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge Date (−10 to +10)",
    x_min=-10,
    x_max=10
)










import numpy as np
import matplotlib.pyplot as plt

def plot_lag_hist_with_cum(lag_series, title, x_min=-10, x_max=10):
    """
    lag_series: Series of ints/floats in days.
    x_min, x_max: range to display on x-axis.
    Tails (<x_min and >x_max) are clipped into the edge bins,
    so cumulative % still goes to 100%.
    """
    lag = lag_series.dropna().astype(int)

    # clip extreme values into the visible range
    lag_clipped = lag.clip(lower=x_min, upper=x_max)

    # integer-day bins from x_min to x_max
    bins = np.arange(x_min - 0.5, x_max + 1.5, 1)

    counts, edges = np.histogram(lag_clipped, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2

    total = counts.sum()
    cum_counts = np.cumsum(counts)
    cum_pct = cum_counts / total * 100

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # histogram (counts)
    ax1.bar(centers, counts, width=0.9, color="#4a90e2", alpha=0.7)
    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)
    ax1.set_xlim(x_min - 0.5, x_max + 0.5)

    # cumulative % line
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_pct, marker="o", color="darkred")
    ax2.set_ylabel("Cumulative % of cases")
    ax2.set_ylim(0, 105)   # a bit above 100 for labels

    # labels on cumulative points
    for x, y in zip(centers, cum_pct):
        ax2.text(x, y, f"{y:.0f}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.show()


# ===== Reuse your lag_current and lag_pred from before =====

plot_lag_hist_with_cum(
    lag_current,
    "Current Scoring Lag vs Actual Discharge Date (Zoomed –10 to +10)",
    x_min=-10,
    x_max=10
)

plot_lag_hist_with_cum(
    lag_pred,
    "Predicted Discharge Scoring Lag vs Actual Discharge Date (Zoomed –10 to +10)",
    x_min=-10,
    x_max=10
)










import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------------------
# 1. Build predicted scoring date (NO SHIFT)
# -------------------------------------------------------------

# predicted discharge date from LOS
pred_dc = df["pred_discharge_dt"]

# actual auth discharge date & its load date
auth_dc = df["auth_actual_discharge_dt"]
auth_load = df["auth_actual_discharge_load_dt"]

# rule:
# if auth_discharge_dt is loaded BEFORE predicted_dc → use auth_dc
# else → use predicted discharge date
use_auth = (
    auth_dc.notna() &
    auth_load.notna() &
    (auth_load <= pred_dc)
)

sim_scoring_dt = pred_dc.copy()
sim_scoring_dt[use_auth] = auth_dc[use_auth]   # override


# -------------------------------------------------------------
# 2. Compute lags (days between scoring date and true discharge)
# -------------------------------------------------------------
actual_dc = df["tum_actual_discharge_dt"]

lag_current = (df["first_scored_dt"] - actual_dc).dt.days
lag_pred = (sim_scoring_dt - actual_dc).dt.days


# -------------------------------------------------------------
# 3. Helper plot function: Histogram + cumulative %
# -------------------------------------------------------------
def plot_lag_hist_with_cum(lag_series, title):
    lag = lag_series.dropna().astype(int)

    # integer-day bins
    bin_min = lag.min()
    bin_max = lag.max()
    bins = np.arange(bin_min - 0.5, bin_max + 1.5, 1)

    counts, edges = np.histogram(lag, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2

    total = counts.sum()
    cum_counts = np.cumsum(counts)
    cum_pct = cum_counts / total * 100

    # figure
    fig, ax1 = plt.subplots(figsize=(10, 6))

    # histogram (counts)
    ax1.bar(centers, counts, width=0.9, color="#4a90e2", alpha=0.7)
    ax1.set_xlabel("Days since actual discharge (lag)")
    ax1.set_ylabel("Number of cases")
    ax1.set_title(title)

    # cumulative % curve
    ax2 = ax1.twinx()
    ax2.plot(centers, cum_pct, marker="o", color="darkred")
    ax2.set_ylabel("Cumulative % of cases")

    # label cumulative % on each point
    for x, y in zip(centers, cum_pct):
        ax2.text(x, y, f"{y:.0f}%", ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.show()


# -------------------------------------------------------------
# 4. PLOTS
# -------------------------------------------------------------

plot_lag_hist_with_cum(
    lag_current,
    "Current Scoring Lag vs Actual Discharge Date"
)

plot_lag_hist_with_cum(
    lag_pred,
    "Predicted Discharge Date — Scoring Lag vs Actual Discharge Date"
)













import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 0. Make sure these datetime columns exist in df
# ---------------------------------------------------------
for c in [
    'actual_admit_dt',
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_admit  = df['actual_admit_dt']
actual_dc     = df['tum_actual_discharge_dt']
auth_dc       = df['auth_actual_discharge_dt']
auth_load     = df['auth_actual_discharge_load_dt']
pred          = df['pred_discharge_dt']
first_scored  = df['first_scored_dt']

# ---------------------------------------------------------
# 1. Lag-based atomic buckets (no admit logic here)
# ---------------------------------------------------------
BUCKETS_LAG = [
    "Early >5 before DC",
    "Early 4–5 before DC",
    "Early 1–3 before DC",
    "On discharge date",
    "Timely 0–4 days",
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]

EARLY_BUCKETS = [
    "Early >5 before DC",
    "Early 4–5 before DC",
    "Early 1–3 before DC",
]

GOOD_BUCKETS = [
    "On discharge date",
    "Timely 0–4 days",
]

LATE_BUCKETS = [
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]


def lag_bucket(lag):
    """Return lag-based bucket label."""
    if pd.isna(lag):
        return None

    if lag < -5:
        return "Early >5 before DC"
    elif -5 <= lag < -3:
        return "Early 4–5 before DC"
    elif -3 <= lag < 0:
        return "Early 1–3 before DC"
    elif lag == 0:
        return "On discharge date"
    elif 0 < lag <= 4:
        return "Timely 0–4 days"
    elif 5 <= lag <= 7:
        return "Late 5–7"
    elif 8 <= lag <= 10:
        return "Late 8–10"
    elif lag > 10:
        return "Late >10"
    return None


# ---------------------------------------------------------
# 2. Simulation engine: return scoring_dt + lag vs DC/ADMIT
# ---------------------------------------------------------
def simulate_scoring_full(shift_days: int):
    """
    Shift predicted DC by shift_days and determine simulated scoring date:
      - If auth_actual_discharge_dt loaded on/before shifted pred DC -> use auth DC
      - Else use shifted pred DC
      - But scoring can never be before first_scored_dt
    Returns:
      sim_dt (Series), lag_vs_dc (Series), lag_vs_admit (Series)
    """
    pred_shifted = pred + pd.to_timedelta(shift_days, unit='D')

    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]

    sim_final = sim_base.copy()
    mask_late_start = first_scored.notna() & (first_scored > sim_base)
    sim_final[mask_late_start] = first_scored[mask_late_start]

    lag_vs_dc   = (sim_final - actual_dc).dt.days
    lag_vs_adm  = (sim_final - actual_admit).dt.days

    return sim_final, lag_vs_dc, lag_vs_adm


# ---------------------------------------------------------
# 3. Build one summary row given scoring_dt + lag_vs_dc
# ---------------------------------------------------------
def build_summary_row(label, scoring_dt: pd.Series, lag_vs_dc: pd.Series):
    """
    Build summary metrics for a given scenario:
      - label: 'CURRENT' or shift integer
      - scoring_dt: Series of scoring dates for that scenario
      - lag_vs_dc: Series of lag days (scoring_dt - actual_dc)
    Returns: dict for one row.
    """
    # ---- atomic lag-based buckets ----
    buckets = lag_vs_dc.apply(lag_bucket)

    bucket_frac = buckets.value_counts(normalize=True)  # 0–1 scale

    row = {
        'shift': label,
        # RAP capture: scored within 4 days of discharge (lag <= 4)
        'capture_rate': (lag_vs_dc <= 4).mean(),
        # Early / Good / Late derived entirely from lag buckets
        'early_frac':  0.0,
        'good_0_4d_frac': 0.0,
        'late_frac':   0.0,
    }

    # Fill atomic bucket columns
    for b in BUCKETS_LAG:
        row[b] = float(bucket_frac.get(b, 0.0))

    # Aggregate to early/good/late
    row['early_frac']     = sum(row[b] for b in EARLY_BUCKETS)
    row['good_0_4d_frac'] = sum(row[b] for b in GOOD_BUCKETS)
    row['late_frac']      = sum(row[b] for b in LATE_BUCKETS)

    # Bucket sum sanity check
    row['bucket_sum'] = sum(row[b] for b in BUCKETS_LAG)

    # ---- extra info: early ON / BEFORE admit (separate metric) ----
    early_before_admit_mask = (scoring_dt <= actual_admit)
    row['early_before_admit_frac'] = early_before_admit_mask.mean()

    return row


# ---------------------------------------------------------
# 4. Build FULL SHIFT SUMMARY TABLE (CURRENT + -5..+5)
# ---------------------------------------------------------
rows = []

# CURRENT: use actual first_scored_dt
lag_current = (first_scored - actual_dc).dt.days
rows.append(build_summary_row("CURRENT", first_scored, lag_current))

# SHIFTS -5 .. +5
for shift in range(-5, 6):
    sim_dt, lag_sim, _ = simulate_scoring_full(shift)
    rows.append(build_summary_row(shift, sim_dt, lag_sim))

results_df = pd.DataFrame(rows)

print("===== SHIFT SUMMARY TABLE (0–1 scale, Excel-friendly) =====")
display(results_df)


















import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 0. Ensure datetimes
# ---------------------------------------------------------
for c in [
    'actual_admit_dt',
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_admit  = df['actual_admit_dt']
actual_dc     = df['tum_actual_discharge_dt']
auth_dc       = df['auth_actual_discharge_dt']
auth_load     = df['auth_actual_discharge_load_dt']
pred          = df['pred_discharge_dt']
first_scored  = df['first_scored_dt']

# ---------------------------------------------------------
# 1. Bucket definitions
# ---------------------------------------------------------
BUCKETS = [
    "Early BEFORE admit",   # admit-based
    "Early >5 before DC",
    "Early 4–5 before DC",
    "Early 1–3 before DC",
    "On discharge date",
    "Timely 0–4 days",
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]

EARLY_BUCKETS = [
    "Early BEFORE admit",
    "Early >5 before DC",
    "Early 4–5 before DC",
    "Early 1–3 before DC",
]

GOOD_BUCKETS = [
    "On discharge date",
    "Timely 0–4 days",
]

LATE_BUCKETS = [
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]

def admit_bucket(days_before_admit):
    """Return admit-based bucket or None."""
    if pd.isna(days_before_admit):
        return None
    if days_before_admit <= 0:
        return "Early BEFORE admit"
    return None

def lag_bucket(lag):
    """Return lag-based bucket or 'Missing'."""
    if pd.isna(lag):
        return "Missing"

    if lag < -5:
        return "Early >5 before DC"
    elif -5 <= lag < -3:
        return "Early 4–5 before DC"
    elif -3 <= lag < 0:
        return "Early 1–3 before DC"
    elif lag == 0:
        return "On discharge date"
    elif 0 < lag <= 4:
        return "Timely 0–4 days"
    elif 5 <= lag <= 7:
        return "Late 5–7"
    elif 8 <= lag <= 10:
        return "Late 8–10"
    elif lag > 10:
        return "Late >10"

    return "Missing"

def assign_bucket(lag, days_before_admit):
    """Admit bucket wins; else lag bucket."""
    b_adm = admit_bucket(days_before_admit)
    if b_adm is not None:
        return b_adm
    return lag_bucket(lag)

# ---------------------------------------------------------
# 2. Simulation engine (no bucket logic here)
# ---------------------------------------------------------
def simulate_scoring(shift_days: int):
    pred_shifted = pred + pd.to_timedelta(shift_days, unit='D')

    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]

    sim_final = sim_base.copy()
    mask_late_start = first_scored.notna() & (first_scored > sim_base)
    sim_final[mask_late_start] = first_scored[mask_late_start]

    lag_vs_dc  = (sim_final - actual_dc).dt.days
    lag_vs_adm = (sim_final - actual_admit).dt.days

    return lag_vs_dc, lag_vs_adm

# ---------------------------------------------------------
# 3. Build results table: CURRENT + shifts -5..+5
# ---------------------------------------------------------
rows = []

def build_row(label, lag_dc, lag_adm, bucket_col_name):
    """
    Helper to compute bucket fractions and summary metrics
    from lag + days_before_admit.
    """
    df[bucket_col_name] = [
        assign_bucket(l, la) for l, la in zip(lag_dc, lag_adm)
    ]

    bucket_frac = df[bucket_col_name].value_counts(normalize=True)  # 0–1

    row = {
        'shift': label,
        'capture_rate': (lag_dc <= 4).mean(),  # identification window
    }

    # Fill atomic bucket columns
    for b in BUCKETS:
        row[b] = float(bucket_frac.get(b, 0.0))

    # Derive early / good / late directly FROM buckets
    row['early_frac']      = sum(row[b] for b in EARLY_BUCKETS)
    row['good_0_4d_frac']  = sum(row[b] for b in GOOD_BUCKETS)
    row['late_frac']       = sum(row[b] for b in LATE_BUCKETS)

    # Sanity: all buckets partition the population
    row['bucket_sum'] = sum(row[b] for b in BUCKETS)

    return row

# CURRENT
lag_cur   = (first_scored - actual_dc).dt.days
lag_adm_c = (first_scored - actual_admit).dt.days
rows.append(build_row("CURRENT", lag_cur, lag_adm_c, 'bucket_cur'))

# SHIFTS -5 .. +5
for shift in range(-5, 6):
    lag_sim, lag_adm_sim = simulate_scoring(shift)
    rows.append(build_row(shift, lag_sim, lag_adm_sim, 'bucket_sim'))

# ---------------------------------------------------------
# 4. Final DataFrame (0–1 scale, Excel-friendly)
# ---------------------------------------------------------
results_df = pd.DataFrame(rows)

print("===== CHECK: bucket_sum, early/good/late consistency =====")
display(results_df[['shift', 'bucket_sum', 'early_frac', 'good_0_4d_frac', 'late_frac']])

print("===== FULL RESULTS =====")
display(results_df)












import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 0. Ensure datetimes
# ---------------------------------------------------------
for c in [
    'actual_admit_dt',
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_admit  = df['actual_admit_dt']
actual_dc     = df['tum_actual_discharge_dt']
auth_dc       = df['auth_actual_discharge_dt']
auth_load     = df['auth_actual_discharge_load_dt']
pred          = df['pred_discharge_dt']
first_scored  = df['first_scored_dt']

# ---------------------------------------------------------
# 1. Bucket definitions
# ---------------------------------------------------------
BUCKETS = [
    "Early BEFORE admit",   # admit-based
    "Early >5 before DC",   # all others are lag-based
    "Early 4–5 before DC",
    "Early 1–3 before DC",
    "On discharge date",
    "Timely 0–4 days",
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]

def admit_bucket(days_before_admit):
    """
    days_before_admit = scoring_dt - admit_dt
    Return admit-based bucket label, or None if not early-before-admit.
    """
    if pd.isna(days_before_admit):
        return None
    if days_before_admit <= 0:
        return "Early BEFORE admit"
    return None


def lag_bucket(lag):
    """
    lag = scoring_dt - discharge_dt (days)
    Return lag-based bucket label, or 'Missing'.
    """
    if pd.isna(lag):
        return "Missing"

    # Early before discharge
    if lag < -5:
        return "Early >5 before DC"
    elif -5 <= lag < -3:
        return "Early 4–5 before DC"
    elif -3 <= lag < 0:
        return "Early 1–3 before DC"

    # On discharge
    if lag == 0:
        return "On discharge date"

    # Timely window
    if 0 < lag <= 4:
        return "Timely 0–4 days"

    # Late windows
    if 5 <= lag <= 7:
        return "Late 5–7"
    elif 8 <= lag <= 10:
        return "Late 8–10"
    elif lag > 10:
        return "Late >10"

    return "Missing"


def assign_bucket(lag, days_before_admit):
    """
    Combine admit bucket + lag bucket.
    Admit logic wins; else fall back to lag-based bucket.
    """
    b_adm = admit_bucket(days_before_admit)
    if b_adm is not None:
        return b_adm
    return lag_bucket(lag)


# ---------------------------------------------------------
# 2. Simulation engine (no bucket logic here)
# ---------------------------------------------------------
def simulate_scoring(shift_days: int):
    """
    Simulated scoring date logic:
      - shift predicted DC by shift_days
      - if auth DC is loaded on/before shifted pred DC -> use auth DC
      - else use shifted pred DC
      - but never earlier than first_scored_dt
    Returns (lag_vs_dc, lag_vs_admit) as Series.
    """
    pred_shifted = pred + pd.to_timedelta(shift_days, unit='D')

    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]

    # respect first_scored_dt
    sim_final = sim_base.copy()
    mask_late_start = first_scored.notna() & (first_scored > sim_base)
    sim_final[mask_late_start] = first_scored[mask_late_start]

    lag_vs_dc  = (sim_final - actual_dc).dt.days
    lag_vs_adm = (sim_final - actual_admit).dt.days

    return lag_vs_dc, lag_vs_adm


# ---------------------------------------------------------
# 3. Build results table: CURRENT + shifts -5..+5
# ---------------------------------------------------------
rows = []

# ---------- CURRENT SCORING ROW ----------------------------------------
lag_cur   = (first_scored - actual_dc).dt.days
lag_adm_c = (first_scored - actual_admit).dt.days

df['bucket_cur'] = [
    assign_bucket(l, la) for l, la in zip(lag_cur, lag_adm_c)
]

bucket_frac_cur = df['bucket_cur'].value_counts(normalize=True)  # 0–1

row_cur = {
    'shift': 'CURRENT',
    'capture_rate': (lag_cur <= 4).mean(),                 # 0–1
    'early_frac': (lag_cur < 0).mean(),
    'good_0_4d_frac': ((lag_cur >= 0) & (lag_cur <= 4)).mean(),
    'late_frac': (lag_cur > 4).mean(),
}

for b in BUCKETS:
    row_cur[b] = float(bucket_frac_cur.get(b, 0.0))

row_cur['bucket_sum'] = sum(row_cur[b] for b in BUCKETS)
row_cur['good_from_buckets'] = row_cur["On discharge date"] + row_cur["Timely 0–4 days"]

rows.append(row_cur)

# ---------- SHIFTED SCENARIOS ------------------------------------------
for shift in range(-5, 6):   # -5, -4, ..., 0, ..., +5
    lag_sim, lag_adm_sim = simulate_scoring(shift)

    df['bucket_sim'] = [
        assign_bucket(l, la) for l, la in zip(lag_sim, lag_adm_sim)
    ]

    bucket_frac_sim = df['bucket_sim'].value_counts(normalize=True)

    row = {
        'shift': shift,
        'capture_rate': (lag_sim <= 4).mean(),
        'early_frac': (lag_sim < 0).mean(),
        'good_0_4d_frac': ((lag_sim >= 0) & (lag_sim <= 4)).mean(),
        'late_frac': (lag_sim > 4).mean(),
    }

    for b in BUCKETS:
        row[b] = float(bucket_frac_sim.get(b, 0.0))

    row['bucket_sum'] = sum(row[b] for b in BUCKETS)
    row['good_from_buckets'] = row["On discharge date"] + row["Timely 0–4 days"]

    rows.append(row)

# ---------------------------------------------------------
# 4. Final DataFrame (0–1 scale, Excel-friendly)
# ---------------------------------------------------------
results_df = pd.DataFrame(rows)

print("===== CHECKS =====")
print("Bucket sums (should be ~1.0 each):")
display(results_df[['shift', 'bucket_sum']])

print("good_0_4d_frac vs On+Timely (should be very close):")
display(results_df[['shift', 'good_0_4d_frac', 'good_from_buckets']])

print("===== FULL RESULTS =====")
display(results_df)
















import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 0. Ensure datetimes
# ---------------------------------------------------------
for c in [
    'actual_admit_dt',
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_admit  = df['actual_admit_dt']
actual_dc     = df['tum_actual_discharge_dt']
auth_dc       = df['auth_actual_discharge_dt']
auth_load     = df['auth_actual_discharge_load_dt']
pred          = df['pred_discharge_dt']
first_scored  = df['first_scored_dt']

# ---------------------------------------------------------
# 1. Atomic timing buckets
# ---------------------------------------------------------
BUCKETS = [
    "Early BEFORE admit",
    "Early >5 before DC",
    "Early 4–5 before DC",
    "Early 1–3 before DC",
    "On discharge date",
    "Timely 0–4 days",
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]

def timing_bucket(lag, days_before_admit):
    # days_before_admit = scoring_dt - admit_dt
    if pd.notna(days_before_admit) and days_before_admit <= 0:
        return "Early BEFORE admit"

    if pd.isna(lag):
        return "Missing"

    # lag = scoring_dt - discharge_dt
    if lag < -5:
        return "Early >5 before DC"
    elif -5 <= lag < -3:
        return "Early 4–5 before DC"
    elif -3 <= lag <= -1:
        return "Early 1–3 before DC"
    elif lag == 0:
        return "On discharge date"
    elif 0 < lag <= 4:
        return "Timely 0–4 days"
    elif 5 <= lag <= 7:
        return "Late 5–7"
    elif 8 <= lag <= 10:
        return "Late 8–10"
    elif lag > 10:
        return "Late >10"

    return "Missing"


# ---------------------------------------------------------
# 2. Simulation engine for any shift
# ---------------------------------------------------------
def simulate_scoring(shift_days: int):
    """
    Simulated scoring date logic:
      - shift predicted DC by shift_days
      - if auth DC is loaded on/before shifted pred DC -> use auth DC
      - else use shifted pred DC
      - but never earlier than first_scored_dt
    Returns (lag_vs_dc, lag_vs_admit).
    """
    pred_shifted = pred + pd.to_timedelta(shift_days, unit='D')

    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]

    sim_final = sim_base.copy()
    mask_late_start = first_scored.notna() & (first_scored > sim_base)
    sim_final[mask_late_start] = first_scored[mask_late_start]

    lag_vs_dc  = (sim_final - actual_dc).dt.days
    lag_vs_adm = (sim_final - actual_admit).dt.days

    return lag_vs_dc, lag_vs_adm


# ---------------------------------------------------------
# 3. Build results table: CURRENT + shifts -5..+5
# ---------------------------------------------------------
rows = []

# ---------- CURRENT SCORING ROW ----------------------------------------
lag_cur   = (first_scored - actual_dc).dt.days
lag_adm_c = (first_scored - actual_admit).dt.days

df['bucket_cur'] = [
    timing_bucket(l, la) for l, la in zip(lag_cur, lag_adm_c)
]

# value_counts(normalize=True) already gives 0–1 fractions
bucket_frac_cur = df['bucket_cur'].value_counts(normalize=True)

row_cur = {
    'shift': 'CURRENT',
    'capture_rate': (lag_cur <= 4).mean(),                 # 0–1
    'early_frac': (lag_cur < 0).mean(),                    # 0–1
    'good_0_4d_frac': ((lag_cur >= 0) & (lag_cur <= 4)).mean(),
    'late_frac': (lag_cur > 4).mean(),
}

for b in BUCKETS:
    row_cur[b] = float(bucket_frac_cur.get(b, 0.0))

row_cur['bucket_sum'] = sum(row_cur[b] for b in BUCKETS)

rows.append(row_cur)

# ---------- SHIFTED SCENARIOS ------------------------------------------
for shift in range(-5, 6):   # -5, -4, ..., 0, ..., +5
    lag_sim, lag_adm_sim = simulate_scoring(shift)

    df['bucket_sim'] = [
        timing_bucket(l, la) for l, la in zip(lag_sim, lag_adm_sim)
    ]

    bucket_frac_sim = df['bucket_sim'].value_counts(normalize=True)

    row = {
        'shift': shift,
        'capture_rate': (lag_sim <= 4).mean(),
        'early_frac': (lag_sim < 0).mean(),
        'good_0_4d_frac': ((lag_sim >= 0) & (lag_sim <= 4)).mean(),
        'late_frac': (lag_sim > 4).mean(),
    }

    for b in BUCKETS:
        row[b] = float(bucket_frac_sim.get(b, 0.0))

    row['bucket_sum'] = sum(row[b] for b in BUCKETS)

    rows.append(row)

# ---------------------------------------------------------
# 4. Final DataFrame (Excel-friendly: all fractions 0–1)
# ---------------------------------------------------------
results_df = pd.DataFrame(rows)

print("===== CHECK BUCKET SUMS (should all be ~1.0) =====")
display(results_df[['shift', 'bucket_sum']])

print("===== FULL RESULTS (0–1 scale, ready for % formatting in Excel) =====")
display(results_df)
















import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 0. Ensure datetimes
# ---------------------------------------------------------
for c in [
    'actual_admit_dt',
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_admit  = df['actual_admit_dt']
actual_dc     = df['tum_actual_discharge_dt']
auth_dc       = df['auth_actual_discharge_dt']
auth_load     = df['auth_actual_discharge_load_dt']
pred          = df['pred_discharge_dt']
first_scored  = df['first_scored_dt']

# ---------------------------------------------------------
# 1. Timing Bucket Function
# ---------------------------------------------------------
def timing_bucket(lag, days_before_admit):
    if pd.notna(days_before_admit) and days_before_admit <= 0:
        return "Early BEFORE admit"
    if pd.isna(lag):
        return "Missing"

    if lag < -5:
        return "Early >5 before DC"
    elif -5 <= lag < -3:
        return "Early 4–5 before DC"
    elif -3 <= lag < -1:
        return "Early 1–3 before DC"
    elif lag == 0:
        return "On discharge date"
    elif 0 < lag <= 4:
        return "Timely 0–4 days"
    elif 5 <= lag <= 7:
        return "Late 5–7"
    elif 8 <= lag <= 10:
        return "Late 8–10"
    elif lag > 10:
        return "Late >10"
    return "Other"


# ---------------------------------------------------------
# 2. Simulation engine for any shift
# ---------------------------------------------------------
def simulate_scoring(shift_days):

    pred_shifted = pred + pd.to_timedelta(shift_days, unit='D')

    # Choose early discharge signal
    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]

    # Respect first_scored_dt
    sim_final = sim_base.copy()
    late_mask = (first_scored.notna()) & (first_scored > sim_base)
    sim_final[late_mask] = first_scored[late_mask]

    lag = (sim_final - actual_dc).dt.days
    lag_adm = (sim_final - actual_admit).dt.days

    return lag, lag_adm


# ---------------------------------------------------------
# 3. Build table: CURRENT first + shifts –5..+5
# ---------------------------------------------------------
rows = []

# ---------- CURRENT -----------------------------------------------------
lag_cur = (first_scored - actual_dc).dt.days
lag_adm_cur = (first_scored - actual_admit).dt.days

df['bucket'] = [timing_bucket(l, la) for l, la in zip(lag_cur, lag_adm_cur)]
bucket_counts = df['bucket'].value_counts(normalize=True).mul(100)

# Prepare row
row = {
    'shift': 'CURRENT',
    'capture_rate_pct': (lag_cur <= 4).mean() * 100,
    'early_pct': (lag_cur < 0).mean() * 100,
    'good_0_4d_pct': ((lag_cur >= 0) & (lag_cur <= 4)).mean() * 100,
    'late_pct': (lag_cur > 4).mean() * 100
}

# Add bucket columns
for bucket in [
    "Early BEFORE admit",
    "Early >5 before DC",
    "Early 4–5 before DC",
    "Early 1–3 before DC",
    "On discharge date",
    "Timely 0–4 days",
    "Late 5–7",
    "Late 8–10",
    "Late >10",
]:
    row[bucket] = bucket_counts.get(bucket, 0)

rows.append(row)


# ---------- SHIFTS –5..+5 ---------------------------------------------
for shift in range(-5, 6):

    lag_sim, lag_adm_sim = simulate_scoring(shift)

    df['bucket_sim'] = [
        timing_bucket(l, la) for l, la in zip(lag_sim, lag_adm_sim)
    ]

    bucket_counts = df['bucket_sim'].value_counts(normalize=True).mul(100)

    row = {
        'shift': shift,
        'capture_rate_pct': (lag_sim <= 4).mean() * 100,
        'early_pct': (lag_sim < 0).mean() * 100,
        'good_0_4d_pct': ((lag_sim >= 0) & (lag_sim <= 4)).mean() * 100,
        'late_pct': (lag_sim > 4).mean() * 100
    }
    
    # Add bucket columns
    for bucket in [
        "Early BEFORE admit",
        "Early >5 before DC",
        "Early 4–5 before DC",
        "Early 1–3 before DC",
        "On discharge date",
        "Timely 0–4 days",
        "Late 5–7",
        "Late 8–10",
        "Late >10",
    ]:
        row[bucket] = bucket_counts.get(bucket, 0)

    rows.append(row)


# ---------------------------------------------------------
# 4. Final DataFrame
# ---------------------------------------------------------
results_df = pd.DataFrame(rows)

print("===== FINAL SHIFT SIMULATION TABLE (CURRENT + SHIFTS –5 TO +5) =====")
display(results_df)

















import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 0. Ensure datetimes
# ---------------------------------------------------------
for c in [
    'actual_admit_dt',
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_admit  = df['actual_admit_dt']
actual_dc     = df['tum_actual_discharge_dt']
auth_dc       = df['auth_actual_discharge_dt']
auth_load     = df['auth_actual_discharge_load_dt']
pred          = df['pred_discharge_dt']
first_scored  = df['first_scored_dt']

# ---------------------------------------------------------
# 1. CURRENT scoring lag
# ---------------------------------------------------------
df['lag_current'] = (first_scored - actual_dc).dt.days
df['days_before_admit_current'] = (first_scored - actual_admit).dt.days

# ---------------------------------------------------------
# 2. SIMULATED scoring (shift = 0 for baseline)
#    Use earlier of predicted vs auth discharge (only if auth loaded by then)
#    But never before first_scored_dt
# ---------------------------------------------------------

def simulate_scoring(pred_shift_days):
    pred_shifted = pred + pd.to_timedelta(pred_shift_days, unit='D')

    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    # Base scoring dt from earliest discharge signal
    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]

    # Respect first_scored_dt
    sim_final = sim_base.copy()
    mask = (first_scored.notna()) & (first_scored > sim_base)
    sim_final[mask] = first_scored[mask]

    return sim_final

sim_dt = simulate_scoring(0)   # no shift baseline

df['lag_sim'] = (sim_dt - actual_dc).dt.days
df['days_before_admit_sim'] = (sim_dt - actual_admit).dt.days

# ---------------------------------------------------------
# 3. COMPLETE BUCKET LOGIC (with before-admit check)
# ---------------------------------------------------------

def timing_bucket(lag, days_before_admit):
    # 1. EARLY BEFORE ADMIT DATE
    if pd.notna(days_before_admit) and days_before_admit <= 0:
        return "Early BEFORE admit date"
    
    # If lag missing
    if pd.isna(lag):
        return "Missing"

    # 2. EARLY BEFORE DISCHARGE
    if lag < -5:
        return "Early >5 days before discharge"
    elif -5 <= lag < -3:
        return "Early 4–5 days before discharge"
    elif -3 <= lag < -1:
        return "Early 1–3 days before discharge"
    elif lag == 0:
        return "On discharge date"

    # 3. GOOD window (RAP opportunity)
    elif 0 < lag <= 4:
        return "Timely (0–4 days after discharge)"

    # 4. LATE buckets
    elif 5 <= lag <= 7:
        return "Late 5–7 days"
    elif 8 <= lag <= 10:
        return "Late 8–10 days"
    elif lag > 10:
        return "Late >10 days"

    return "Other"


df['current_bucket'] = df.apply(
    lambda r: timing_bucket(r['lag_current'], r['days_before_admit_current']),
    axis=1
)

df['sim_bucket'] = df.apply(
    lambda r: timing_bucket(r['lag_sim'], r['days_before_admit_sim']),
    axis=1
)

# ---------------------------------------------------------
# 4. Summary distributions
# ---------------------------------------------------------

current_dist = df['current_bucket'].value_counts(normalize=True).mul(100).round(2)
sim_dist     = df['sim_bucket'].value_counts(normalize=True).mul(100).round(2)

print("======== CURRENT SCORING TIMING ========")
display(current_dist)

print("\n======== SIMULATED SCORING TIMING ========")
display(sim_dist)
















import pandas as pd
import numpy as np

# --------------------------------------------------------------------
# 0. Ensure datetime conversion
# --------------------------------------------------------------------
for c in [
    'tum_actual_discharge_dt',
    'auth_actual_discharge_dt',
    'auth_actual_discharge_load_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual      = df['tum_actual_discharge_dt']
auth_dc     = df['auth_actual_discharge_dt']
auth_load   = df['auth_actual_discharge_load_dt']
pred        = df['pred_discharge_dt']
first_scored = df['first_scored_dt']

# --------------------------------------------------------------------
# 1. CURRENT SCORING: lag_current = first_scored_dt - actual_discharge
# --------------------------------------------------------------------
df['lag_current'] = (first_scored - actual).dt.days

# --------------------------------------------------------------------
# 2. SIMULATED SCORING USING RULE:
#    (If auth discharge is loaded before predicted, use auth actual dc;
#     else use predicted. But NEVER earlier than first_scored_dt)
# --------------------------------------------------------------------

def simulate_scoring(pred_shift_days):
    pred_shifted = pred + pd.to_timedelta(pred_shift_days, unit='D')

    use_auth = (
        auth_dc.notna() &
        auth_load.notna() &
        (auth_load <= pred_shifted)
    )

    # base scoring date = either auth actual discharge OR shifted predicted discharge
    sim_base = pd.Series(pd.NaT, index=df.index)
    sim_base[use_auth]  = auth_dc[use_auth]
    sim_base[~use_auth] = pred_shifted[~use_auth]
    
    # respect first scoring (cannot go earlier)
    final_sim = sim_base.copy()
    mask = (first_scored.notna()) & (first_scored > sim_base)
    final_sim[mask] = first_scored[mask]
    
    return (final_sim - actual).dt.days  # lag in days


df['lag_sim_0'] = simulate_scoring(0)   # no shift case

# --------------------------------------------------------------------
# 3. Define EARLY and LATE granular buckets
# --------------------------------------------------------------------

def timing_bucket(lag):
    if pd.isna(lag):
        return "Missing"
    
    # EARLY buckets (<0)
    if lag < -5:
        return "Early >5 days before discharge"
    elif -5 <= lag < -3:
        return "Early 4–5 days before discharge"
    elif -3 <= lag < -1:
        return "Early 1–3 days before discharge"
    elif lag == 0:
        return "On the discharge date"
    
    # ON-TIME window (0–4)
    elif 0 < lag <= 4:
        return "Timely (0–4 days)"
    
    # LATE buckets (>4)
    elif 5 <= lag <= 7:
        return "Late 5–7 days"
    elif 8 <= lag <= 10:
        return "Late 8–10 days"
    elif lag > 10:
        return "Late >10 days"
    
    return "Other"

# --------------------------------------------------------------------
# 4. Apply buckets for CURRENT and SIMULATED scoring
# --------------------------------------------------------------------
df['current_bucket']  = df['lag_current'].apply(timing_bucket)
df['sim_bucket']      = df['lag_sim_0'].apply(timing_bucket)

# --------------------------------------------------------------------
# 5. Summary distribution tables
# --------------------------------------------------------------------
current_dist = df['current_bucket'].value_counts(normalize=True).mul(100).round(2)
sim_dist     = df['sim_bucket'].value_counts(normalize=True).mul(100).round(2)

print("====== CURRENT SCORING TIMING DISTRIBUTION (%) ======")
display(current_dist)

print("\n====== SIMULATED SCORING TIMING DISTRIBUTION (%) ======")
display(sim_dist)














mimport pandas as pd

# ensure datetime types
df['first_scored_dt'] = pd.to_datetime(df['first_scored_dt'], errors='coerce')
df['tum_actual_discharge_dt'] = pd.to_datetime(df['tum_actual_discharge_dt'], errors='coerce')

# lag in days between scoring and REAL discharge
df['lag_current'] = (df['first_scored_dt'] - df['tum_actual_discharge_dt']).dt.days

# capture rate: scored within 4 days since discharge
current_capture_rate = (df['lag_current'] <= 4).mean() * 100

# timing distribution
current_early = (df['lag_current'] < 0).mean() * 100
current_good  = ((df['lag_current'] >= 0) & (df['lag_current'] <= 4)).mean() * 100
current_late  = (df['lag_current'] > 4).mean() * 100

print("===== CURRENT CAPTURE PERFORMANCE =====")
print(f"Current Capture Rate (<=4 days): {current_capture_rate:.2f}%")
print(f"Early Sending (<0 days):         {current_early:.2f}%")
print(f"Good Window (0–4 days):          {current_good:.2f}%")
print(f"Late Sending (>4 days):          {current_late:.2f}%")







import pandas as pd
import numpy as np

# Make sure datetime types are correct
for c in [
    'tum_actual_discharge_dt',      # ground truth actual discharge date
    'pred_discharge_dt',            # predicted discharge date (LOS-based)
    'auth_actual_discharge_dt',     # actual discharge date from auth feed
    'auth_actual_discharge_load_dt',# date when auth_actual_discharge_dt was loaded
    'first_scored_dt'               # first time the member was ever scored in current pipeline
]:
    df[c] = pd.to_datetime(df[c], errors='coerce')

actual_truth = df['tum_actual_discharge_dt']
pred         = df['pred_discharge_dt']
auth_dc      = df['auth_actual_discharge_dt']
auth_dc_load = df['auth_actual_discharge_load_dt']
first_scored = df['first_scored_dt']

# Shifts to test
shifts = [-3, -2, -1, 0, 1, 2, 3]

results = []

for s in shifts:
    # 1) Shift predicted discharge date
    pred_shifted = pred + pd.to_timedelta(s, unit='D')
    
    # 2) Decide which discharge signal we would use as the *base* scoring date:
    #    If auth actual discharge date is loaded on/before shifted predicted discharge date,
    #    then use auth_actual_discharge_dt; else use shifted predicted discharge date.
    use_auth = (
        auth_dc.notna() &
        auth_dc_load.notna() &
        (auth_dc_load <= pred_shifted)
    )
    
    sim_base_dt = pd.Series(pd.NaT, index=df.index)
    sim_base_dt[use_auth]  = auth_dc[use_auth]
    sim_base_dt[~use_auth] = pred_shifted[~use_auth]
    
    # 3) Respect first_scored_dt: cannot score before we ever started scoring
    #    Final simulated scoring date = max(sim_base_dt, first_scored_dt)
    sim_scoring_dt = sim_base_dt.copy()
    mask_late_start = first_scored.notna() & (first_scored > sim_base_dt)
    sim_scoring_dt[mask_late_start] = first_scored[mask_late_start]
    
    # 4) Compute lag vs true discharge (x-axis of your graph)
    lag = (sim_scoring_dt - actual_truth).dt.days
    
    # 5) Buckets: early / good / late
    early = (lag < 0).mean() * 100
    good  = ((lag >= 0) & (lag <= 4)).mean() * 100   # RAP opportunity window
    late  = (lag > 4).mean() * 100                   # lost opportunity
    
    capture = (lag <= 4).mean() * 100                # cases still within 4 days of discharge
    
    results.append([s, capture, early, good, late])

results_df = pd.DataFrame(
    results,
    columns=['shift_days', 'capture_rate_pct', 'early_pct', 'good_0_4d_pct', 'late_gt4d_pct']
)

print("===== SHIFT OPTIMIZATION RESULTS (USING AUTH OR PRED DATES + FIRST_SCORED_DT) =====")
display(results_df)

















import pandas as pd
import numpy as np

# -------------------------------------------------------------
# 0. ENSURE DATETIME TYPES (critical!)
# -------------------------------------------------------------
date_cols = [
    'tum_actual_discharge_dt',
    'pred_discharge_dt',
    'first_scored_dt'
]

for c in date_cols:
    df[c] = pd.to_datetime(df[c], errors='coerce')   # converts string → datetime safely

# -------------------------------------------------------------
# 1. DEFINE SERIES (now all are datetimes)
# -------------------------------------------------------------
actual = df['tum_actual_discharge_dt']
pred   = df['pred_discharge_dt']
first_scored = df['first_scored_dt']

# -------------------------------------------------------------
# 2. Compute lag between predicted vs actual discharge
# -------------------------------------------------------------
df['lag_vs_actual'] = (pred - actual).dt.days

# <0 = scoring would happen BEFORE actual discharge
# =0 = ON discharge day
# >0 = AFTER discharge

# -------------------------------------------------------------
# 3. Compute delay vs CURRENT scoring process
# -------------------------------------------------------------
df['delay_vs_current'] = (pred - first_scored).dt.days

# +ve = predicted discharge scoring is LATER than current
# -ve = predicted discharge scoring is EARLIER

# -------------------------------------------------------------
# 4. Summary statistics
# -------------------------------------------------------------
avg_delay_actual   = df['lag_vs_actual'].mean()
median_delay_actual = df['lag_vs_actual'].median()

pct_before = (df['lag_vs_actual'] < 0).mean() * 100
pct_on     = (df['lag_vs_actual'] == 0).mean() * 100
pct_after  = (df['lag_vs_actual'] > 0).mean() * 100

avg_delay_current   = df['delay_vs_current'].mean()
median_delay_current = df['delay_vs_current'].median()

# -------------------------------------------------------------
# 5. Lag distribution table (like your Excel screenshot)
# -------------------------------------------------------------
lag_dist = (
    df['lag_vs_actual']
      .value_counts()
      .sort_index()
      .reset_index()
)

lag_dist.columns = ['lag_days', 'count']
lag_dist['percent'] = (lag_dist['count'] / lag_dist['count'].sum() * 100).round(2)
lag_dist['cum_percent'] = lag_dist['percent'].cumsum().round(2)

# -------------------------------------------------------------
# 6. PRINT FINAL MANAGER SUMMARY
# -------------------------------------------------------------
print("===== SCORING IMPACT IF WE SCORE ON PREDICTED DISCHARGE DATE =====\n")

print(f"Average lag vs actual discharge : {avg_delay_actual:.2f} days")
print(f"Median lag vs actual discharge  : {median_delay_actual:.2f} days\n")

print(f"% Scored BEFORE actual discharge: {pct_before:.2f}%")
print(f"% Scored ON discharge day       : {pct_on:.2f}%")
print(f"% Scored AFTER discharge        : {pct_after:.2f}%\n")

print(f"Average delay vs current scoring: {avg_delay_current:.2f} days")
print(f"Median delay vs current scoring : {median_delay_current:.2f} days\n")

print("===== LAG DISTRIBUTION TABLE =====")
display(lag_dist)






import pandas as pd
import numpy as np

# -------------------------------------------------------------
# 1. DEFINE COLUMNS (rename these to match your exact dataframe)
# -------------------------------------------------------------
actual = df['tum_actual_discharge_dt']
pred = df['pred_discharge_dt']
first_scored = df['first_scored_dt']

# -------------------------------------------------------------
# 2. Compute lag between PREDICTED discharge and ACTUAL discharge
# -------------------------------------------------------------
df['lag_vs_actual'] = (pred - actual).dt.days

# Interpretation:
#   < 0 = scoring would happen BEFORE actual discharge
#   = 0 = scoring ON discharge day
#   > 0 = scoring AFTER discharge (late)

# -------------------------------------------------------------
# 3. Compute delay vs CURRENT scoring process
# -------------------------------------------------------------
df['delay_vs_current'] = (pred - first_scored).dt.days
# +ve = predicted discharge scoring is LATER
# -ve = predicted discharge scoring is EARLIER

# -------------------------------------------------------------
# 4. Summary statistics (overall)
# -------------------------------------------------------------
avg_delay_actual = df['lag_vs_actual'].mean()
median_delay_actual = df['lag_vs_actual'].median()

pct_before = (df['lag_vs_actual'] < 0).mean() * 100
pct_on     = (df['lag_vs_actual'] == 0).mean() * 100
pct_after  = (df['lag_vs_actual'] > 0).mean() * 100

avg_delay_current = df['delay_vs_current'].mean()
median_delay_current = df['delay_vs_current'].median()

# -------------------------------------------------------------
# 5. Lag distribution table (like your Excel screenshot)
# -------------------------------------------------------------
lag_dist = (
    df['lag_vs_actual']
      .value_counts()
      .sort_index()
      .reset_index()
)

lag_dist.columns = ['lag_days', 'count']
lag_dist['percent'] = (lag_dist['count'] / lag_dist['count'].sum() * 100).round(2)
lag_dist['cum_percent'] = lag_dist['percent'].cumsum().round(2)

# -------------------------------------------------------------
# 6. PRINT FINAL SUMMARY (manager-ready)
# -------------------------------------------------------------
print("===== SCORING TIMING IMPACT WHEN USING PREDICTED DISCHARGE DATE =====\n")

print(f"Avg lag vs actual discharge (days): {avg_delay_actual:.2f}")
print(f"Median lag vs actual discharge (days): {median_delay_actual:.2f}\n")

print(f"% scored BEFORE actual discharge: {pct_before:.2f}%")
print(f"% scored ON actual discharge day: {pct_on:.2f}%")
print(f"% scored AFTER actual discharge: {pct_after:.2f}%\n")

print(f"Avg delay vs current scoring process: {avg_delay_current:.2f} days")
print(f"Median delay vs current scoring process: {median_delay_current:.2f} days\n")

print("===== LAG DISTRIBUTION TABLE =====")
display(lag_dist)







shifts = [-3, -2, -1, 0, 1, 2, 3]


import numpy as np
import pandas as pd

results = []

for shift in shifts:
    shifted_pred = base_pred + shift   # apply the bias correction

    # errors
    mae  = np.mean(np.abs(actual - shifted_pred))
    rmse = np.sqrt(np.mean((actual - shifted_pred) ** 2))
    bias = np.mean(actual - shifted_pred)

    results.append([shift, mae, rmse, bias])

results_df = pd.DataFrame(results, columns=['shift_days', 'MAE', 'RMSE', 'BIAS'])


results_df = results_df.sort_values('MAE')
print(results_df)

plt.plot(results_df['shift_days'], results_df['MAE'], marker='o')
plt.axhline(y=results_df.loc[results_df['shift_days']==0, 'MAE'].values[0],
            linestyle='--', color='gray')
plt.title('MAE Sensitivity to LOS Shift')
plt.xlabel('Shift Applied to Predicted LOS (days)')
plt.ylabel('MAE')
plt.grid(True)
plt.show()

















SELECT
  authorization_id,

  -- first day this auth was scored
  MIN(IF(scored = 'SCORED', req_load_dt, NULL)) AS first_scored_req_load_dt,

  -- first day a discharge date showed up
  MIN(IF(actual_discharge_dts IS NOT NULL, req_load_dt, NULL)) AS first_dc_req_load_dt,

  -- (optional) the first discharge date itself
  MIN(IF(actual_discharge_dts IS NOT NULL, actual_discharge_dts, NULL)) AS first_discharge_dt

FROM `project.dataset.your_table`
GROUP BY authorization_id;







pred_col = 'median_los_all'   # instead of 'pred_los'
df['signed_error'] = df[actual_col] - df[pred_col]
# rerun the rest of the cells unchanged

import numpy as np
import pandas as pd

# actual & predicted
actual_col = 'tum_act_los_day_cnt'
pred_col   = 'pred_los'   # change to 'median_los_all' or whatever you’re using

# signed error: +ve = under-prediction, -ve = over-prediction
df['signed_error'] = df[actual_col] - df[pred_col]

# absolute error
df['abs_error'] = df['signed_error'].abs()

# squared error
df['sq_error'] = df['signed_error'] ** 2

# label type of error
def classify_error(e, tol=0.5):
    """
    tol = tolerance in days to treat as 'about right'
    """
    if e > tol:
        return 'under_pred'   # actual > predicted
    elif e < -tol:
        return 'over_pred'    # actual < predicted
    else:
        return 'near_exact'

df['error_type'] = df['signed_error'].apply(classify_error)

mae  = df['abs_error'].mean()
rmse = np.sqrt(df['sq_error'].mean())
bias = df['signed_error'].mean()   # +ve means on avg you under-predict

error_mix = df['error_type'].value_counts(normalize=True)  # proportions

print(f"MAE  : {mae:.3f} days")
print(f"RMSE : {rmse:.3f} days")
print(f"Bias (actual - pred): {bias:.3f} days")

print("\nError mix:")
print((error_mix * 100).round(1).astype(str) + '%')


def error_by_group(df, group_cols, actual_col='tum_act_los_day_cnt', pred_col='pred_los'):
    g = df.groupby(group_cols, as_index=False).agg(
        count       = (actual_col, 'size'),
        mae         = ('abs_error', 'mean'),
        rmse        = ('sq_error', lambda x: np.sqrt(x.mean())),
        avg_pred    = (pred_col, 'mean'),
        avg_actual  = (actual_col, 'mean'),
        bias        = ('signed_error', 'mean'),
        under_rate  = ('error_type', lambda s: (s == 'under_pred').mean()),
        over_rate   = ('error_type', lambda s: (s == 'over_pred').mean()),
    )
    # convert rates to %
    g['under_rate'] = (g['under_rate'] * 100).round(1)
    g['over_rate']  = (g['over_rate']  * 100).round(1)
    return g

# by service type
err_by_srv = error_by_group(df, ['tum_stay_srv_type_cd'])
print("===== ERROR BY SERVICE TYPE =====")
print(err_by_srv.sort_values('mae'))

# by admission status
err_by_adm = error_by_group(df, ['SAAdmissionStatusType'])
print("\n===== ERROR BY ADMISSION STATUS =====")
print(err_by_adm.sort_values('mae'))












median_los_lvl1 = df.groupby(['icd_group', 'tum_stay_sry_type_cd', 'SAAdmissionStatusType'])['tum_act_los_day_cnt'].median()



# ============================================
# 0. IMPORTS
# ============================================
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sns.set(style="whitegrid")

# ============================================
# 1. BASIC PREP
# ============================================
# df = pd.read_csv("your_file.csv")   # Load here

# Create error columns
df['los_error'] = df['median_los_grp'] - df['tum_act_los_day_cnt']
df['abs_error'] = df['los_error'].abs()

print("Error fields created.")

# ============================================
# 2. OVERALL SUMMARY
# ============================================
print("\n===== GLOBAL ERROR SUMMARY =====")
display(df[['tum_act_los_day_cnt', 'median_los_grp', 'los_error', 'abs_error']].describe())

# ============================================
# 3. FUNCTION: ERROR BY CATEGORY
# ============================================
def error_by_group(col):
    print(f"\n===== ERROR BY {col} =====")
    g = df.groupby(col).agg(
        count=('auth_id','count'),
        mae=('abs_error','mean'),
        rmse=('los_error', lambda x: np.sqrt((x**2).mean())),
        avg_pred=('median_los_grp','mean'),
        avg_actual=('tum_act_los_day_cnt','mean')
    ).sort_values('mae')

    display(g.head(20))
    return g

# Run on important categorical fields
cat_fields = [
    'tum_stay_sry_type_cd',
    'SAAdmissionStatusType',
    'DischargeTo',
    'category',
    'LOBCode',
    'PrecertDecisionStatus',
    'tum_admission_type_cd',
    'tum_admit_class_cd'
]

grouped_results = {col: error_by_group(col) for col in cat_fields}

# ============================================
# 4. PLOT FUNCTIONS
# ============================================
def plot_mae(col):
    plt.figure(figsize=(12,5))
    tmp = df.groupby(col)['abs_error'].mean().sort_values()
    sns.barplot(x=tmp.index, y=tmp.values)
    plt.xticks(rotation=45)
    plt.title(f"Mean Absolute Error by {col}")
    plt.ylabel("MAE")
    plt.show()


def plot_distribution():
    plt.figure(figsize=(10,5))
    sns.kdeplot(df['tum_act_los_day_cnt'], label='Actual LOS', shade=True)
    sns.kdeplot(df['median_los_grp'], label='Predicted LOS', shade=True)
    plt.title("Distribution: Actual vs Predicted LOS")
    plt.legend()
    plt.show()


def plot_error_dist():
    plt.figure(figsize=(10,5))
    sns.histplot(df['los_error'], bins=60, kde=True)
    plt.title("Error Distribution (Predicted – Actual)")
    plt.axvline(0, color='black', linestyle='--')
    plt.show()


def plot_scatter():
    plt.figure(figsize=(8,6))
    sns.scatterplot(x=df['tum_act_los_day_cnt'], y=df['median_los_grp'], alpha=0.3)
    plt.xlabel("Actual LOS")
    plt.ylabel("Predicted (Median LOS)")
    plt.title("Actual vs Predicted LOS")
    plt.show()

# ============================================
# 5. RUN PLOTS
# ============================================
plot_distribution()
plot_error_dist()
plot_scatter()

for col in cat_fields:
    plot_mae(col)

# ============================================
# 6. HIGH ERROR SEGMENTS
# ============================================
print("\n===== TOP HIGH-ERROR CASES =====")
high_error = df.nlargest(20, 'abs_error')[[
    'auth_id', 'DiagnosisCode', 'tum_stay_sry_type_cd',
    'tum_act_los_day_cnt', 'median_los_grp', 'abs_error'
]]
display(high_error)

# ============================================
# 7. ERROR BY DIAGNOSIS (OPTIONAL)
# ============================================
print("\n===== ERROR BY ICD CATEGORY =====")
dx_err = error_by_group('icd9_dx_ctg_cd').head(30)

# ============================================
# 8. SHORT-STAY VS LONG-STAY ERROR
# ============================================
df['LOS_bin'] = pd.cut(
    df['tum_act_los_day_cnt'],
    bins=[0, 2, 5, 10, 20, 999],
    labels=["0-2", "3-5", "6-10", "11-20", "20+"]
)

print("\n===== ERROR BY LOS GROUP =====")
display(error_by_group('LOS_bin'))

# ============================================
# 9. SAVE SUMMARY TABLES (OPTIONAL)
# ============================================
summary_tables = {
    col: error_by_group(col)
    for col in cat_fields + ['LOS_bin', 'icd9_dx_ctg_cd']
}

for key, table in summary_tables.items():
    table.to_csv(f"error_summary_{key}.csv")

print("All summary CSVs exported successfully.")








actual: test_df['actual_los']
predicted: test_df['predicted_los']
diagnosis group: test_df['dx_grp']


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

test_df['scored_flag'] = np.where(test_df['predicted_los'].notnull(), 1, 0)

# Overall % scored
overall_scored = test_df['scored_flag'].mean() * 100
print("Overall % Scored:", overall_scored)

# By diagnosis group
scored_by_dx = test_df.groupby('dx_grp')['scored_flag'].mean().sort_values(ascending=False) * 100
print(scored_by_dx)

plt.figure(figsize=(12,5))
scored_by_dx.plot(kind='bar')
plt.title('% Scored by Diagnosis Group')
plt.ylabel('% Scored')
plt.show()

#2
test_df['error'] = test_df['predicted_los'] - test_df['actual_los']

# Histogram
plt.figure(figsize=(10,5))
sns.histplot(test_df['error'], kde=True, bins=30)
plt.title('Error Distribution (Predicted - Actual LOS)')
plt.xlabel('Prediction Error')
plt.ylabel('Frequency')
plt.axvline(0, color='red', linestyle='--')
plt.show()

# Boxplot
plt.figure(figsize=(10,2))
sns.boxplot(x=test_df['error'])
plt.title('Error Boxplot')
plt.axvline(0, color='red', linestyle='--')
plt.show()

#3

plt.figure(figsize=(8,6))
sns.scatterplot(x=test_df['predicted_los'], y=test_df['actual_los'], alpha=0.4)
plt.plot([0, test_df['actual_los'].max()], [0, test_df['actual_los'].max()], 'r--')
plt.xlabel('Predicted LOS')
plt.ylabel('Actual LOS')
plt.title('Predicted vs Actual LOS')
plt.show()

#4
# Bucketing predicted LOS
test_df['pred_bucket'] = pd.cut(
    test_df['predicted_los'],
    bins=[0,2,4,7,999],
    labels=['0-2','2-4','4-7','7+'],
    include_lowest=True
)

calibration = test_df.groupby('pred_bucket')[['actual_los','predicted_los']].mean()

print(calibration)

calibration.plot(kind='bar', figsize=(10,5))
plt.title('Calibration Plot: Mean Actual vs Predicted by LOS Bucket')
plt.ylabel('LOS (days)')
plt.show()

#5
err_by_dx = test_df.groupby('dx_grp').agg(
    count=('actual_los', 'count'),
    mae=('error', lambda x: np.mean(np.abs(x))),
    median_error=('error', 'median'),
    pct_under=('error', lambda x: np.mean(x < 0) * 100),
    pct_over=('error', lambda x: np.mean(x > 0) * 100)
).sort_values('mae')

print(err_by_dx.head(20))

# Plotting MAE by diagnosis group
plt.figure(figsize=(12,6))
err_by_dx['mae'].plot(kind='bar')
plt.title('MAE by Diagnosis Group')
plt.ylabel('Mean Absolute Error')
plt.show()



























im trying to do an evaluation of er program; program identification is members with greater than 4 er visits, im trying to do intent to treat and engaged analysis. for engaged cohort my treatment is actually engaged on avergae of 65 days ... so index date is technically 65 days from identified and control group is just identified similar national population , hence pre post er utilization metrics for control and treatment group differ a lot








Interpretation – RAP vs. RAP-SNF
	•	Identification: RAP-SNF identified 52% of total admits versus 45% under RAP. However, much of the higher identification reflects members already captured through RAP-Acute, indicating program overlap rather than unique new capture.
	•	Targeting: RAP-SNF targeted 25% of total admits compared to 14% for RAP, showing stronger operational follow-through from identification to outreach in the post-acute space.
	•	Engagement: Engagement of total admits was higher for RAP-SNF (9%) versus RAP (5%), with engagement conversion among targeted members remaining consistent at ~35–36%, indicating similar outreach effectiveness once members are contacted.








m
SELECT
  mc.member_id,
  -- Count of ER visits from medical_case source
  COUNT(DISTINCT CASE 
    WHEN TRIM(mc.med_cs_ps_ctg_cd) = 'E' 
         AND mc.source = 'medical_case' 
    THEN mc.med_case_start_dt 
  END) AS medical_case_er_count,

  -- Count of ER visits from daily_claims source
  COUNT(DISTINCT CASE 
    WHEN TRIM(mc.med_cs_ps_ctg_cd) = 'E' 
         AND mc.source = 'daily_claims' 
    THEN mc.med_case_start_dt 
  END) AS daily_claims_er_count,

  -- Total distinct ER visits across all sources
  COUNT(DISTINCT CASE 
    WHEN TRIM(mc.med_cs_ps_ctg_cd) = 'E' 
    THEN mc.med_case_start_dt 
  END) AS total_er_count

FROM your_table_name mc
GROUP BY mc.member_id;









You’re right — the “Any CM Activity” category does include both regular RAP and RAP SNF programs.

To clarify how the metrics differ:
	•	Metrics 1 & 2 (RAP SNF Target and Engagement Rates) were calculated using the unique program card associated with each authorization ID.
	•	When a member is identified by regular RAP (acute) and later transitions to a SNF, the same CM program card remains open and is not re-created for the SNF authorization.
	•	As a result, metrics 1 and 2 only reflect newly identified members during the SNF stay (i.e., those not already under an active RAP CM program).
	•	Metrics 3–5 (Any CM Activity), on the other hand, take a broader view of all CM engagement, regardless of which model triggered the initial identification.
	•	These metrics capture any CM program activity between the SNF admit date and up to 30 days post-discharge, covering both regular RAP and RAP SNF engagements.

In total, out of ~144K scored SNF cases, around 74K (≈51%) were identified. While identification volumes are higher during SNF, many of these members were already identified earlier by the regular RAP model during their acute stay and continued under that same CM card. Therefore, most SNF identifications represent continuations rather than net-new identifications.

Regarding your observation — it’s expected that only a small portion of SNF discharges appear as new identifications under regular RAP, since the workflow intentionally suppresses new program creation when a member transitions from acute to SNF. SNF admits are indeed targeted, but as you mentioned, case management activity tends to be limited during the SNF phase and picks up closer to the discharge-to-home transition.








Post-Acute CM Engagement Overview (from first sheet)
	•	65% of all SNF admits are targeted for Case Management (CM).
	•	35.4% of RAP-targeted SNF admits are engaged in CM.
	•	Indicates moderate conversion from targeting to engagement — opportunity to strengthen CM follow-through.

⸻

2️⃣ RAP-SNF Monthly Performance (Jan–Sep 2025)
	•	Average Target Rate: ~47% of identified SNF admits targeted.
	•	Average Engagement Rate: ~36% of targeted admits engaged.
	•	Highest Target Rate: April (57%)
	•	Highest Engagement Rate: September (43%)
	•	Targeting fluctuates month to month, while engagement remains steady with slight improvement in late Q3.




WITH ranked_programs AS (
  SELECT
    pme_reference_no,
    memberprogramid,
    first_program_track,
    CASE
      WHEN first_program_track = 'RAP' THEN 1
      WHEN first_program_track = 'ACCP' THEN 2
      WHEN first_program_track = 'High' THEN 3
      WHEN first_program_track = 'Medium' THEN 4
      ELSE 99
    END AS program_priority
  FROM
    `anbc-hcb-dev.clin_analytics_hcb_dev.DS_SNF_YTD_Analysis_03_Final_SNF_PROGRAM_ACTIVITY_FY25`
),

deduped AS (
  SELECT
    pme_reference_no,
    memberprogramid,
    first_program_track,
    program_priority,
    ROW_NUMBER() OVER (PARTITION BY pme_reference_no ORDER BY program_priority) AS rn
  FROM ranked_programs
)

SELECT
  pme_reference_no,
  memberprogramid,
  first_program_track,
  program_priority
FROM deduped
WHERE rn = 1;





SELECT
    pme_reference_no,
    req_load_dt,
    actual_discharge_dt,
    lobcode,
    scored_volume
FROM your_table
WHERE actual_discharge_dt IS NOT NULL
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY pme_reference_no
    ORDER BY actual_discharge_dt ASC
) = 1;






WITH distinct_activity AS (
  SELECT
    memberprogramid,
    pme_reference_no,
    MAX(rap_targeted)       AS rap_targeted,
    MAX(rap_engaged)        AS rap_engaged,
    MAX(accp_targeted)      AS accp_targeted,
    MAX(accp_engaged)       AS accp_engaged,
    MAX(high_targeted)      AS high_targeted,
    MAX(high_engaged)       AS high_engaged,
    MAX(medium_targeted)    AS medium_targeted,
    MAX(medium_engaged)     AS medium_engaged,
    MAX(bh_targeted)        AS bh_targeted,
    MAX(bh_engaged)         AS bh_engaged,
    MAX(complex_chronic)    AS complex_chronic,
    MAX(short_term_referral) AS short_term_referral,
    MAX(healthy_heart)      AS healthy_heart,
    MAX(social_services)    AS social_services,
    MAX(dedicated_grouptriggers) AS dedicated_grouptriggers
  FROM
    `anbc-hcb-dev.clin_analytics_hcb_dev.DS_SNF_YTD_Analysis_03_Final_SNF_PROGRAM_ACTIVITY_FY25`
  GROUP BY
    memberprogramid, pme_reference_no
)

SELECT
  COUNT(*) AS row_cnt,
  COUNT(DISTINCT memberprogramid) AS pgm_cnt,
  COUNT(DISTINCT pme_reference_no) AS auth_cnt,
  SUM(rap_targeted) AS rap_targeted,
  SUM(rap_engaged) AS rap_engaged,
  SUM(accp_targeted) AS accp_targeted,
  SUM(accp_engaged) AS accp_engaged,
  SUM(high_targeted) AS high_targeted,
  SUM(high_engaged) AS high_engaged,
  SUM(medium_targeted) AS medium_targeted,
  SUM(medium_engaged) AS medium_engaged,
  SUM(bh_targeted) AS bh_targeted,
  SUM(bh_engaged) AS bh_engaged,
  SUM(complex_chronic) AS complex_chronic,
  SUM(short_term_referral) AS short_term_referral,
  SUM(healthy_heart) AS healthy_heart,
  SUM(social_services) AS social_services,
  SUM(dedicated_grouptriggers) AS dedicated_grouptriggers
FROM distinct_activity;







CASE 
  WHEN discharge_date = DATE '9999-12-31' THEN discharge_date
  ELSE DATE_ADD(discharge_date, INTERVAL 30 DAY)
END AS discharge_plus_30


WITH windowed_auth AS (
  SELECT
    service_auth_id,
    member_id,
    admit_date,
    discharge_date,
    DATE_ADD(discharge_date, INTERVAL 30 DAY) AS discharge_plus_30
  FROM
    service_auth
)

SELECT
  a.service_auth_id,
  a.member_id,
  p.program_id,

  -- Targeted flag: 1 if either min or max targeted date in window
  CASE 
    WHEN (p.min_targeted_dt BETWEEN a.admit_date AND a.discharge_plus_30)
      OR (p.max_targeted_dt BETWEEN a.admit_date AND a.discharge_plus_30)
    THEN 1 ELSE 0 
  END AS targeted_flag,

  -- Engaged flag: 1 if either min or max engaged date in window
  CASE 
    WHEN (p.min_engaged_dt BETWEEN a.admit_date AND a.discharge_plus_30)
      OR (p.max_engaged_dt BETWEEN a.admit_date AND a.discharge_plus_30)
    THEN 1 ELSE 0 
  END AS engaged_flag

FROM
  windowed_auth a
LEFT JOIN
  programs p
ON
  a.member_id = p.member_id
WHERE
  -- Keep rows where there’s at least some overlap
  ( (p.min_targeted_dt BETWEEN a.admit_date AND a.discharge_plus_30)
    OR (p.max_targeted_dt BETWEEN a.admit_date AND a.discharge_plus_30)
    OR (p.min_engaged_dt BETWEEN a.admit_date AND a.discharge_plus_30)
    OR (p.max_engaged_dt BETWEEN a.admit_date AND a.discharge_plus_30) )
ORDER BY
  a.service_auth_id, p.program_id;
  
  
  
  








We do have discharge date information available in the RAP API payloads that are refreshed daily, so that can be leveraged for this analysis.

@Mike — it would be helpful to learn more about how this is captured or derived from the MedCompass curated tables, so we can align both sources. Could you please also share the point of contact who can help us with access or additional details on that?

Thanks,
Chakradhar






-- Base cohort with one row per (individual_id, index_dt)
WITH base AS (
  SELECT
    individual_id,
    index_dt
  FROM `your_project.your_ds.er_eval_version2_eligible_membership_04`   -- << change
),

-- 1) DAILY CLAIMS: last 3 months before index_dt, only claims adjudicated by index_dt,
--    and keep the row with the latest insights_pstd_dts per (member, visit date, index_dt)
daily_keep AS (
  SELECT
    b.individual_id,
    b.index_dt,
    d.med_case_start_dt
  FROM base b
  JOIN `your_project.your_ds.daily_claim_line_final` d                     -- << change
    ON d.individual_id = b.individual_id
   AND TRIM(d.med_cs_ps_ctg_cd) = 'E'
   AND DATE(d.adjn_dt) <= b.index_dt
   AND d.med_case_start_dt >= DATE_SUB(b.index_dt, INTERVAL 3 MONTH)
   AND d.med_case_start_dt <  b.index_dt
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY b.individual_id, b.index_dt, d.med_case_start_dt
    ORDER BY d.insights_pstd_dts DESC
  ) = 1
),

-- 2) MEDICAL CASE: months -6 to -3 relative to index_dt
medcase_keep AS (
  SELECT
    b.individual_id,
    b.index_dt,
    m.med_case_start_dt
  FROM base b
  JOIN `your_project.your_ds.medical_case` m                                  -- << change
    ON m.individual_id = b.individual_id
   AND TRIM(m.med_cs_ps_ctg_cd) = 'E'
   AND m.med_case_start_dt >= DATE_SUB(b.index_dt, INTERVAL 6 MONTH)
   AND m.med_case_start_dt <  DATE_SUB(b.index_dt, INTERVAL 3 MONTH)
),

-- 3) UNION the two windows for the same (member, index_dt)
er_window AS (
  SELECT * FROM daily_keep
  UNION ALL
  SELECT * FROM medcase_keep
),

-- 4) Count distinct visits in the 6-month lookback for each (member, index_dt)
er_counts AS (
  SELECT
    individual_id,
    index_dt,
    COUNT(DISTINCT med_case_start_dt) AS er_visits_past_6m
  FROM er_window
  GROUP BY individual_id, index_dt
)

-- 5) Join back to base and flag ≥4
SELECT
  b.*,
  COALESCE(c.er_visits_past_6m, 0) AS er_visits_past_6m,
  CASE WHEN COALESCE(c.er_visits_past_6m, 0) >= 4 THEN 1 ELSE 0 END AS er6m_ge4
FROM base b
LEFT JOIN er_counts c
  ON c.individual_id = b.individual_id
 AND c.index_dt      = b.index_dt;









DECLARE start_month DATE DEFAULT DATE '2023-07-01';
DECLARE end_month   DATE DEFAULT DATE '2025-02-01';

WITH month_spine AS (
  SELECT month_dt
  FROM UNNEST(GENERATE_DATE_ARRAY(start_month, end_month, INTERVAL 1 MONTH)) AS month_dt
),

-- Daily ER (all time), pre-filter to ER + adjudicated rows; dedupe later per index
daily_er_all AS (
  SELECT
    individual_id,
    med_case_start_dt,
    insights_pstd_dts,
    adjn_dt
  FROM `your_project.your_ds.daily_claim_line_final`          -- << change
  WHERE TRIM(med_cs_ps_ctg_cd) = 'E'
),

-- Medical case ER (all time)
medcase_er_all AS (
  SELECT
    individual_id,
    med_case_start_dt
  FROM `your_project.your_ds.medical_case`                    -- << change
  WHERE TRIM(med_cs_ps_ctg_cd) = 'E'
),

-- Build member × index_month counts
er_6m_by_month AS (
  SELECT
    m.month_dt AS index_month,
    x.individual_id,
    COUNT(DISTINCT x.med_case_start_dt) AS er_visits_past_6m
  FROM month_spine m
  JOIN (
    -- recent 3 months from DAILY (adjudicated by index, latest posting kept)
    SELECT
      d.individual_id,
      d.med_case_start_dt,
      m2.month_dt AS index_month
    FROM month_spine m2
    JOIN (
      SELECT
        individual_id,
        med_case_start_dt,
        insights_pstd_dts,
        adjn_dt,
        ROW_NUMBER() OVER (
          PARTITION BY individual_id, med_case_start_dt
          ORDER BY insights_pstd_dts DESC
        ) AS rn
      FROM daily_er_all
    ) d
      ON d.rn = 1
     AND DATE(d.adjn_dt) <= m2.month_dt
     AND d.med_case_start_dt >= DATE_SUB(m2.month_dt, INTERVAL 3 MONTH)
     AND d.med_case_start_dt <  m2.month_dt

    UNION ALL

    -- months -6 to -3 from MED CASE
    SELECT
      mc.individual_id,
      mc.med_case_start_dt,
      m3.month_dt AS index_month
    FROM month_spine m3
    JOIN medcase_er_all mc
      ON mc.med_case_start_dt >= DATE_SUB(m3.month_dt, INTERVAL 6 MONTH)
     AND mc.med_case_start_dt <  DATE_SUB(m3.month_dt, INTERVAL 3 MONTH)
  ) x
    ON TRUE
  GROUP BY index_month, individual_id
)

SELECT
  index_month,
  individual_id,
  er_visits_past_6m,
  CASE WHEN er_visits_past_6m >= 4 THEN 1 ELSE 0 END AS er6m_ge4
FROM er_6m_by_month
ORDER BY index_month, individual_id;








import pandas as pd
import matplotlib.pyplot as plt

# Example: assuming your dataframe is called df
# and columns are named 'pcp_visits_past_6M' and 'er_visits_past_6M'

# List of categorical/count columns you want to visualize
cols_to_plot = ['pcp_visits_past_6M', 'er_visits_past_6M']

# Loop through each and plot histogram
for col in cols_to_plot:
    plt.figure(figsize=(6,4))
    df[col].value_counts().sort_index().plot(kind='bar', color='skyblue', edgecolor='black')
    plt.title(f'Distribution of {col}')
    plt.xlabel(col)
    plt.ylabel('Count of Members')
    plt.xticks(rotation=0)
    plt.show()
    
    
import seaborn as sns

for col in cols_to_plot:
    plt.figure(figsize=(6,4))
    sns.histplot(data=df, x=col, hue='treatment_grp', multiple='dodge', bins=range(0,10), shrink=0.8)
    plt.title(f'Distribution of {col} by Treatment Group')
    plt.xlabel(col)
    plt.ylabel('Count of Members')
    plt.show()







# List of columns representing BH conditions
bh_cols = ['ANX', 'DEP', 'PMC', 'BIP', 'DEM', 'CDO', 'EDO', 'SDO', 'PPD', 'PSY', 'ALC', 'AUT']

# Create bh_flag column
eng_eval['bh_flag'] = (eng_eval[bh_cols].sum(axis=1) > 0).astype(int)





We use both IPW and Overlap Weighting in DiD models. While IPW balances groups based on treatment probability, OW improves precision by emphasizing members where treatment and control populations are most comparable. This ensures findings are robust even in small or imbalanced samples.




A re-weighting approach that focuses analysis on the population with the greatest overlap in baseline characteristics between treatment and control.
	•	Down-weights extreme cases with very low/high treatment probability.
	•	Produces better covariate balance than IPW in small samples.





# keep only strata with both 0 and 1
valid_strata = itt_eval.groupby(["index_yrmo", "pre_mm_180", "post_mm_90"])["treatment_grp"].nunique()
valid_strata = valid_strata[valid_strata == 2].index

itt_eval_filtered = itt_eval.set_index(["index_yrmo", "pre_mm_180", "post_mm_90"]).loc[valid_strata].reset_index()








itt_eval["index_yrmo"] = itt_eval["index_year"].astype(str) + "_" + itt_eval["index_month"].astype(str)

# Post mm 90
valid_post_mm = itt_eval.groupby("post_mm_90")["treatment_grp"].nunique()
valid_post_mm = valid_post_mm[valid_post_mm == 2].index

# Pre mm 180
valid_pre_mm = itt_eval.groupby("pre_mm_180")["treatment_grp"].nunique()
valid_pre_mm = valid_pre_mm[valid_pre_mm == 2].index

# Index year-month
valid_index_yrmo = itt_eval.groupby("index_yrmo")["treatment_grp"].nunique()
valid_index_yrmo = valid_index_yrmo[valid_index_yrmo == 2].index


itt_eval_filtered = itt_eval[
    itt_eval["post_mm_90"].isin(valid_post_mm) &
    itt_eval["pre_mm_180"].isin(valid_pre_mm) &
    itt_eval["index_yrmo"].isin(valid_index_yrmo)
].copy()

print("Before:", itt_eval.shape)
print("After :", itt_eval_filtered.shape)







import pandas as pd
import numpy as np

# assume df['age_nbr'] contains numeric ages
bins = [0, 64, 69, 74, 79, 84, 200]
labels = ["<65", "65-69", "70-74", "75-79", "80-84", "85+"]

df['age_bucket'] = pd.cut(df['age_nbr'], bins=bins, labels=labels, right=True)

# check distribution
print(df['age_bucket'].value_counts())







WITH base AS (
  SELECT
    sc.edw_mbr_id,
    sc.index_dt,
    sc.*  -- keep all columns from study cohort
  FROM `project.dataset.study_cohort_01` sc
),

membership_months AS (
  SELECT
    b.edw_mbr_id,
    b.index_dt,
    DATE_TRUNC(em.eff_dt, MONTH) AS mem_month
  FROM base b
  JOIN `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_MEMBERSHIP` em
    ON em.member_id = b.edw_mbr_id
)

, flags AS (
  SELECT
    edw_mbr_id,
    index_dt,

    -- months before
    COUNT(DISTINCT CASE
      WHEN mem_month BETWEEN DATE_TRUNC(DATE_SUB(index_dt, INTERVAL 6 MONTH), MONTH)
                         AND DATE_TRUNC(DATE_SUB(index_dt, INTERVAL 1 MONTH), MONTH)
      THEN mem_month END) AS prev_6m,

    -- months after
    COUNT(DISTINCT CASE
      WHEN mem_month BETWEEN DATE_TRUNC(DATE_ADD(index_dt, INTERVAL 1 MONTH), MONTH)
                         AND DATE_TRUNC(DATE_ADD(index_dt, INTERVAL 3 MONTH), MONTH)
      THEN mem_month END) AS post_3m
  FROM membership_months
  GROUP BY edw_mbr_id, index_dt
)

-- join back to base
SELECT
  b.*,
  f.prev_6m,
  f.post_3m
FROM base b
LEFT JOIN flags f
  ON b.edw_mbr_id = f.edw_mbr_id
 AND b.index_dt = f.index_dt;








-- Build one row per member–month in the window around index_date
WITH base AS (
  SELECT
    sc.edw_mbr_id,
    sc.index_dt,
    -- normalize membership to month grain
    DATE_TRUNC(em.eff_dt, MONTH) AS mm_start
  FROM `project.dataset.study_cohort_01` sc
  JOIN `edp-prod-hcbstorage.edp_hcb_core_cnsv.EMIS_MEMBERSHIP` em
    ON em.member_id = sc.edw_mbr_id
  -- keep only Medicare (adjust filters as needed)
  LEFT JOIN `...PRODUCT_LINE` pl
    ON pl.member_id = em.member_id  -- <-- if this join multiplies rows,
  LEFT JOIN `...INDVDL_CUST_DIST` cd --     it will duplicate months; we dedup next.
    ON cd.member_id = em.member_id

  -- limit to months that could fall in the 6m pre or 3m post windows
  WHERE em.eff_dt BETWEEN DATE_SUB(sc.index_dt, INTERVAL 6 MONTH)
                      AND DATE_ADD(sc.index_dt, INTERVAL 3 MONTH)
),

-- Deduplicate inflated months caused by the joins
dedup_mm AS (
  SELECT edw_mbr_id, index_dt, mm_start
  FROM (
    SELECT
      edw_mbr_id, index_dt, mm_start,
      ROW_NUMBER() OVER (
        PARTITION BY edw_mbr_id, index_dt, mm_start
        ORDER BY mm_start
      ) AS rn
    FROM base
  )
  WHERE rn = 1
),

-- Count distinct months in pre/post windows (exclude index day by using -1/+1)
mm_counts AS (
  SELECT
    edw_mbr_id,
    index_dt,
    COUNTIF(
      mm_start BETWEEN DATE_TRUNC(DATE_SUB(index_dt, INTERVAL 6 MONTH), MONTH)
                   AND DATE_TRUNC(DATE_SUB(index_dt, INTERVAL 1 DAY),   MONTH)
    ) AS prev_6m,
    COUNTIF(
      mm_start BETWEEN DATE_TRUNC(DATE_ADD(index_dt, INTERVAL 1 DAY),   MONTH)
                   AND DATE_TRUNC(DATE_ADD(index_dt, INTERVAL 90 DAY),  MONTH)
    ) AS post_3m
  FROM dedup_mm
  GROUP BY 1,2
)

-- Attach back to your cohort
SELECT sc.*, mc.prev_6m, mc.post_3m
FROM `project.dataset.study_cohort_01` sc
LEFT JOIN mm_counts mc
  ON mc.edw_mbr_id = sc.edw_mbr_id
 AND mc.index_dt   = sc.index_dt;











-- ================================================
-- CONTROL COHORT WITH PRE/POST MEMBER-MONTH BALANCING
-- ================================================

-- 1. Control pool by month, including pre/post member-months
WITH control_pool_by_month AS (
  SELECT
    CAST(mbr_id AS STRING)      AS mbr_id,
    DATE_TRUNC(index_date, MONTH) AS index_month,
    prev_6m,
    post_3m
  FROM `project.dataset.randomized_control_with_er_id`
  WHERE eff_dt_last IS NOT NULL
),

-- 2. Assign exactly ONE canonical month per control member (stable random),
-- partitioned by index_month + prev_6m + post_3m
assigned_controls AS (
  SELECT
    mbr_id,
    index_month,
    prev_6m,
    post_3m,
    ROW_NUMBER() OVER (
      PARTITION BY mbr_id
      ORDER BY FARM_FINGERPRINT(CONCAT(mbr_id, '|', CAST(index_month AS STRING)))
    ) AS rn
  FROM control_pool_by_month
),
canonical_controls AS (
  SELECT
    mbr_id,
    index_month,
    prev_6m,
    post_3m
  FROM assigned_controls
  WHERE rn = 1
),

-- 3. Match control for ENGAGED cohort:
--    Sample per month, matching on prev_6m & post_3m as well
control_engaged AS (
  SELECT
    ac.mbr_id,
    ac.index_month,
    ac.prev_6m,
    ac.post_3m,
    'ENGAGED_CONTROL' AS control_cohort
  FROM canonical_controls ac
  JOIN (
    SELECT index_month, prev_6m, post_3m, COUNT(DISTINCT edw_mbr_id) AS engaged_cnt
    FROM `project.dataset.study_cohort_01`
    WHERE cohort_type = 'engaged'
    GROUP BY 1,2,3
  ) ed
  ON ac.index_month = ed.index_month
     AND ac.prev_6m   = ed.prev_6m
     AND ac.post_3m   = ed.post_3m
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ac.index_month, ac.prev_6m, ac.post_3m
    ORDER BY FARM_FINGERPRINT(ac.mbr_id)
  ) <= ed.engaged_cnt * 20
),

-- 4. Match control for ITT cohort:
--    Sample per month, matching on prev_6m & post_3m as well
control_itt AS (
  SELECT
    ac.mbr_id,
    ac.index_month,
    ac.prev_6m,
    ac.post_3m,
    'ITT_CONTROL' AS control_cohort
  FROM canonical_controls ac
  JOIN (
    SELECT index_month, prev_6m, post_3m, COUNT(DISTINCT edw_mbr_id) AS itt_cnt
    FROM `project.dataset.study_cohort_01`
    WHERE cohort_type = 'targeted'
    GROUP BY 1,2,3
  ) id
  ON ac.index_month = id.index_month
     AND ac.prev_6m   = id.prev_6m
     AND ac.post_3m   = id.post_3m
  LEFT JOIN control_engaged ce
    ON ce.mbr_id = ac.mbr_id
  WHERE ce.mbr_id IS NULL  -- ensure disjoint sets
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ac.index_month, ac.prev_6m, ac.post_3m
    ORDER BY FARM_FINGERPRINT(ac.mbr_id)
  ) <= id.itt_cnt * 20
)

-- 5. Union ENGAGED + ITT controls
SELECT * FROM control_engaged
UNION ALL
SELECT * FROM control_itt;










1. Adjustors (go into propensity / overlap weights, DID models)

Use these so treatment and control are balanced at baseline:
	•	Demographics: age, gender
	•	Clinical risk: risk scores (IP6, Frisk, ER, Strategic), chronic count, HCC if available
	•	Utilization & cost history: pre-ER visits (PMPM or band for engaged), IP admits, costs, HPD/polypharmacy
	•	Enrollment: pre member months (180d)
	•	Program contamination (baseline): cm_pre180_engaged, cm_pre90_engaged, cm_ongoing_at_index_engaged
	•	VBC flag, PCP flag (access to coordinated care models)
	•	SDOH flags (rural/urban, access score, LIS/dual status, subsidy)

👉 Adjustors = what the model balances on so the groups are comparable.

⸻

2. Descriptive Stats (reporting, context only)

Use these to describe populations and interpret results, but not always in PS model:
	•	Market/state distributions (MI, IL, WI, IN)
	•	Index month distribution
	•	Post-period CM flags (cm_post90_start, cm_post90_overlap) → show as contamination rates, but keep out of PS model (can be DID covariates)
	•	Breakdown by VBC, PCP, SDOH (good for context in reporting)

👉 Descriptive = tells the story of who’s in program, how different they are, and contamination rates.

⸻

3. Exact Match Variables (PSM setup)

Use for must-have identical categories before propensity score caliper matching:
	•	Index month (align observation window)
	•	Market/state (MI, IL, WI, IN)
	•	LOB/product (Medicare vs DSNP)
	•	Pre member months band (continuous enrollment buckets)
	•	VBC flag (yes/no)

👉 Exact match = avoids impossible comparisons (e.g., MI member in Jan 2024 vs WI member in Sep 2025).

⸻

✅ In one line to manager:
	•	“We use CM/VBC/PCP/SDOH flags mainly as adjustors to ensure fair comparison. Some are also shown descriptively to explain program context. A few key structural ones (index month, market, LOB, enrollment) we enforce via exact matching so treated and controls are truly comparable.”














ER Evaluation – Progress & Next Steps

Findings so far
	1.	Raw DID results (no adjustment)
	•	Treatment group (ER diversion) shows higher ER visits post-index than control, suggesting the program is not effective at reducing ER visits.
	•	Early signal is negative ROI at high level.
	2.	Treatment & Control definitions
	•	Treatment = targeted and engaged ER diversion members (subset also analyzed: engaged only).
	•	Control = national matched population (restricted to pre 6m + post 3m continuous enrollment).
	•	But, treatment/control differences exist because of CM program overlaps.
	3.	Other program overlaps (contamination)
	•	Members may already be engaged in other CM programs (RA, ACCP, High/Medium) before or during ER diversion.
	•	If engaged elsewhere at index, ER diversion just “marks” them engaged (not true outreach).
	•	Built flags to measure this contamination:
	•	Pre-180/Pre-90 (recent CM exposure before index).
	•	Ongoing at index (active CM on index date).
	•	Post-90 start (new CM starts in follow-up).
	•	Post-90 overlap (any CM active during follow-up).
	4.	Data quality & CM process notes
	•	CM sometimes don’t enter end_dt → handled by treating NULL as “still open.”
	•	Continuous enrollment difference: controls are fully enrolled pre/post, treatment has variation — using PMPM normalizes but still worth flagging.

⸻

Next Steps
	1.	Propensity/IPW adjustment
	•	Use baseline covariates (demographics, risk scores, utilization, costs, cm_pre180_engaged, vbc_flag) to balance treatment vs control.
	•	Avoid post variables in IPW to prevent leakage.
	2.	DID regression refinement
	•	Add post contamination flags (cm_post90_start_engaged, cm_post90_overlap_engaged) as adjustors.
	•	Sensitivity: exclude members with cm_ongoing_at_index_engaged=1 to isolate “true ER diversion.”
	3.	Descriptive reporting
	•	Show overlap percentages: how many ERD members were already in other CM, how many picked up new CM in follow-up.
	•	Split engaged vs targeted results to show difference in program intensity.
	4.	Manager discussion points
	•	Even after IPW/DID, don’t expect a big reversal: raw signal already shows no ER reduction.
	•	Next steps help confirm robustness and clarify whether effects are driven by ER diversion vs other CM programs.
















Pre-period flags (baseline confounding)
	•	cm_pre180_engaged → 1 if the member was engaged in any CM program in the 180 days before index (using end_dt if available, otherwise start_dt).
	•	cm_pre90_engaged → 1 if the member was engaged in any CM program in the 90 days before index.
	•	cm_pre180_targeted → 1 if the member was targeted in any CM program in the 180 days before index.
	•	cm_pre90_targeted → 1 if the member was targeted in any CM program in the 90 days before index.

⸻

Ongoing at index flags (contamination at baseline)
	•	cm_ongoing_at_index_engaged → 1 if the member was actively engaged in another CM program on the index date (start ≤ index ≤ end, with open-ended if end_dt missing).
	•	cm_ongoing_at_index_targeted → 1 if the member was targeted and still open on the index date.

⸻

Post-period flags (contamination in follow-up)
	•	cm_post90_start_engaged → 1 if the member started engagement in another CM program within 0–90 days after index.
	•	cm_post90_overlap_engaged → 1 if the member had any overlap with an engagement episode during the 0–90 day post window (includes those that started before but continued).
	•	cm_post90_start_targeted → 1 if the member was targeted for another CM program in the 0–90 days after index.
	•	cm_post90_overlap_targeted → 1 if the member had any targeted episode overlapping with the 0–90 day post window.

⸻

✅ That’s it — 10 clean flags.
Each is 0/1 per member, so your cohort stays 1 row per individual_id + index_date.

⸻

How to use them
	•	Propensity (IPW model): use cm_pre180_engaged (baseline CM exposure) + vbc_flag.
	•	DID regression adjustors: use cm_post90_start_engaged or cm_post90_overlap_engaged to adjust for post contamination.
	•	Descriptive slides: report both engaged + targeted versions to show “touched vs active” overlap.
	•	Sensitivity: rerun models excluding members with cm_ongoing_at_index_engaged = 1 (auto-engaged cases).








## new

CREATE TEMP TABLE episodes AS
WITH mc AS (
  SELECT * FROM `project.dataset.medcompass_activity_mc_status_program_level`
),
unified AS (
  -- ENGAGED episodes
  SELECT individual_id, 'ENGAGED' AS episode_type, 'RAP' AS program,
         min_engaged_date_rap  AS start_dt, max_engaged_date_rap  AS end_dt FROM mc
  UNION ALL SELECT individual_id, 'ENGAGED', 'ACCP',  min_engaged_date_accp,  max_engaged_date_accp  FROM mc
  UNION ALL SELECT individual_id, 'ENGAGED', 'HIGH',  min_engaged_date_high,  max_engaged_date_high  FROM mc
  UNION ALL SELECT individual_id, 'ENGAGED', 'MED',   min_engaged_date_medium,max_engaged_date_medium FROM mc

  UNION ALL
  -- TARGETED episodes
  SELECT individual_id, 'TARGETED', 'RAP',  min_targeted_date_rap,  max_targeted_date_rap  FROM mc
  UNION ALL SELECT individual_id, 'TARGETED', 'ACCP', min_targeted_date_accp, max_targeted_date_accp FROM mc
  UNION ALL SELECT individual_id, 'TARGETED', 'HIGH', min_targeted_date_high, max_targeted_date_high FROM mc
  UNION ALL SELECT individual_id, 'TARGETED', 'MED',  min_targeted_date_medium, max_targeted_date_medium FROM mc
)
SELECT individual_id, episode_type, program, start_dt, end_dt
FROM unified
WHERE start_dt IS NOT NULL OR end_dt IS NOT NULL;   -- keep only real episodes


CREATE TEMP TABLE pre_flags AS
WITH e AS (
  SELECT e.*, c.index_date,
         -- last_touch = end_dt if present, else start_dt
         COALESCE(e.end_dt, e.start_dt) AS last_touch
  FROM episodes e
  JOIN cohort  c USING (individual_id)
),
-- choose closest (latest) episode in PRE-180 by episode_type
pre180 AS (
  SELECT individual_id, episode_type,
         ARRAY_AGG(STRUCT(program, last_touch) ORDER BY last_touch DESC LIMIT 1)[OFFSET(0)] AS pick
  FROM e
  WHERE last_touch BETWEEN DATE_SUB(index_date, INTERVAL 180 DAY) AND index_date
  GROUP BY individual_id, episode_type
),
-- choose closest (latest) episode in PRE-90 by episode_type
pre90 AS (
  SELECT individual_id, episode_type,
         ARRAY_AGG(STRUCT(program, last_touch) ORDER BY last_touch DESC LIMIT 1)[OFFSET(0)] AS pick
  FROM e
  WHERE last_touch BETWEEN DATE_SUB(index_date, INTERVAL 90 DAY) AND index_date
  GROUP BY individual_id, episode_type
),
-- ongoing at index: episodes with start <= index <= end
ongoing AS (
  SELECT individual_id, episode_type,
         -- pick the one that started most recently before index (closest active episode)
         ARRAY_AGG(STRUCT(program, start_dt, end_dt) ORDER BY start_dt DESC LIMIT 1)[OFFSET(0)] AS pick
  FROM (
    SELECT e.*,
           -- treat NULL end as far-future for overlap check only
           IFNULL(e.end_dt, DATE '9999-12-31') AS end_for_overlap
    FROM e
  ) x
  WHERE x.start_dt <= x.index_date AND x.end_for_overlap >= x.index_date
  GROUP BY individual_id, episode_type
)

SELECT
  c.individual_id,
  c.index_date,

  -- ENGAGED (dates + flags + program picked)
  (SELECT pick.last_touch FROM pre180  WHERE pre180.individual_id=c.individual_id AND episode_type='ENGAGED') AS pre180_eng_dt,
  (SELECT pick.program   FROM pre180  WHERE pre180.individual_id=c.individual_id AND episode_type='ENGAGED') AS pre180_eng_program,
  CAST((SELECT 1 FROM pre180 WHERE pre180.individual_id=c.individual_id AND episode_type='ENGAGED') IS NOT NULL AS INT64) AS cm_pre180_engaged,

  (SELECT pick.last_touch FROM pre90   WHERE pre90.individual_id =c.individual_id AND episode_type='ENGAGED') AS pre90_eng_dt,
  (SELECT pick.program   FROM pre90   WHERE pre90.individual_id =c.individual_id AND episode_type='ENGAGED') AS pre90_eng_program,
  CAST((SELECT 1 FROM pre90  WHERE pre90.individual_id =c.individual_id AND episode_type='ENGAGED') IS NOT NULL AS INT64) AS cm_pre90_engaged,

  CAST((SELECT 1 FROM ongoing WHERE ongoing.individual_id=c.individual_id AND episode_type='ENGAGED') IS NOT NULL AS INT64) AS cm_ongoing_at_index_engaged,
  (SELECT pick.program FROM ongoing WHERE ongoing.individual_id=c.individual_id AND episode_type='ENGAGED') AS ongoing_eng_program,

  -- TARGETED (dates + flags + program picked)
  (SELECT pick.last_touch FROM pre180  WHERE pre180.individual_id=c.individual_id AND episode_type='TARGETED') AS pre180_tar_dt,
  (SELECT pick.program   FROM pre180  WHERE pre180.individual_id=c.individual_id AND episode_type='TARGETED') AS pre180_tar_program,
  CAST((SELECT 1 FROM pre180 WHERE pre180.individual_id=c.individual_id AND episode_type='TARGETED') IS NOT NULL AS INT64) AS cm_pre180_targeted,

  (SELECT pick.last_touch FROM pre90   WHERE pre90.individual_id =c.individual_id AND episode_type='TARGETED') AS pre90_tar_dt,
  (SELECT pick.program   FROM pre90   WHERE pre90.individual_id =c.individual_id AND episode_type='TARGETED') AS pre90_tar_program,
  CAST((SELECT 1 FROM pre90  WHERE pre90.individual_id =c.individual_id AND episode_type='TARGETED') IS NOT NULL AS INT64) AS cm_pre90_targeted,

  CAST((SELECT 1 FROM ongoing WHERE ongoing.individual_id=c.individual_id AND episode_type='TARGETED') IS NOT NULL AS INT64) AS cm_ongoing_at_index_targeted,
  (SELECT pick.program FROM ongoing WHERE ongoing.individual_id=c.individual_id AND episode_type='TARGETED') AS ongoing_tar_program

FROM cohort c;



CREATE TEMP TABLE post_flags AS
WITH e AS (
  SELECT e.*, c.index_date,
         IFNULL(e.end_dt, DATE '9999-12-31') AS end_for_overlap
  FROM episodes e
  JOIN cohort  c USING (individual_id)
),

post_start AS (
  SELECT individual_id, episode_type,
         ARRAY_AGG(STRUCT(program, start_dt) ORDER BY start_dt ASC LIMIT 1)[OFFSET(0)] AS pick
  FROM e
  WHERE start_dt BETWEEN index_date AND DATE_ADD(index_date, INTERVAL 90 DAY)
  GROUP BY individual_id, episode_type
),

post_overlap AS (
  SELECT individual_id, episode_type,
         -- among overlapping episodes, pick the one that starts earliest in/near the window
         ARRAY_AGG(STRUCT(program, start_dt, end_for_overlap)
                   ORDER BY start_dt ASC LIMIT 1)[OFFSET(0)] AS pick
  FROM e
  WHERE start_dt <= DATE_ADD(index_date, INTERVAL 90 DAY)
    AND end_for_overlap >= index_date
  GROUP BY individual_id, episode_type
)

SELECT
  c.individual_id,
  c.index_date,

  -- ENGAGED post starts / overlap
  (SELECT pick.start_dt FROM post_start   WHERE post_start.individual_id=c.individual_id AND episode_type='ENGAGED') AS post90_eng_start_dt,
  CAST((SELECT 1         FROM post_start WHERE post_start.individual_id=c.individual_id AND episode_type='ENGAGED') IS NOT NULL AS INT64) AS cm_post90_start_engaged,
  CAST((SELECT 1         FROM post_overlap WHERE post_overlap.individual_id=c.individual_id AND episode_type='ENGAGED') IS NOT NULL AS INT64) AS cm_post90_overlap_engaged,
  (SELECT pick.program   FROM post_overlap WHERE post_overlap.individual_id=c.individual_id AND episode_type='ENGAGED') AS post_overlap_eng_program,

  -- TARGETED post starts / overlap
  (SELECT pick.start_dt FROM post_start   WHERE post_start.individual_id=c.individual_id AND episode_type='TARGETED') AS post90_tar_start_dt,
  CAST((SELECT 1         FROM post_start WHERE post_start.individual_id=c.individual_id AND episode_type='TARGETED') IS NOT NULL AS INT64) AS cm_post90_start_targeted,
  CAST((SELECT 1         FROM post_overlap WHERE post_overlap.individual_id=c.individual_id AND episode_type='TARGETED') IS NOT NULL AS INT64) AS cm_post90_overlap_targeted,
  (SELECT pick.program   FROM post_overlap WHERE post_overlap.individual_id=c.individual_id AND episode_type='TARGETED') AS post_overlap_tar_program

FROM cohort c;


# join all tables

SELECT
  p.individual_id,
  p.index_date,
  -- PRE flags/dates/programs
  pre.cm_pre180_engaged, pre.pre180_eng_dt, pre.pre180_eng_program,
  pre.cm_pre90_engaged,  pre.pre90_eng_dt,  pre.pre90_eng_program,
  pre.cm_ongoing_at_index_engaged, pre.ongoing_eng_program,
  pre.cm_pre180_targeted, pre.pre180_tar_dt, pre.pre180_tar_program,
  pre.cm_pre90_targeted,  pre.pre90_tar_dt,  pre.pre90_tar_program,
  pre.cm_ongoing_at_index_targeted, pre.ongoing_tar_program,
  -- POST flags/dates/programs
  post.cm_post90_start_engaged,  post.post90_eng_start_dt,  post.cm_post90_overlap_engaged,  post.post_overlap_eng_program,
  post.cm_post90_start_targeted, post.post90_tar_start_dt, post.cm_post90_overlap_targeted, post.post_overlap_tar_program
FROM cohort p
LEFT JOIN pre_flags  pre  USING (individual_id, index_date)
LEFT JOIN post_flags post USING (individual_id, index_date);






















### old
WITH cohort AS (
  SELECT individual_id, index_date
  FROM `project.dataset.er_eval_version2_final_cohort`
),

-- Pull (per member) program start/end pairs (min/max) for each program
raw AS (
  SELECT
    c.individual_id, c.index_date,

    -- ENGAGED windows
    mc.min_engaged_date_rap    AS rap_e_start,    mc.max_engaged_date_rap    AS rap_e_end,
    mc.min_engaged_date_accp   AS accp_e_start,   mc.max_engaged_date_accp   AS accp_e_end,
    mc.min_engaged_date_high   AS high_e_start,   mc.max_engaged_date_high   AS high_e_end,
    mc.min_engaged_date_medium AS med_e_start,    mc.max_engaged_date_medium AS med_e_end,

    -- TARGETED windows
    mc.min_targeted_date_rap    AS rap_t_start,   mc.max_targeted_date_rap    AS rap_t_end,
    mc.min_targeted_date_accp   AS accp_t_start,  mc.max_targeted_date_accp   AS accp_t_end,
    mc.min_targeted_date_high   AS high_t_start,  mc.max_targeted_date_high   AS high_t_end,
    mc.min_targeted_date_medium AS med_t_start,   mc.max_targeted_date_medium AS med_t_end
  FROM cohort c
  LEFT JOIN `project.dataset.medcompass_activity_mc_status_program_level` mc
    ON c.individual_id = mc.individual_id
),

-- Normalize to arrays so we can test windows with EXISTS cleanly
norm AS (
  SELECT
    individual_id, index_date,

    -- Treat NULL end as open-ended (still active)
    ARRAY<STRUCT<start DATE, finish DATE>>[
      STRUCT(rap_e_start,  COALESCE(rap_e_end,  DATE '9999-12-31')),
      STRUCT(accp_e_start, COALESCE(accp_e_end, DATE '9999-12-31')),
      STRUCT(high_e_start, COALESCE(high_e_end, DATE '9999-12-31')),
      STRUCT(med_e_start,  COALESCE(med_e_end,  DATE '9999-12-31'))
    ] AS engaged_eps,

    ARRAY<STRUCT<start DATE, finish DATE>>[
      STRUCT(rap_t_start,  COALESCE(rap_t_end,  DATE '9999-12-31')),
      STRUCT(accp_t_start, COALESCE(accp_t_end, DATE '9999-12-31')),
      STRUCT(high_t_start, COALESCE(high_t_end, DATE '9999-12-31')),
      STRUCT(med_t_start,  COALESCE(med_t_end,  DATE '9999-12-31'))
    ] AS targeted_eps
  FROM raw
)

SELECT
  individual_id,
  index_date,

  -- =========================
  -- ENGAGED (per any program)
  -- =========================

  -- Pre-180 (any engagement activity recorded within 180 days prior)
  CAST(EXISTS (
    SELECT 1 FROM UNNEST(engaged_eps) ep
    WHERE ep.finish BETWEEN DATE_SUB(index_date, INTERVAL 180 DAY) AND index_date
  ) AS INT64) AS cm_pre180_engaged,

  -- Pre-90 (recent engagement prior to index)
  CAST(EXISTS (
    SELECT 1 FROM UNNEST(engaged_eps) ep
    WHERE ep.finish BETWEEN DATE_SUB(index_date, INTERVAL 90 DAY) AND index_date
  ) AS INT64) AS cm_pre90_engaged,

  -- Ongoing at index (active on index_date)
  CAST(EXISTS (
    SELECT 1 FROM UNNEST(engaged_eps) ep
    WHERE ep.start <= index_date AND ep.finish >= index_date
  ) AS INT64) AS cm_ongoing_at_index_engaged,

  -- Post-90 START (a new engagement begins in 0–90d after index)
  CAST(EXISTS (
    SELECT 1 FROM UNNEST(engaged_eps) ep
    WHERE ep.start BETWEEN index_date AND DATE_ADD(index_date, INTERVAL 90 DAY)
  ) AS INT64) AS cm_post90_start_engaged,

  -- Post-90 OVERLAP (any engagement overlaps the 0–90d window)
  CAST(EXISTS (
    SELECT 1 FROM UNNEST(engaged_eps) ep
    WHERE ep.start <= DATE_ADD(index_date, INTERVAL 90 DAY)
      AND ep.finish >= index_date
  ) AS INT64) AS cm_post90_overlap_engaged,

  -- =========================
  -- TARGETED (per any program)
  -- =========================

  CAST(EXISTS (
    SELECT 1 FROM UNNEST(targeted_eps) ep
    WHERE ep.finish BETWEEN DATE_SUB(index_date, INTERVAL 180 DAY) AND index_date
  ) AS INT64) AS cm_pre180_targeted,

  CAST(EXISTS (
    SELECT 1 FROM UNNEST(targeted_eps) ep
    WHERE ep.finish BETWEEN DATE_SUB(index_date, INTERVAL 90 DAY) AND index_date
  ) AS INT64) AS cm_pre90_targeted,

  CAST(EXISTS (
    SELECT 1 FROM UNNEST(targeted_eps) ep
    WHERE ep.start <= index_date AND ep.finish >= index_date
  ) AS INT64) AS cm_ongoing_at_index_targeted,

  CAST(EXISTS (
    SELECT 1 FROM UNNEST(targeted_eps) ep
    WHERE ep.start BETWEEN index_date AND DATE_ADD(index_date, INTERVAL 90 DAY)
  ) AS INT64) AS cm_post90_start_targeted,

  CAST(EXISTS (
    SELECT 1 FROM UNNEST(targeted_eps) ep
    WHERE ep.start <= DATE_ADD(index_date, INTERVAL 90 DAY)
      AND ep.finish >= index_date
  ) AS INT64) AS cm_post90_overlap_targeted

FROM norm;











WITH cohort AS (
  SELECT individual_id, index_date
  FROM `project.dataset.er_eval_version2_final_cohort`
),

prog AS (
  SELECT
    c.individual_id,
    c.index_date,

    -- TARGETED min/max across all programs
    LEAST(
      mc.min_targeted_date_rap, mc.min_targeted_date_accp,
      mc.min_targeted_date_high, mc.min_targeted_date_medium
    ) AS any_min_targeted_dt,
    GREATEST(
      mc.max_targeted_date_rap, mc.max_targeted_date_accp,
      mc.max_targeted_date_high, mc.max_targeted_date_medium
    ) AS any_max_targeted_dt,

    -- ENGAGED min/max across all programs
    LEAST(
      mc.min_engaged_date_rap, mc.min_engaged_date_accp,
      mc.min_engaged_date_high, mc.min_engaged_date_medium
    ) AS any_min_engaged_dt,
    GREATEST(
      mc.max_engaged_date_rap, mc.max_engaged_date_accp,
      mc.max_engaged_date_high, mc.max_engaged_date_medium
    ) AS any_max_engaged_dt
  FROM cohort c
  LEFT JOIN `project.dataset.medcompass_activity_mc_status_program_level` mc
    ON c.individual_id = mc.individual_id
),

-- Handle NULLs
norm AS (
  SELECT
    *,
    IFNULL(any_min_targeted_dt, DATE '9999-12-31') AS min_tar,
    IFNULL(any_max_targeted_dt, DATE '1900-01-01') AS max_tar,
    IFNULL(any_min_engaged_dt,  DATE '9999-12-31') AS min_eng,
    IFNULL(any_max_engaged_dt,  DATE '1900-01-01') AS max_eng
  FROM prog
)

SELECT
  individual_id,
  index_date,

  -- =====================
  -- TARGETED FLAGS
  -- =====================

  -- Pre-180 (any targeted within 6m before index)
  CAST(max_tar BETWEEN DATE_SUB(index_date, INTERVAL 180 DAY) AND index_date AS INT64) AS cm_pre180_targeted,

  -- Pre-90 (any targeted within 90d before index)
  CAST(max_tar BETWEEN DATE_SUB(index_date, INTERVAL 90 DAY) AND index_date AS INT64)  AS cm_pre90_targeted,

  -- Ongoing at index
  CAST(min_tar <= index_date AND max_tar >= index_date AS INT64)                       AS cm_ongoing_at_index_targeted,

  -- Post-90 start (newly targeted after index)
  CAST(min_tar BETWEEN index_date AND DATE_ADD(index_date, INTERVAL 90 DAY) AS INT64)  AS cm_post90_start_targeted,

  -- Post-90 overlap (any targeted episode overlapping index→+90d)
  CAST(min_tar <= DATE_ADD(index_date, INTERVAL 90 DAY) AND max_tar >= index_date AS INT64) AS cm_post90_overlap_targeted,


  -- =====================
  -- ENGAGED FLAGS
  -- =====================

  -- Pre-180 (any engaged within 6m before index)
  CAST(max_eng BETWEEN DATE_SUB(index_date, INTERVAL 180 DAY) AND index_date AS INT64) AS cm_pre180_engaged,

  -- Pre-90 (any engaged within 90d before index)
  CAST(max_eng BETWEEN DATE_SUB(index_date, INTERVAL 90 DAY) AND index_date AS INT64)  AS cm_pre90_engaged,

  -- Ongoing at index
  CAST(min_eng <= index_date AND max_eng >= index_date AS INT64)                       AS cm_ongoing_at_index_engaged,

  -- Post-90 start (newly engaged after index)
  CAST(min_eng BETWEEN index_date AND DATE_ADD(index_date, INTERVAL 90 DAY) AS INT64)  AS cm_post90_start_engaged,

  -- Post-90 overlap (any engagement overlapping index→+90d)
  CAST(min_eng <= DATE_ADD(index_date, INTERVAL 90 DAY) AND max_eng >= index_date AS INT64) AS cm_post90_overlap_engaged

FROM norm;















m
%pip uninstall -y google-auth google-cloud-bigquery google-auth-impersonated-credentials google-cloud-core googleapis-common-protos

%pip install \
  google-cloud-bigquery==3.11.4 \
  google-auth==2.23.4 \
  google-auth-impersonated-credentials==2.1.0 \
  google-cloud-core==2.3.3 \
  pandas-gbq==0.22.0 \
  db-dtypes==1.2.0 \
  pyarrow==10.0.1



%pip install -U google-cloud-bigquery google-auth google-auth-impersonated-credentials pandas-gbq db-dtypes pyarrow

# 1) Activate the env you created
conda activate /home/jupyter/conda_envs/cobra_38

# 2) Install/upgrade the needed packages into THIS env
pip install -U pip setuptools wheel ipykernel \
  google-cloud-bigquery google-auth google-auth-impersonated-credentials \
  pandas-gbq db-dtypes pyarrow

# 3) (Re)register the kernel so Jupyter can use this env
python -m ipykernel install --name "cobra_38" --user















-- PREV 6 FULL MONTHS: from 1st of month 6 months before eff_dt
--                     to last day of month 1 month before eff_dt
CASE
  WHEN DATE_TRUNC(m.eff_dt, MONTH) BETWEEN
           DATE_TRUNC(DATE_SUB(a.eff_dt, INTERVAL 6 MONTH), MONTH)             -- e.g. 2024-01-01
       AND DATE_SUB(DATE_TRUNC(DATE_SUB(a.eff_dt, INTERVAL 1 MONTH), MONTH) 
                    + INTERVAL 1 MONTH, INTERVAL 1 DAY)                        -- e.g. 2024-06-30
  THEN 1 ELSE 0
END AS prev_6m,

-- POST 3 FULL MONTHS: from 1st of month 1 month after eff_dt
--                     to last day of month 3 months after eff_dt
CASE
  WHEN DATE_TRUNC(m.eff_dt, MONTH) BETWEEN
           DATE_TRUNC(DATE_ADD(a.eff_dt, INTERVAL 1 MONTH), MONTH)             -- e.g. 2024-08-01
       AND DATE_SUB(DATE_TRUNC(DATE_ADD(a.eff_dt, INTERVAL 3 MONTH), MONTH) 
                    + INTERVAL 1 MONTH, INTERVAL 1 DAY)                        -- e.g. 2024-10-31
  THEN 1 ELSE 0
END AS post_3m








#0826

-- ========= EDIT IF NEEDED =========
DECLARE TREATMENT_TABLE STRING DEFAULT 'anbc-hcb-dev.clin_analytics_hcb_dev.a538985_er_eval_version2_study_cohort_01';
DECLARE CONTROL_POOL_TABLE STRING DEFAULT 'anbc-hcb-dev.clin_analytics_hcb_dev.a538985_er_eval_version2_randomized_control_with_er_id';
-- CONTROL_POOL_TABLE columns (from your screenshot): member_id, business_ln_cd, eff_dt_last (DATE; month-end)
-- TREATMENT_TABLE columns: edw_mbr_id, engaged, engaged_date, targeted, targeted_date, cohort_type, index_dt (etc.)
-- =================================

-- 1) Treatment monthly distributions we need to mirror
WITH treat AS (
  SELECT
    CAST(edw_mbr_id AS STRING) AS mbr_id,
    engaged,
    targeted,
    SAFE.DATE(engaged_date)  AS engaged_dt,
    SAFE.DATE(targeted_date) AS targeted_dt
  FROM `${TREATMENT_TABLE}`
),

treat_months AS (
  SELECT
    -- month start is easier for joins
    DATE_TRUNC(engaged_dt,  MONTH) AS eng_index_month,
    DATE_TRUNC(targeted_dt, MONTH) AS itt_index_month,
    mbr_id,
    engaged,
    targeted
  FROM treat
),

eng_dist AS (
  SELECT eng_index_month AS index_month, COUNT(DISTINCT mbr_id) AS engaged_cnt
  FROM treat_months
  WHERE engaged = 1 AND eng_index_month IS NOT NULL
  GROUP BY 1
),
itt_dist AS (
  SELECT itt_index_month AS index_month, COUNT(DISTINCT mbr_id) AS itt_cnt
  FROM treat_months
  WHERE targeted = 1 AND itt_index_month IS NOT NULL
  GROUP BY 1
),

-- 2) Control pool (already filtered to “>4 ER in prior 6m” and membership window in your prep)
--    Normalize to month start so it aligns with eng_dist / itt_dist.
control_pool_by_month AS (
  SELECT
    CAST(member_id AS STRING) AS mbr_id,
    DATE_TRUNC(SAFE.DATE(eff_dt_last), MONTH) AS index_month  -- month start
  FROM `${CONTROL_POOL_TABLE}`
  WHERE eff_dt_last IS NOT NULL
),

-- 3) Assign exactly ONE canonical month per control member (stable random).
--    This guarantees no control appears more than once across months/cohorts.
assigned_controls AS (
  SELECT mbr_id, index_month AS assigned_month
  FROM (
    SELECT
      mbr_id,
      index_month,
      ROW_NUMBER() OVER (
        PARTITION BY mbr_id
        ORDER BY RAND(CAST(FARM_FINGERPRINT(mbr_id) AS INT64))  -- stable seed
      ) AS rn
    FROM control_pool_by_month
  )
  WHERE rn = 1
),

-- 4) CONTROL for ENGAGED: sample per month = engaged_cnt
control_engaged AS (
  SELECT
    ac.mbr_id,
    ac.assigned_month AS index_month,
    'ENGAGED_CONTROL' AS control_cohort
  FROM assigned_controls ac
  JOIN eng_dist ed
    ON ed.index_month = ac.assigned_month
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ac.assigned_month
    ORDER BY RAND(CAST(FARM_FINGERPRINT(ac.mbr_id) AS INT64))
  ) <= ed.engaged_cnt
),

-- 5) CONTROL for ITT: sample per month = itt_cnt, EXCLUDING any member used in ENGAGED
control_itt AS (
  SELECT
    ac.mbr_id,
    ac.assigned_month AS index_month,
    'ITT_CONTROL' AS control_cohort
  FROM assigned_controls ac
  JOIN itt_dist id
    ON id.index_month = ac.assigned_month
  LEFT JOIN control_engaged ce
    ON ce.mbr_id = ac.mbr_id    -- ensure disjoint control sets
  WHERE ce.mbr_id IS NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY ac.assigned_month
    ORDER BY RAND(CAST(FARM_FINGERPRINT(CONCAT(ac.mbr_id,'|ITT')) AS INT64))
  ) <= id.itt_cnt
)

-- 6) Final outputs (two separate selects). You can CREATE TABLE AS SELECT if desired.
SELECT * FROM control_engaged
UNION ALL
SELECT * FROM control_itt
ORDER BY control_cohort, index_month, mbr_id;


WITH need AS (
  SELECT 'ENGAGED' grp, * FROM eng_dist
  UNION ALL
  SELECT 'ITT' grp, * FROM itt_dist
),
have AS (
  SELECT 'ENGAGED' grp, index_month, COUNT(*) cnt FROM control_engaged GROUP BY 1,2
  UNION ALL
  SELECT 'ITT' grp, index_month, COUNT(*) cnt FROM control_itt GROUP BY 1,2
)
SELECT n.grp, n.index_month, 
       COALESCE(CASE WHEN n.grp='ENGAGED' THEN n.engaged_cnt ELSE n.itt_cnt END,0) AS need_cnt,
       COALESCE(h.cnt,0) AS have_cnt,
       COALESCE(CASE WHEN n.grp='ENGAGED' THEN n.engaged_cnt ELSE n.itt_cnt END,0) - COALESCE(h.cnt,0) AS short_by
FROM need n
LEFT JOIN have h USING (grp, index_month)
ORDER BY grp, index_month;










# 0826

WITH treat AS (
  SELECT
    member_id,
    DATE_TRUNC(index_date, MONTH) AS index_month,
    cohort_type   -- 'targeted' or 'engaged'
  FROM `proj.ds.treatment_table`
),

-- counts of treated per month and cohort_type
treat_counts AS (
  SELECT
    index_month,
    cohort_type,
    COUNT(*) AS n_treated
  FROM treat
  GROUP BY 1,2
),

-- control candidates (large pool)
control_pool AS (
  SELECT
    member_id,
    DATE_TRUNC(index_date, MONTH) AS index_month
    -- you can also add dummy cohort_type = 'targeted' or 'engaged'
    -- if you want to draw separately for both
  FROM `proj.ds.control_candidates`
),

-- rank control candidates within each month
control_ranked AS (
  SELECT
    c.member_id,
    c.index_month,
    -- random rank per month
    ROW_NUMBER() OVER (PARTITION BY c.index_month ORDER BY RAND()) AS rn
  FROM control_pool c
),

-- now select matched controls for each cohort_type
control_matched AS (
  SELECT
    t.cohort_type,
    r.member_id,
    r.index_month
  FROM treat_counts t
  JOIN control_ranked r
    ON r.index_month = t.index_month
  WHERE r.rn <= t.n_treated
)

SELECT * FROM control_matched;















# Aetna GitHub Enterprise
Host github-aetna
    HostName github.aetna.com
    User git
    IdentityFile ~/.ssh/id_ed25519_aetna
    IdentitiesOnly yes

# Personal GitHub
Host github-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_github
    IdentitiesOnly yes


# Start ssh-agent if not running
if ! pgrep -u "$USER" ssh-agent >/dev/null 2>&1; then
  eval "$(ssh-agent -s)" >/dev/null
fi

# Add keys (ignore errors if already added)
ssh-add -l >/dev/null 2>&1 || true
ssh-add ~/.ssh/id_ed25519_aetna 2>/dev/null || true
ssh-add ~/.ssh/id_ed25519_github 2>/dev/null || true



6. GOALS

Christine successfully met the goals outlined at the start of her internship. She familiarized herself with the RAP model pipelines and associated codebase, retrained both the Commercial and Medicare models using LLM-derived clinical notes, and conducted a thorough comparative analysis to evaluate performance impacts. Despite infrastructure delays early on, she showed good follow-through and delivered on all planned objectives.

⸻

7. HEART AT WORK BEHAVIORS

Christine demonstrated strong collaboration and adaptability throughout her internship. She proactively engaged with cross-functional teams — particularly when GCP infrastructure issues slowed down early progress — and followed up diligently with platform and engineering teams. Her willingness to listen, take feedback, and work independently while contributing to shared goals reflected the team’s values of ownership, teamwork, and continuous improvement.

⸻

8. OVERALL PERFORMANCE

Christine showed initiative and ownership over her project, especially in technical areas like optimizing the Gemini Flash pipeline. She significantly improved performance by fine-tuning API limits, adding error handling, and leveraging multithreading. She was dependable in executing scoped tasks, communicated clearly, and collaborated well across teams. Her work built a strong foundation for future scaling and demonstrated solid technical capabilities.

⸻

9. STRENGTHS
	•	Strong initiative in owning and executing her assigned project
	•	Quick learner when working with new modeling methodologies and tools
	•	Resolved technical issues independently, including API optimization and GCP blockers
	•	Excellent collaborator with clear and timely communication
	•	Dependable in delivering results with minimal supervision

⸻

10. AREAS FOR IMPROVEMENT

Christine is still developing her understanding of some foundational RAP modeling concepts — especially around discrete-time survival modeling, why we expand datasets, and how to structure and validate cohorts correctly across train/test/validation splits. She would benefit from thinking more critically about the modeling process — for example, exploring different time windows for clinical notes, validating query logic, or suggesting alternative feature engineering strategies. These areas will help her connect the dots better and contribute more strategically in future roles.

# Define thresholds
short_los_threshold = 10
long_los_threshold = 20

# Create flags
df_clean['short_stay_flag'] = df_clean['length_of_stay'] <= short_los_threshold
df_clean['long_stay_flag'] = df_clean['length_of_stay'] >= long_los_threshold

# Aggregate cumulative % of long and short stays per decile
los_percent_summary = df_clean.groupby("risk_decile").agg(
    total=('length_of_stay', 'count'),
    long_stay_pct=('long_stay_flag', 'mean'),
    short_stay_pct=('short_stay_flag', 'mean')
).reset_index()

# Convert to percentages
los_percent_summary['long_stay_pct'] *= 100
los_percent_summary['short_stay_pct'] *= 100



import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(14, 6))

# Plot Long Stay %
plt.subplot(1, 2, 1)
sns.barplot(data=los_percent_summary, x='risk_decile', y='long_stay_pct', palette='Reds')
plt.title(f'Cumulative % of LOS ≥ {long_los_threshold} Days by Risk Decile')
plt.ylabel('% of Long Stays')
plt.xlabel('Risk Decile')

# Plot Short Stay %
plt.subplot(1, 2, 2)
sns.barplot(data=los_percent_summary, x='risk_decile', y='short_stay_pct', palette='Blues')
plt.title(f'Cumulative % of LOS ≤ {short_los_threshold} Days by Risk Decile')
plt.ylabel('% of Short Stays')
plt.xlabel('Risk Decile')

plt.tight_layout()
plt.show()




import pandas as pd
import numpy as np

# Ensure 'length_of_stay' is numeric
df_clean['length_of_stay'] = pd.to_numeric(df_clean['length_of_stay'], errors='coerce')

# Create SNF Risk Score Deciles (if not already created)
df_clean["risk_decile"] = pd.qcut(df_clean["snf_score_new"], q=10, labels=[f'D{i+1}' for i in range(10)])

# Define stay flags
df_clean['short_stay_flag'] = df_clean['length_of_stay'] <= 10
df_clean['long_stay_flag'] = df_clean['length_of_stay'] >= 20

# Group by decile and compute total + % of short and long stays
los_percent_summary = df_clean.groupby("risk_decile").agg(
    total=('length_of_stay', 'count'),
    long_stay_pct=('long_stay_flag', 'mean'),
    short_stay_pct=('short_stay_flag', 'mean')
).reset_index()

# Convert to percentages
los_percent_summary['long_stay_pct'] = (los_percent_summary['long_stay_pct'] * 100).round(1)
los_percent_summary['short_stay_pct'] = (los_percent_summary['short_stay_pct'] * 100).round(1)

# Display the summary
print(los_percent_summary)

# Optional: Save to Excel
los_percent_summary.to_excel("los_cumulative_pct_by_decile.xlsx", index=False)




### 0617

import pandas as pd

def get_metrics_grid(df, score_col='rap_score', los_col='snf_los',
                     los_thresholds=range(7, 21), score_cutoffs=[0.3, 0.4, 0.5, 0.6, 0.7]):
    """
    Computes classification metrics (TP, FP, FN, TN, Sensitivity, Specificity, PPV, NPV, Accuracy, Lift)
    for each combination of LOS threshold and score cutoff.

    Parameters:
    - df: DataFrame
    - score_col: Column with prediction score
    - los_col: Column with SNF LOS
    - los_thresholds: List or range of LOS thresholds to evaluate
    - score_cutoffs: List of score cutoffs to evaluate

    Returns:
    - DataFrame with all metrics for each LOS threshold and cutoff
    """
    results = []

    for los_thresh in los_thresholds:
        df['y_true'] = (df[los_col] >= los_thresh).astype(int)

        for cutoff in score_cutoffs:
            df['y_pred'] = (df[score_col] >= cutoff).astype(int)

            tp = ((df['y_pred'] == 1) & (df['y_true'] == 1)).sum()
            tn = ((df['y_pred'] == 0) & (df['y_true'] == 0)).sum()
            fp = ((df['y_pred'] == 1) & (df['y_true'] == 0)).sum()
            fn = ((df['y_pred'] == 0) & (df['y_true'] == 1)).sum()

            sensitivity = round(tp / (tp + fn), 2) if (tp + fn) else None
            specificity = round(tn / (tn + fp), 2) if (tn + fp) else None
            ppv = round(tp / (tp + fp), 2) if (tp + fp) else None
            npv = round(tn / (tn + fn), 2) if (tn + fn) else None
            accuracy = round((tp + tn) / (tp + tn + fp + fn), 2)
            lift = round((tp / (tp + fp)) / ((tp + fn) / (tp + tn + fp + fn)), 2) if (tp + fp) and (tp + fn) else None

            results.append({
                'LOS_Threshold': los_thresh,
                'Score_Cutoff': cutoff,
                'TP': tp,
                'FP': fp,
                'FN': fn,
                'TN': tn,
                'Sensitivity': sensitivity,
                'Specificity': specificity,
                'PPV': ppv,
                'NPV': npv,
                'Accuracy': accuracy,
                'Lift': lift
            })

    return pd.DataFrame(results)
    
metrics_grid_df = get_metrics_grid(
    df,
    score_col='rap_score',
    los_col='snf_los',
    los_thresholds=range(7, 21),
    score_cutoffs=[0.3, 0.4, 0.5, 0.6, 0.7]
)

## 0617 graphs

import matplotlib.pyplot as plt
import seaborn as sns

def plot_sensitivity_specificity(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['Sensitivity'], marker='o', label='Sensitivity')
        plt.plot(data['Score_Cutoff'], data['Specificity'], marker='o', label='Specificity')
        plt.title(f'Sensitivity vs. Specificity for LOS ≥ {threshold} Days')
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel('Metric Value')
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()
        plt.show()
        
        
def plot_ppv_npv_accuracy(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['PPV'], marker='o', label='PPV')
        plt.plot(data['Score_Cutoff'], data['NPV'], marker='o', label='NPV')
        plt.plot(data['Score_Cutoff'], data['Accuracy'], marker='o', label='Accuracy')
        plt.title(f'PPV, NPV, Accuracy for LOS ≥ {threshold} Days')
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel('Metric Value')
        plt.ylim(0, 1)
        plt.grid(True)
        plt.legend()
        plt.show()
        
def plot_lift(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['Lift'], marker='o', label='Lift', color='purple')
        plt.title(f'Lift vs. Score Cutoff for LOS ≥ {threshold} Days')
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel('Lift')
        plt.grid(True)
        plt.legend()
        plt.show()
        
        
plot_sensitivity_specificity(metrics_grid_df)
plot_ppv_npv_accuracy(metrics_grid_df)
plot_lift(metrics_grid_df)

# visualize cutoff 

# Add Youden’s J to existing metrics grid
metrics_grid_df['Youdens_J'] = metrics_grid_df['Sensitivity'] + metrics_grid_df['Specificity'] - 1

best_cutoffs = (
    metrics_grid_df
    .sort_values(['LOS_Threshold', 'Youdens_J'], ascending=[True, False])
    .groupby('LOS_Threshold')
    .head(1)
    .reset_index(drop=True)
)

print(best_cutoffs)

import matplotlib.pyplot as plt

def plot_youden(metrics_df, los_thresholds=[7, 10, 14]):
    for threshold in los_thresholds:
        data = metrics_df[metrics_df['LOS_Threshold'] == threshold]

        plt.figure(figsize=(10, 5))
        plt.plot(data['Score_Cutoff'], data['Youdens_J'], marker='o', label="Youden's J")
        plt.title(f"Youden’s J vs Score Cutoff for LOS ≥ {threshold} Days")
        plt.xlabel('RAP Score Cutoff')
        plt.ylabel("Youden's J")
        plt.grid(True)
        plt.legend()
        plt.show()
        
plot_youden(metrics_grid_df)



def get_score_decile_cutoffs(df, score_col='rap_score'):
    """
    Returns the cutoff values for each decile of the score.
    Shows min/max score within each decile.
    """
    df = df.copy()
    df['decile'] = pd.qcut(df[score_col], 10, labels=False) + 1  # 1 = lowest, 10 = highest

    decile_summary = (
        df.groupby('decile')[score_col]
        .agg(['min', 'max'])
        .rename(columns={'min': 'score_min', 'max': 'score_max'})
        .reset_index()
    )

    return decile_summary

decile_cutoffs = get_score_decile_cutoffs(df, score_col='rap_score')
print(decile_cutoffs)


######## 06/24

import pandas as pd
import matplotlib.pyplot as plt

# Assuming your DataFrame is named df
# df = pd.read_csv("your_file.csv")  # Or however you're loading it

# Convert to datetime
df['score_eff_dt'] = pd.to_datetime(df['score_eff_dt'])
df['admit_dt'] = pd.to_datetime(df['admit_dt'])

# Calculate days between score and admit
df['days_before_admit'] = (df['admit_dt'] - df['score_eff_dt']).dt.days

# Basic statistics
print("Summary statistics:")
print(df['days_before_admit'].describe())

# Distribution plot
plt.figure(figsize=(10, 6))
plt.hist(df['days_before_admit'], bins=30, edgecolor='black')
plt.title('Distribution of Days Between Score and Admit Date')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Number of Patients')
plt.grid(True)
plt.show()



### 0625

import pandas as pd
import matplotlib.pyplot as plt

# Assume df['days_before_admit'] is already created

plt.figure(figsize=(10, 6))

# Plot histogram as percentages
counts, bins, patches = plt.hist(df['days_before_admit'], bins=30, edgecolor='black', density=True)

# Convert y-axis to percentage
plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y * 100:.1f}%'))

plt.title('Distribution of Days Between Score and Admit Date (as %)')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Percentage of Patients')
plt.xlim(-10, 20)  # Focus on range of interest
plt.grid(True)
plt.show()

#### 0626

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Assume df['days_before_admit'] already exists

# Define bins (customize as needed)
bins = np.arange(-10, 21, 2)  # bins from -10 to 20 with step size 2

# Bin the data
counts, bin_edges = np.histogram(df['days_before_admit'], bins=bins)

# Convert counts to percentages
percentages = counts / counts.sum() * 100

# Midpoints for plotting
bin_midpoints = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot
plt.figure(figsize=(10, 6))
plt.bar(bin_midpoints, percentages, width=1.8, edgecolor='black')

plt.title('Percentage of Patients by Days Between Score and Admit Date')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Percentage of Patients')
plt.xticks(bin_edges)
plt.grid(True)
plt.show()



#### 0628
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Assume df['days_before_admit'] already exists

# Define bins (customize as needed)
bins = np.arange(-10, 21, 2)  # from -10 to 20 days, 2-day width

# Create histogram
counts, bin_edges = np.histogram(df['days_before_admit'], bins=bins)
bin_midpoints = (bin_edges[:-1] + bin_edges[1:]) / 2

# Plot
plt.figure(figsize=(10, 6))
bars = plt.bar(bin_midpoints, counts, width=1.8, edgecolor='black', color='skyblue')

# Add value labels on top of each bar
for bar in bars:
    height = bar.get_height()
    if height > 0:
        plt.text(bar.get_x() + bar.get_width()/2, height + 500, f'{height:,}', 
                 ha='center', va='bottom', fontsize=9)

plt.title('Number of Patients by Days Between Score and Admit Date')
plt.xlabel('Days Before Admit Date (score_eff_dt - admit_dt)')
plt.ylabel('Number of Patients')
plt.xticks(bin_edges)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

import pandas as pd

# Rename 'rap_score' to 'snf_score'
df.rename(columns={'rap_score': 'snf_score'}, inplace=True)

# Ensure dates are in datetime format
df['admit_date'] = pd.to_datetime(df['admit_date'])
df['discharge_date'] = pd.to_datetime(df['discharge_date'])

# Compute LOS as (discharge - admit + 1)
df['los'] = (df['discharge_date'] - df['admit_date']).dt.days + 1

####0626

import matplotlib.pyplot as plt
import numpy as np

# Define bin edges manually from -35 to +5 (every 1 day)
bin_edges = np.arange(-35, 6, 1)

# Plot histogram as percentages
plt.figure(figsize=(12, 6))
n, bins, patches = plt.hist(
    filtered_df['days_before_admit'],
    bins=bin_edges,
    edgecolor='black',
    color='skyblue',
    density=True
)

# Convert frequencies to percentages
percentages = n * 100
for patch, pct in zip(patches, percentages):
    patch.set_height(pct)

# Vertical line at day 0
plt.axvline(x=0, color='red', linestyle='--', label='Admit Date (0 days)')

# Axis labels and title
plt.title('Percentage Distribution of Days (Score Eff Date vs Admit Date)', fontsize=14)
plt.xlabel('Days Before Admit (Positive = Scored Before Admission)', fontsize=12)
plt.ylabel('Percentage of Members (%)', fontsize=12)
plt.xticks(np.arange(-35, 6, 5))  # Clean x-axis ticks
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()




#### 0711

df = client.query(sql).result().to_dataframe(progress_bar_type='tqdm')

from google.cloud import bigquery
from google.cloud import bigquery_storage
from google.auth import default

credentials, project_id = default()
bq_client = bigquery.Client(credentials=credentials, project=project_id)
bq_storage_client = bigquery_storage.BigQueryReadClient(credentials=credentials)

query = """SELECT * FROM `your_project.your_dataset.your_table`"""  # Your actual query
query_job = bq_client.query(query)

# Stream efficiently using BigQuery Storage API
df = query_job.result().to_dataframe(bqstorage_client=bq_storage_client)


### added progress bar 


from google.cloud import bigquery
from google.cloud import bigquery_storage_v1
from google.auth import default
from tqdm import tqdm
import pandas as pd

credentials, project_id = default()
bq_client = bigquery.Client(credentials=credentials, project=project_id)
bq_storage_client = bigquery_storage_v1.BigQueryReadClient(credentials=credentials)

query = """SELECT * FROM `your_project.your_dataset.your_table`"""
query_job = bq_client.query(query)
query_job.result()  # Wait for job to finish

# Get reference to destination table
destination = query_job.destination
table_ref = destination.to_bqstorage()

# Create read session with parallel streams
session = bq_storage_client.create_read_session(
    parent=f"projects/{project_id}",
    read_session=bigquery_storage_v1.types.ReadSession(
        table=table_ref,
        data_format=bigquery_storage_v1.types.DataFormat.ARROW,
    ),
    max_stream_count=10,  # Controls parallelism; adjust for your machine
)

# Monitor progress across streams
dfs = []
for stream in tqdm(session.streams, desc="Downloading streams"):
    reader = bq_storage_client.read_rows(stream.name)
    dfs.append(reader.to_dataframe())

# Concatenate all partitions
df = pd.concat(dfs, ignore_index=True)




#### 0711


import pandas as pd
import numpy as np

def get_metrics_by_percentiles(df, score_col='rap_score', los_col='snf_los', los_threshold=10, percentiles=[5, 10, 15, 20, 25]):
    results = []

    for perc in percentiles:
        score_cutoff = np.percentile(df[score_col], perc)
        y_true = (df[los_col] <= los_threshold).astype(int)
        y_pred = (df[score_col] <= score_cutoff).astype(int)  # "low" scores for short LOS

        tp = ((y_true == 1) & (y_pred == 1)).sum()
        tn = ((y_true == 0) & (y_pred == 0)).sum()
        fp = ((y_true == 0) & (y_pred == 1)).sum()
        fn = ((y_true == 1) & (y_pred == 0)).sum()

        sensitivity = round(tp / (tp + fn), 2) if (tp + fn) else None
        specificity = round(tn / (tn + fp), 2) if (tn + fp) else None
        ppv = round(tp / (tp + fp), 2) if (tp + fp) else None
        npv = round(tn / (tn + fn), 2) if (tn + fn) else None
        accuracy = round((tp + tn) / (tp + tn + fp + fn), 2)
        lift = round((ppv / ((tp + fp) / len(df))), 2) if (tp + fp) else None
        identified = round(((tp + fp) / len(df)) * 100, 2)

        results.append({
            'Percentile': f'Top {perc}%',
            'Score Cutoff': round(score_cutoff, 2),
            'Sensitivity': sensitivity,
            'Specificity': specificity,
            'PPV': ppv,
            'NPV': npv,
            'Accuracy': accuracy,
            'Lift': lift,
            '% Identified': identified
        })

    return pd.DataFrame(results)
    
    
### grpah

import pandas as pd
import matplotlib.pyplot as plt

# Manually enter the data
data = {
    'RAP Score Cutoff': [22.05, 24.67, 27.68, 31.48, 36.03, 41.89],
    'Sensitivity': [0.37, 0.32, 0.27, 0.21, 0.16, 0.11],
    'Specificity': [0.66, 0.71, 0.76, 0.81, 0.86, 0.91],
    'PPV': [0.38, 0.38, 0.38, 0.38, 0.38, 0.39],
    'Accuracy': [0.56, 0.57, 0.58, 0.60, 0.61, 0.62]
}

df = pd.DataFrame(data)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(df['RAP Score Cutoff'], df['Sensitivity'], marker='o', label='Sensitivity')
plt.plot(df['RAP Score Cutoff'], df['Specificity'], marker='o', label='Specificity')
plt.plot(df['RAP Score Cutoff'], df['PPV'], marker='o', label='PPV')
plt.plot(df['RAP Score Cutoff'], df['Accuracy'], marker='o', label='Accuracy')

# Add vertical threshold line at Top 20% (RAP Score ~36.03)
threshold = 36.03
plt.axvline(x=threshold, color='red', linestyle='--', linewidth=1.5, label='Top 20% Threshold')
plt.text(threshold + 0.3, 0.45, f'Top 20%\n({threshold})', color='red', fontsize=9)

# Labels and formatting
plt.xlabel('RAP Score Cutoff')
plt.ylabel('Metric Value')
plt.title('Evaluating RAP Score for Predicting Long SNF Stays (LOS ≥ 20 Days)')
plt.ylim(0, 1)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()



-- Simulate table_a with duplicates and NULLs
WITH table_a AS (
  SELECT 1 AS individual_id UNION ALL
  SELECT 1 UNION ALL
  SELECT 2 UNION ALL
  SELECT NULL
),

-- Simulate table_b with duplicates and NULLs
table_b AS (
  SELECT 2 AS individual_id UNION ALL
  SELECT 3 UNION ALL
  SELECT 3 UNION ALL
  SELECT NULL
),

-- Step 1: LEFT JOIN table_a to table_b
cte_c AS (
  SELECT a.individual_id
  FROM table_a a
  LEFT JOIN table_b b
    ON a.individual_id = b.individual_id
)

-- Step 2: LEFT JOIN cte_c to table_a again and check for missing matches
SELECT c.individual_id
FROM cte_c c
LEFT JOIN table_a d
  ON c.individual_id = d.individual_id
WHERE d.individual_id IS NULL;





6. GOALS

Christine completed the key objectives laid out for her internship, including comparative analysis of RAP models, enhancing the Gemini Flash pipeline, and retraining commercial models. She showed solid follow-through on assigned tasks and was able to deliver working outputs despite early infrastructure setbacks. She successfully met her goals, though there is still room to deepen exploration of advanced modeling approaches and data strategies.

⸻

7. HEART AT WORK BEHAVIORS

Christine demonstrated strong collaboration with teammates and cross-functional groups, especially during the initial weeks when GCP issues delayed progress. She stayed engaged, took feedback well, and contributed to improving team workflows. Her willingness to step up and communicate across teams reflects the values of joining forces, rising to the challenge, and creating simplicity.

⸻

8. OVERALL PERFORMANCE

Christine made meaningful progress in her project, particularly in improving pipeline efficiency and retraining models. She displayed good ownership of her work and adapted well when facing technical blockers. While she completed her goals successfully, there’s potential to elevate her impact by proactively exploring alternate modeling approaches and thinking more strategically about data and feature design.

⸻

9. STRENGTHS
	•	Strong debugging and optimization skills
	•	Good collaboration and follow-up with platform teams
	•	Reliable in executing well-defined tasks
	•	Fast learner when working with new tools and ML pipelines

⸻

10. AREAS FOR IMPROVEMENT

Christine would benefit from developing a stronger modeling mindset—thinking more critically about how input features (like clinical notes) are selected, engineered, and tuned for performance. Exploring different modeling strategies, prompt enhancements, and approaches beyond the existing pipeline would help strengthen her contributions in future roles.


### more human way
6. GOALS

Christine did a great job completing the goals we set at the start of her internship. Despite some early delays due to GCP access issues, she stayed on track and delivered solid work — including improving the Gemini Flash pipeline, retraining both Medicare and Commercial models, and comparing their performance. I do think there’s still room to explore more creative modeling strategies, but overall, she met her objectives well.

⸻

7. HEART AT WORK BEHAVIORS

Christine showed strong collaboration throughout her internship, especially during the early weeks when platform issues slowed things down. She worked closely with our team, stayed positive, and was proactive in reaching out to others to resolve blockers. Her willingness to adapt, listen, and learn from different perspectives really aligned well with our team’s culture and values.

⸻

8. OVERALL PERFORMANCE

Overall, Christine performed well given the challenges. She was able to independently improve pipeline efficiency, retrain models, and contribute to key pieces of work. While she executed her tasks well, I would have liked to see more curiosity around experimenting with new ideas or asking “what else can we try?” from a modeling perspective. Still, she showed a solid foundation and great potential to grow with more time and experience.

⸻

9. STRENGTHS
	•	Great at following through on tasks and delivering results
	•	Strong at troubleshooting and optimizing code
	•	Communicates well with team members and collaborates effectively
	•	Picks up new tools and workflows quickly

⸻

10. AREAS FOR IMPROVEMENT

Christine could grow by thinking more critically about modeling choices and experimenting beyond the current setup. For example, trying different time windows for notes, playing with prompt tuning, or suggesting new features to test. With a bit more time and confidence, I think she’ll get there.

##### 0808

6. GOALS

Christine successfully completed all key goals of her internship. She gained a strong understanding of the RAP model pipelines, became familiar with the codebase, and retrained both the Medicare and Commercial models by integrating clinical notes features to improve performance. She also conducted a detailed comparative analysis to assess the impact of different features and modeling strategies. Despite early infrastructure issues, she stayed focused and delivered on time.

⸻

7. HEART AT WORK BEHAVIORS

Christine demonstrated excellent collaboration and adaptability throughout her internship. She proactively worked with cross-functional teams, especially during the initial weeks when GCP issues delayed access. She consistently took initiative, communicated clearly, and supported others — all while contributing to shared goals. Her positive attitude and willingness to take on challenges were a great fit for our team culture.

⸻

8. OVERALL PERFORMANCE

Overall, Christine made strong progress in her work. She independently improved the Gemini Flash pipeline, increasing processing speed by nearly 20x through multithreading and error handling. She followed through on all deliverables, engaged actively in discussions, and made meaningful contributions to model development and evaluation. She was dependable, thoughtful, and eager to learn.

⸻

9. STRENGTHS
	•	Took ownership of technical tasks and delivered consistently
	•	Improved pipeline efficiency and robustness significantly
	•	Strong collaboration and communication with teammates and platform teams
	•	Quick learner and adaptable to new tools and challenges
	•	Reliable in executing tasks with minimal guidance

⸻

10. AREAS FOR IMPROVEMENT

Christine would benefit from deepening her understanding of modeling methodology — particularly around discrete-time survival models, why dataset expansion is needed, and how to validate data structure and cohort logic. She could also grow by exploring strategies beyond the current pipeline — such as experimenting with different time windows for clinical note features, tuning LLM prompts, or proposing new features to test. These steps would help her build a stronger modeling mindset and contribute more strategically in future roles.


