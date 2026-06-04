RAP Acute + SNF Prioritization Simulator

Project Context and Agent Handoff

⸻

Overview

This project is being developed for the Medicare Readmission Avoidance Program (RAP) at Aetna/CVS Health.

The objective is to build a simulation tool that estimates the operational and financial impact of changing Acute RAP and SNF RAP prioritization strategies.

The simulator will help leadership evaluate tradeoffs between:

* Acute RAP volume
* SNF RAP volume
* SHJ release volume
* Care Management capacity
* Member engagement
* Expected readmission reduction
* Estimated savings / ROI

The final deliverable should be a local standalone simulator that can be opened directly in a browser without requiring any web server.

⸻

Current RAP Programs

Acute RAP

The Acute RAP model is triggered whenever an Acute Inpatient authorization is received.

Current identification logic:

identified_flag = (
    rap_score >= acute_threshold
) & (
    days_since_discharge.between(0, 4)
)

Current threshold is approximately:

12.5%

This identifies roughly the top 30% highest-risk members.

⸻

SNF RAP

The SNF RAP model is triggered whenever a Skilled Nursing Facility (SNF) authorization is received.

Current identification logic:

identified_flag = (
    snf_rap_score >= snf_threshold
) & (
    days_since_discharge.between(0, 4)
)

Current threshold is approximately:

12.5%

This identifies approximately 5-7% of SNF members.

⸻

Business Problem

Both RAP programs can identify the same member.

Example:

March 1
Member admitted to Acute Inpatient
March 15
Discharged
March 16
Acute RAP identifies member
April 1
Member admitted to SNF
April 15
Discharged
April 16
SNF RAP identifies member

However, if an active RAP outreach/program card already exists from the Acute RAP identification, then the SNF identification may not create a new outreach opportunity.

Therefore:

Gross Identifications
≠
Net New Opportunities

The simulator must account for this overlap.

⸻

Leadership Question

Leadership wants to understand:

What happens to volume, case mix, engagement, and savings if we prioritize more SNF cases versus Acute cases?

Examples:

* Lower Acute threshold
* Lower SNF threshold
* Prioritize SNF cases in SHJ
* Reserve a minimum number of SNF cases each month
* Change case mix without increasing overall volume

⸻

Operational Workflow

The RAP team only performs identification.

The actual workflow is:

Model Scored Population
        ↓
Identification Logic Applied
        ↓
Cases Sent To SHJ / CEC
        ↓
SHJ Inclusion & Exclusion Rules
        ↓
Released To MedCompass
        ↓
Care Manager Capacity
        ↓
Targeted
        ↓
Engaged

⸻

SHJ Responsibilities

SHJ performs operational processing.

Examples:

Exclusions

* NME exclusions
* Contract exclusions
* Other operational exclusions

Inclusions

* Member eligibility
* Program eligibility
* Other operational checks

SHJ determines which cases are ultimately released to MedCompass.

⸻

Care Management Process

Released cases are sent to MedCompass.

Care Managers pick cases based on capacity.

Important:

Released
≠
Targeted

and

Targeted
≠
Engaged

Cases can remain available and be released again on subsequent days if capacity was unavailable.

⸻

Available Data Sources

1. Acute RAP Scored Population

Required fields:

member_id
admission_id
admit_dt
discharge_dt
score_dt
rap_score
days_since_discharge
readmit_30d_flag

⸻

2. SNF RAP Scored Population

Required fields:

member_id
admission_id
admit_dt
discharge_dt
score_dt
rap_score
days_since_discharge
readmit_30d_flag

⸻

3. SHJ / CEC Identification Table

This table records members identified by RAP and sent to SHJ.

Required fields:

member_id
event_id
identified_dt
program_type
source_model
sent_to_shj_flag
shj_eligible_flag
released_to_medcompass_flag
release_dt

⸻

4. MedCompass Program Card Table

Required fields:

member_id
program_card_id
program_type
program_start_dt
program_end_dt
targeted_flag
engaged_flag
engaged_dt

⸻

5. Readmission Outcome Table

Required fields:

member_id
event_id
index_discharge_dt
readmit_30d_flag
readmit_dt

⸻

SHJ Data Limitation

SHJ launched during mid-2025.

