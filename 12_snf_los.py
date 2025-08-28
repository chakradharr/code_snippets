
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


