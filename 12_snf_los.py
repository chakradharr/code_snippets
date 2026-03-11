Slide 1 — Program Overview Title: ER Diversion Initiative

Objective Reduce ER utilization and downstream inpatient admissions by
proactively engaging high-utilizing members and guiding them to
appropriate care settings.

Target Population Medicare & DSNP members with ≥4 ER visits in the past
6 months.

Program Geography Great Lakes market (Northern IL, Michigan,
Indianapolis, Wisconsin).

Slide 2 — Operational Workflow

Identification and Outreach Process 1. Members identified based on ≥4 ER
visits in prior 6 months. 2. Identified members recorded as targeted. 3.
Care manager reviews targeted members. 4. Care manager attempts outreach
and engagement.

Operational Constraint Only one care manager assigned to the pilot.
Engagement limited by CM capacity.

Program Funnel Identified / Targeted: 21,705 members (100%) Engaged: 737
members (3.3%)

Slide 3 — Data and Evaluation Challenges

Retrospective Reconstruction Issue

Operational identification used real-time hybrid data sources: - Daily
claims (recent 0–3 months) - Medical case insights (months 3–6)

Retrospective evaluation uses fully adjudicated claims.

As a result: - Some targeted members appear to have <4 ER visits
retrospectively. - Differences arise due to claims lag and data
reconciliation.

Slide 4 — Analytic Cohort Refinement

Ensuring Consistent Eligibility Definition

To align treatment and control cohorts: - Treatment cohort restricted to
members with ER ≥4 using adjudicated claims. - Approximately 65% of
targeted members meet this threshold retrospectively.

Purpose: - Reduce eligibility misclassification. - Ensure comparability
between treatment and control groups.

Slide 5 — Evaluation Framework

Because engagement was limited by CM capacity, two complementary
analyses were conducted.

Primary Analysis — Engagement Effect Compare: Engaged members vs
Targeted but Not Engaged members.

Purpose: Evaluate the impact of care manager engagement on utilization
outcomes.

Secondary Analysis — Program Availability (Intent-to-Treat) Compare:
Targeted members vs National Medicare sample with ER ≥4.

Purpose: Evaluate the impact of program rollout in the market.

Slide 6 — Methodology

Risk Adjustment and Matching

Baseline differences between cohorts addressed using: - Variable
selection from baseline characteristics - Propensity score modeling -
Overlap weighting / matching

Goal: Ensure comparable baseline characteristics between treatment and
control groups.

Slide 7 — Parallel Trends Assessment

Parallel trends evaluated using monthly ER utilization in the 6 months
prior to index date.

Observation: Pre-period trends between engaged and non-engaged members
were not fully parallel.

Reason: Engagement may correlate with higher baseline risk and
operational outreach prioritization.

Implication: Engagement analysis interpreted with caution.

Slide 8 — Primary Analysis Results

Engagement Effect

Outcome measures: - ER utilization (PMPM) - IP admissions - Total
medical costs

Key observations: - No statistically significant reduction in ER
utilization. - Directional reduction observed in inpatient admissions. -
Total cost differences not statistically significant.

Slide 9 — Secondary Analysis Results

Program Availability (Intent-to-Treat)

Comparison: Targeted members vs National ER ≥4 control group.

Purpose: Estimate impact of program availability at market level.

Results: - No significant difference in ER utilization. - Directional
trends consistent with primary analysis.

Slide 10 — Interpretation

Key Takeaways

1.  Engagement rate limited by care manager capacity.
2.  Operational identification differs from retrospective claims
    reconstruction.
3.  Engagement analysis suggests potential downstream IP utilization
    reduction.
4.  Overall program impact difficult to detect due to low engagement
    rate.

Slide 11 — Operational Implications

Program Improvement Opportunities

-   Expand care manager capacity to increase engagement.
-   Automate outreach workflows.
-   Improve real-time data integration for identification.

Higher engagement may improve measurable program impact.

Slide 12 — Summary

-   Program successfully identified high ER utilizers.
-   Engagement limited by operational capacity.
-   Analyses conducted to evaluate both engagement impact and program
    availability impact.
-   Results provide directional insights for program scaling.













I have a dataset where each row represents a monthly cohort of members for a program evaluation. The dataset already contains these columns:

- month
- expected_rr
- observed_rr
- test_rr
- holdout_rr
- expected_rr_test
- expected_rr_holdout
- observed_rr_test
- observed_rr_holdout

I want to validate whether the risk-adjusted readmission model signal aligns with the program impact estimated by the evaluation team.

Please generate Python code that does the following:

1. Create two new columns:
   - true_impact = holdout_rr - test_rr
   - proxy_impact = expected_rr - observed_rr

2. Compute the Pearson correlation between true_impact and proxy_impact.

3. Run a simple linear regression:
   true_impact = intercept + slope * proxy_impact

4. Print:
   - correlation coefficient
   - regression intercept
   - regression slope
   - R-squared

5. Create a scatter plot with:
   - x-axis = proxy_impact
   - y-axis = true_impact
   - regression line overlaid
   - each point labeled by month if possible

6. Add a short printed interpretation explaining whether the proxy signal appears to align with the evaluation-based program impact.

Use pandas, matplotlib, and either statsmodels or scikit-learn.

Assume the dataframe is already loaded as df.

Please write clean, runnable Python code with comments.