Therefore:

Full-year SHJ history is unavailable.

Only Q3-Q4 2025 are considered clean and stable.

⸻

Recommended Approach

Q3-Q4 2025

Use actual SHJ outcomes.

Observed Data

⸻

Jan-Jun 2025

Apply assumptions learned from Q3-Q4.

Estimated Data

⸻

Cohort Construction

Build one master scored cohort:

acute_scored_2025
UNION ALL
snf_scored_2025

Required standardized fields:

member_id
event_id
event_type
admit_dt
discharge_dt
score_dt
rap_score
days_since_discharge
readmit_30d_flag

⸻

Baseline Identification Logic

Current production simulation:

identified_flag = (
    rap_score >= threshold
) & (
    days_since_discharge.between(0,4)
)

⸻

Percentile-Based Framework

Instead of hardcoded thresholds, compute percentiles.

Acute:

acute_percentile

SNF:

snf_percentile

This allows simulation of:

Top 20%
Top 25%
Top 30%
Top 35%
Top 40%

without recalculating thresholds.

⸻

Overlap Suppression Logic

One of the most important components.

Members may appear in both Acute and SNF RAP.

Create episode logic:

member_id
ordered by score_dt

Rule:

If member already has active RAP outreach
within prior 30 days
→ Suppress new identification
Else
→ Count as net-new opportunity

Output metrics:

Gross Identifications
Overlap Suppressed
Net-New Identifications

⸻

SHJ Funnel Estimation

Using clean Q3-Q4 data estimate:

Acute Funnel:

Identified
→ SHJ Eligible
→ Released
→ Targeted
→ Engaged

SNF Funnel:

Identified
→ SHJ Eligible
→ Released
→ Targeted
→ Engaged

Estimate conversion rates separately.

⸻

Capacity Modeling

Version 1:

No explicit capacity constraints.

Use observed funnel rates.

⸻

Version 2:

Allow user input:

Monthly Capacity
Weekly Capacity
Targeted Capacity
Engagement Capacity

Support prioritization strategies:

Highest Score First
SNF First
Acute First
Highest Expected Savings
SNF Minimum Floor

⸻

Readmission Rate Estimation

Create percentile bands:

0-5%
5-10%
10-15%
...
95-100%

Calculate:

Observed Readmission Rate

for each band.

This allows cumulative risk estimation as thresholds move.

⸻

Savings Model

Default assumptions:

Intervention Effectiveness = 35%
Savings Per Avoided Readmission = $15,000

Formula:

estimated_savings =
engaged_cases
*
expected_readmission_rate
*
0.35
*
15000

⸻

Scenarios To Simulate

Baseline

Acute Top 30%
SNF Top 5%

⸻

Scenario A

Acute Top 30%
SNF Top 10%

⸻

Scenario B

Acute Top 25%
SNF Top 15%

⸻

Scenario C

Acute Top 20%
SNF Top 20%

⸻

Scenario D

SNF Floor Strategy
Minimum SNF Volume Per Month

⸻

Scenario E

SHJ Prioritizes SNF

When capacity is constrained:

SNF Wins
Acute Deferred

⸻

Simulator Outputs

For each scenario calculate:

Acute Identified
SNF Identified
Overlap Suppressed
Net-New Identified
SHJ Eligible
Released To MedCompass
Targeted
Engaged
Expected Readmission Rate
Avoided Readmissions
Estimated Savings
SNF Mix %

Also show:

Incremental Volume
Incremental Engagement
Incremental Savings
Change In SNF Mix

compared to baseline.

⸻

Recommended Technical Architecture

Backend

Python

Responsibilities:

Load Data
Construct Cohorts
Calculate Percentiles
Estimate SHJ Funnel
Run Scenario Grid
Calculate Savings
Export Results

⸻

Frontend

Single standalone HTML file.

No Flask.

No server.

No hosting.

Open directly in browser:

rap_prioritization_simulator.html

⸻

Recommended UI Controls

Acute Top % Slider
SNF Top % Slider
Prioritization Dropdown
SNF Floor Input
Capacity Input
Savings Per Readmission
Intervention Effectiveness

⸻

Recommended Visuals

KPI Cards

Identified
Targeted
Engaged
Savings

⸻

Funnel Chart

Identified
↓
SHJ Eligible
↓
Released
↓
Targeted
↓
Engaged
↓
Avoided Readmissions
↓
Savings

⸻

Scenario Comparison Table

Baseline versus selected scenario.

⸻

SNF Mix Chart

SNF Mix %
vs
Estimated Savings

⸻

Key Assumptions

Expose these assumptions directly in the simulator.

Observed SHJ Period = Q3-Q4 2025
Estimated Period = Jan-Jun 2025
Intervention Effectiveness = 35%
Savings Per Avoided Readmission = $15,000
Overlap Window = 30 Days
Separate Acute and SNF Funnel Rates

⸻

Important Caveats

1. SHJ data is only mature beginning in Q3-Q4 2025.
2. Early 2025 SHJ outcomes should be estimated.
3. Acute and SNF overlap must be suppressed.
4. Lower thresholds increase volume but reduce average risk.
5. Increased identification volume does not automatically create more engagement due to SHJ and CM capacity constraints.
6. Savings are estimated and not causal proof.
7. Actual ROI depends on intervention effectiveness and operational execution.

⸻

Final Deliverable

A standalone browser-based simulator:

rap_prioritization_simulator.html

generated by Python and capable of estimating:

* Acute/SNF case mix
* Overlap-adjusted identification volume
* SHJ release volume
* Targeted volume
* Engagement volume
* Expected readmission reduction
* Estimated savings
* Scenario comparison versus baseline












# Risk-Adjusted Readmission Model: Methodology and Implementation Context

## 1. Purpose of This Document

This document explains the design and methodology for building a **risk-adjusted 30-day readmission model** for **facility benchmarking**. It lays out:

- What we are trying to build
- Why we are building it
- How expected readmission probabilities are generated
- How yearly model training, calibration, and scoring should work
- Why prior-year reference rates are used
- Why calibration is required
- How to avoid data leakage
- How facility-level expected rates and observed-to-expected ratios should be calculated

The goal is to provide enough context for another analyst, data scientist, or AI coding agent to implement the framework correctly.

---

## 2. What We Are Trying to Do

We are building a **risk-adjusted readmission model** that predicts the probability that an inpatient admission will result in a **30-day readmission**.

The model is intended for **facility benchmarking**, not only member targeting.

The unit of analysis is:

> **Each inpatient admission, indexed at discharge date**

For every eligible inpatient discharge, the model should output:

```text
Expected 30-day readmission probability
```

At the facility level, these member/admission-level probabilities are aggregated to calculate:

```text
Expected readmissions = sum(predicted calibrated probabilities)
```

Then facility-level expected readmission rate is:

```text
Expected readmission rate = expected readmissions / number of eligible index admissions
```

And the observed-to-expected ratio is:

```text
O/E ratio = observed readmissions / expected readmissions
```

---

## 3. Why We Are Doing This

Raw readmission rates are not enough for fair facility comparison.

Example:

- Facility A may serve sicker members with more complex conditions.
- Facility B may serve relatively healthier members.
- Facility A may have a higher raw readmission rate, but that does not automatically mean Facility A is performing worse.

A risk-adjusted model helps answer:

> Given the clinical and utilization risk profile of the patients treated by this facility, how many readmissions would we have expected?

This enables fairer comparison across facilities.

The key business use cases are:

1. **Facility benchmarking**  
   Compare observed readmission performance against expected risk-adjusted performance.

2. **Performance monitoring**  
   Track whether facilities are performing better or worse than expected over time.

3. **Program and vendor evaluation support**  
   Use expected readmission rates as a risk-adjusted baseline for cohorts.

4. **Executive reporting**  
   Summarize which facilities have higher-than-expected or lower-than-expected readmissions.

---

## 4. Target Definition

The model target is:

```text
30-day readmission after inpatient discharge
```

The index date is:

```text
Inpatient discharge date
```

Each row in the modeling dataset should represent an eligible inpatient admission/discharge.

Important target-definition decisions should be documented separately, including:

- Whether readmission includes all-cause readmission
- Whether observation stays are included or excluded
- Whether planned readmissions are excluded
- Whether transfers are excluded
- Whether same-day returns are included
- Whether SNF-to-IP and IP-to-IP transitions are both included
- Whether mortality exclusions apply

For benchmarking, the denominator definition must remain consistent across years.

---

## 5. Feature Strategy

The model uses two broad types of features:

### 5.1 Member-Level / Admission-Level Risk Features

These may include:

- Demographics
- Diagnosis history
- Comorbidities
- Prior inpatient utilization
- Prior emergency room utilization
- Prior SNF utilization
- Claims-based clinical history
- Discharge disposition
- Length of stay
- Admission type
- Procedure history
- Medication or condition indicators, if available

These features should be calculated using information available before or at the index discharge date.

### 5.2 Historical Reference-Rate Features

The model will also use historical raw readmission rates by clinical groupings such as:

- DRG
- Diagnosis group
- Procedure group
- Other clinically meaningful groupings

Example features:

```text
drg_prior_year_readmission_rate
dx_group_prior_year_readmission_rate
procedure_group_prior_year_readmission_rate
```

These are not the target itself. They are historical baseline-risk features that help the model understand that some conditions or procedures have naturally higher readmission risk.

---

## 6. Why Use Prior-Year Reference Rates?

Reference-rate features must be calculated from a previous year to avoid outcome leakage.

For example, when training on 2023 admissions, the DRG/procedure/diagnosis-group reference rates should come from 2022.

Why?

If we use 2023 readmission rates as features while training on 2023 admissions, each admissionâs own outcome may indirectly contribute to the feature value. This creates leakage.

Bad design:

```text
Training cohort: 2023 admissions
Reference rates: 2023 DRG readmission rates
```

This is risky because 2023 outcomes are being used to create features for 2023 training rows.

Preferred design:

```text
Training cohort: 2023 admissions
Reference rates: 2022 DRG readmission rates
```

This better mimics real-world prospective scoring because only prior information is used.

---

## 7. Yearly Training and Scoring Framework

The framework uses a rolling-year design.

Rule:

> For a model trained on year Y, use reference-rate features from year Y-1. Use the trained model and calibration from year Y to score year Y+1.

Final recommended table:

| Scoring Year | Score Cohort | Model Trained On | Reference Rates Used as Features | Calibration Used | Output |
|---|---:|---:|---:|---|---|
| 2024 | 2024 admissions | 2023 | 2022 | 2023 OOF isotonic | Expected 2024 readmission probability |
| 2025 | 2025 admissions | 2024 | 2023 | 2024 OOF isotonic | Expected 2025 readmission probability |
| 2026 | 2026 admissions | 2025 | 2024 | 2025 OOF isotonic | Expected 2026 readmission probability |
| 2027 | 2027 admissions | 2026 | 2025 | 2026 OOF isotonic | Expected 2027 readmission probability |

Example for 2026 scoring:

```text
Score cohort: 2026 admissions
Model: trained on 2025 admissions
Reference-rate features: calculated from 2024 data
Calibration: isotonic calibrator fitted using 2025 out-of-fold predictions
Final output: calibrated expected 30-day readmission probability
```

---

## 8. Why Calibration Is Needed

Machine learning models such as XGBoost often rank members well but may not produce accurate probabilities.

Example:

| Raw Model Score | Actual Readmission Rate |
|---:|---:|
| 0.80 | 0.32 |
| 0.60 | 0.21 |
| 0.40 | 0.12 |

A raw model score of 0.80 does not necessarily mean the true probability is 80%.

For facility benchmarking, this is a major issue because expected readmissions are calculated as the sum of probabilities.

```text
Expected readmissions = sum(predicted probabilities)
```

If predicted probabilities are too high or too low, then:

- Expected counts will be wrong
- Expected rates will be wrong
- O/E ratios will be wrong
- Facility rankings may be misleading

Calibration converts raw model scores into better estimated probabilities.

---

## 9. Isotonic Regression Calibration

The planned calibration method is **isotonic regression**.

Isotonic regression learns a monotonic mapping:

```text
raw model score -> calibrated probability
```

It preserves the ordering of risk while correcting the probability scale.

Example mapping:

| Raw Score | Calibrated Probability |
|---:|---:|
| 0.90 | 0.42 |
| 0.75 | 0.30 |
| 0.50 | 0.16 |
| 0.25 | 0.06 |

This is useful because facility benchmarking requires probability accuracy, not just ranking accuracy.

---

## 10. Why Out-of-Fold Calibration Is Needed

Calibration should not be fitted using predictions from a model that was trained on the same rows.

Bad design:

```text
Train model on all 2023 admissions
Predict on same 2023 admissions
Fit isotonic calibrator using those same predictions
```

This can produce overly optimistic predictions because the model has already seen those rows.

Preferred design:

```text
Generate out-of-fold predictions
Fit isotonic calibrator on those out-of-fold predictions
```

Out-of-fold predictions mean each admission is predicted by a model that did not train on that admission.

This better simulates production scoring.

---

## 11. Quarterly 4-Fold Out-of-Fold Calibration Design

For each training year, use four quarter-based folds.

Example for 2023:

| Fold | Train Temporary Model On | Predict On |
|---|---|---|
| Fold 1 | Q2-Q4 2023 | Q1 2023 |
| Fold 2 | Q1, Q3, Q4 2023 | Q2 2023 |
| Fold 3 | Q1, Q2, Q4 2023 | Q3 2023 |
| Fold 4 | Q1-Q3 2023 | Q4 2023 |

This creates one out-of-fold prediction for every 2023 admission.

Final OOF calibration dataset:

| admission_id | discharge_quarter | raw_oof_prediction | actual_30_day_readmission |
|---|---|---:|---:|
| A | Q1 | 0.34 | 1 |
| B | Q2 | 0.12 | 0 |
| C | Q3 | 0.28 | 0 |
| D | Q4 | 0.47 | 1 |

Then fit isotonic regression:

```text
isotonic_2023.fit(raw_oof_prediction, actual_30_day_readmission)
```

This creates one final calibration object:

```text
isotonic_2023
```

---

## 12. Temporary Fold Models vs Final Production Model

For each training year, the pipeline creates:

### Temporary fold models

These are used only to generate OOF predictions for calibration.

Example for 2023:

```text
fold_model_2023_q1
fold_model_2023_q2
fold_model_2023_q3
fold_model_2023_q4
```

These models are not used for final scoring.

### Final production model

After OOF predictions and calibration are created, train one final model on all training-year data.

Example:

```text
final_model_2023 = train on all 2023 admissions
```

Final 2024 scoring uses:

```text
final_model_2023 + isotonic_2023
```

---

## 13. Example: 2024 Scoring

To score 2024 admissions:

### Step 1: Build 2022 reference rates

Calculate raw readmission rates from 2022 by:

- DRG
- diagnosis group
- procedure group
- other selected clinical groupings

These become features for 2023 training and 2024 scoring.

### Step 2: Train temporary fold models on 2023

Use quarter-based 4-fold training to generate OOF predictions for all 2023 admissions.

### Step 3: Fit isotonic calibrator

Fit:

```text
isotonic_2023.fit(oof_predictions_2023, actual_readmissions_2023)
```

### Step 4: Train final model on all 2023

Fit:

```text
final_model_2023.fit(all_2023_training_data)
```

### Step 5: Score 2024 admissions

For each 2024 admission:

```text
raw_score = final_model_2023.predict_proba(2024_features)
expected_probability = isotonic_2023.transform(raw_score)
```

The expected_probability is the final expected 30-day readmission probability.

---

## 14. Facility-Level Aggregation

Once every admission has a calibrated expected probability, aggregate to facility level.

For each facility:

```text
expected_readmissions = sum(expected_probability)
observed_readmissions = sum(actual_30_day_readmission)
index_admissions = count(eligible_admissions)
```

Then:

```text
expected_rate = expected_readmissions / index_admissions
observed_rate = observed_readmissions / index_admissions
OE_ratio = observed_readmissions / expected_readmissions
```

Example:

| Metric | Value |
|---|---:|
| Eligible index admissions | 1,000 |
| Observed readmissions | 140 |
| Sum of expected probabilities | 120 |
| Observed rate | 14.0% |
| Expected rate | 12.0% |
| O/E ratio | 1.17 |

Interpretation:

```text
The facility had 17% more readmissions than expected after risk adjustment.
```

---

## 15. Data Leakage Controls

Avoiding leakage is critical for benchmarking credibility.

### 15.1 Do not use same-year reference rates for training

Bad:

```text
Training year: 2023
Reference rates: 2023
```

Good:

```text
Training year: 2023
Reference rates: 2022
```

### 15.2 Do not calibrate on in-sample predictions

Bad:

```text
Train model on all 2023
Predict all 2023
Fit isotonic on those predictions
```

Good:

```text
Generate 2023 OOF predictions
Fit isotonic on OOF predictions
```

### 15.3 Do not use future outcome information

For 2024 scoring, do not use 2024 outcomes to build 2024 expected probabilities.

For 2026 live scoring, do not use 2026 readmission outcomes because they are not fully known yet.

### 15.4 Use only features available at discharge

Any feature used for an index admission should be available on or before the discharge date.

Avoid features that accidentally include post-discharge events within the 30-day outcome window.

### 15.5 Be careful with facility-level features

If the goal is facility benchmarking, avoid using facility ID or facility historical readmission rate as a direct model feature unless explicitly justified.

Reason:

The model may adjust away the facility effect you are trying to measure.

For benchmarking, the model should primarily adjust for patient clinical risk, not excuse facility-level performance differences.

---

## 16. Handling Sparse Reference-Rate Groups

Raw DRG/procedure/diagnosis rates can be unstable for low-volume groups.

Example:

```text
1 readmission out of 2 admissions = 50% raw rate
```

This may be too noisy.

Recommended approach:

- Apply minimum volume thresholds
- Use hierarchical fallback logic
- Use smoothing/shrinkage toward the global rate

Example shrinkage formula:

```text
smoothed_rate = (group_readmits + k * global_rate) / (group_admissions + k)
```

Where:

- group_readmits = readmissions in the DRG/procedure/dx group
- group_admissions = eligible admissions in that group
- global_rate = overall readmission rate
- k = smoothing strength

If group volume is very small, use a broader grouping fallback.

Example fallback hierarchy:

```text
DRG -> diagnosis category -> service line -> global rate
```

---

## 17. Recommended Artifact Versioning

For each scoring year, save all artifacts needed to reproduce scores.

Example for 2024 scoring:

```text
final_model_2023.pkl
isotonic_2023.pkl
reference_rates_2022.parquet
feature_logic_v2023.sql
cohort_definition_v2023.md
model_config_v2023.json
```

Example for 2026 scoring:

```text
final_model_2025.pkl
isotonic_2025.pkl
reference_rates_2024.parquet
feature_logic_v2025.sql
cohort_definition_v2025.md
model_config_v2025.json
```

This is important because facility benchmarking reports must be reproducible.

If model artifacts are overwritten, historical expected rates may shift unexpectedly.

---

## 18. Prospective vs Retrospective Modes

There are two possible modes.

### 18.1 Production Prospective Mode

This is the preferred mode for official benchmarking.

For 2026 scoring, use:

```text
final_model_2025
isotonic_2025
reference_rates_2024
```

This reflects what was available before or during 2026 scoring.

### 18.2 Retrospective Research Mode

After 2026 outcomes fully mature, analysts may build a 2026-trained model and 2026 calibration object.

That can be useful for research, validation, or future model development.

However, retrospective models should not overwrite the original production expected probabilities used for official 2026 benchmarking.

---

## 19. Recommended Implementation Logic

For each training year Y:

1. Build training cohort from year Y admissions.
2. Build reference-rate features from year Y-1.
3. Create 4 quarter-based folds within year Y.
4. For each fold:
   - Train temporary model on other three quarters.
   - Predict raw probabilities on held-out quarter.
5. Combine all held-out predictions into one OOF prediction table.
6. Fit isotonic regression using OOF predictions and actual outcomes.
7. Train final production model on all year Y admissions.
8. Save final model, isotonic calibrator, reference tables, and feature logic.
9. Score year Y+1 admissions.
10. Apply isotonic calibration to raw predictions.
11. Aggregate expected probabilities to facility level.
12. Calculate observed rate, expected rate, and O/E ratio once outcomes mature.

---

## 20. Pseudocode

```python
for training_year in [2023, 2024, 2025, 2026]:
    scoring_year = training_year + 1
    reference_year = training_year - 1

    # 1. Build reference-rate features
    reference_rates = build_reference_rates(reference_year)

    # 2. Build training data
    train_df = build_training_dataset(
        admission_year=training_year,
        reference_rates=reference_rates
    )

    # 3. Generate OOF predictions by quarter
    oof_predictions = []

    for holdout_quarter in [1, 2, 3, 4]:
        fold_train = train_df[train_df.quarter != holdout_quarter]
        fold_holdout = train_df[train_df.quarter == holdout_quarter]

        fold_model = train_model(fold_train)
        fold_pred = fold_model.predict_proba(fold_holdout[features])[:, 1]

        oof_predictions.append({
            "admission_id": fold_holdout.admission_id,
            "raw_pred": fold_pred,
            "actual": fold_holdout.readmit_30_day
        })

    oof_df = concatenate(oof_predictions)

    # 4. Fit isotonic calibrator
    isotonic = fit_isotonic(
        x=oof_df.raw_pred,
        y=oof_df.actual
    )

    # 5. Train final production model on all training-year data
    final_model = train_model(train_df)

    # 6. Save artifacts
    save(final_model, f"final_model_{training_year}.pkl")
    save(isotonic, f"isotonic_{training_year}.pkl")
    save(reference_rates, f"reference_rates_{reference_year}.parquet")

    # 7. Score next year
    score_df = build_scoring_dataset(
        admission_year=scoring_year,
        reference_rates=reference_rates
    )

    raw_score = final_model.predict_proba(score_df[features])[:, 1]
    calibrated_score = isotonic.transform(raw_score)

    score_df["expected_readmission_probability"] = calibrated_score

    save(score_df, f"expected_scores_{scoring_year}.parquet")
```

---

## 21. Validation Checks

For each scoring year, evaluate:

### 21.1 Admission-level model performance

- AUC / C-statistic
- Average precision
- Brier score
- Calibration intercept
- Calibration slope
- Calibration plot
- Decile observed vs expected rates

### 21.2 Facility-level benchmarking stability

- Facility observed vs expected scatterplot
- O/E ratio distribution
- Confidence intervals around O/E
- Minimum volume thresholds
- Year-over-year facility rank stability
- Sensitivity to small facilities

### 21.3 Calibration quality

For deciles of calibrated risk:

```text
mean predicted probability vs actual readmission rate
```

The closer these are, the better the expected counts will be.

---

## 22. Important Design Decision: Facility Features

Because the goal is facility benchmarking, be cautious about including facility-level historical performance as a feature.

If we include facility ID or facility historical readmission rate, the model may learn that some facilities are historically high-risk and assign them higher expected rates. This can reduce their O/E ratio and make poor performance appear expected.

This may be acceptable for forecasting but can be problematic for accountability benchmarking.

Recommended default:

```text
Do not include facility ID or facility historical readmission rate in the core benchmarking model.
```

Instead, adjust primarily for patient clinical risk and admission characteristics.

---

## 23. Final Summary

We are building a rolling yearly risk-adjusted readmission benchmarking framework.

The model predicts 30-day readmission risk at the inpatient admission/discharge level.

For each scoring year:

- Train the model on the prior year.
- Use reference-rate features from one year before the training year.
- Use quarter-based OOF predictions from the training year to fit isotonic calibration.
- Train one final model on the full training year.
- Score the next year using the final model and final isotonic calibrator.
- Aggregate calibrated probabilities to facility level.
- Compare observed vs expected readmissions.

The core design principles are:

1. Avoid future data leakage.
2. Use prior-year reference rates.
3. Use OOF predictions for calibration.
4. Calibrate probabilities because expected counts depend on probability accuracy.
5. Save yearly frozen artifacts for reproducibility.
6. Aggregate member/admission-level expected probabilities to facility-level expected rates.

The final expected probability for an admission is:

```text
expected_probability = isotonic_Y(final_model_Y.predict_proba(features_with_reference_rates_Y_minus_1))
```

Where:

- Y = training year
- Y + 1 = scoring year
- Y - 1 = reference-rate year

Example for 2026:

```text
expected_probability_2026 = isotonic_2025(final_model_2025.predict_proba(features_using_2024_reference_rates))
```

This gives a leakage-aware, calibrated, reproducible expected readmission probability suitable for facility benchmarking.
