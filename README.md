# Program Impact Validation Using Risk-Adjusted Readmission Model

## Objective
The purpose of this analysis is to validate whether the **risk-adjusted readmission model** can provide a directional signal of program performance when a full program evaluation study is not yet available.

The NBA Call Pod team measures program impact using a **test vs holdout cohort evaluation**.  
The risk-adjusted model provides **expected readmission probabilities**, which can be compared with **observed readmission rates**.

This analysis compares:

1. **Traditional program impact** estimated by the NBA evaluation.
2. **Risk-adjusted program impact** estimated using expected vs observed readmission rates from the model.

---

## Dataset Structure

Each row in the dataset represents a **monthly cohort of members**.

| Column | Description |
|------|-------------|
| month | Month of the inpatient admission |
| expected_rr | Average predicted readmission probability from the model |
| observed_rr | Actual readmission rate in the cohort |
| test_rr | Observed readmission rate for program test cohort |
| holdout_rr | Observed readmission rate for holdout/control cohort |
| expected_rr_test | Predicted risk for test cohort |
| expected_rr_holdout | Predicted risk for holdout cohort |
| observed_rr_test | Actual readmission rate for test cohort |
| observed_rr_holdout | Actual readmission rate for holdout cohort |

---

## 1. Traditional Program Impact (NBA Evaluation)

Program impact is estimated by comparing readmission rates between test and holdout cohorts.

**Formula:**

Program Impact = Holdout RR âˆ’ Test RR

Example:

| Metric | Value |
|------|------|
Test Readmission Rate | 10.76% |
Holdout Readmission Rate | 11.52% |
Program Impact | **0.76 percentage points reduction** |

Interpretation:

Members in the program cohort experienced **0.76pp fewer readmissions** than the holdout cohort.

---

## 2. Risk-Adjusted Program Impact

The risk-adjusted readmission model estimates **expected readmission probability** based on patient characteristics.

### Baseline Risk Comparison

| Cohort | Expected RR |
|------|------|
Test | 10.50% |
Holdout | 10.53% |

Difference: **0.03pp**

This indicates the cohorts have **very similar baseline risk**.

---

### Observed vs Expected Performance

| Cohort | Observed RR | Expected RR | Difference |
|------|------|------|------|
Test | 10.76% | 10.50% | +0.26pp |
Holdout | 11.52% | 10.53% | +0.99pp |

---

### Risk-Adjusted Impact Calculation

Risk-adjusted impact is calculated as:

(HoldoutObserved âˆ’ HoldoutExpected) âˆ’ (TestObserved âˆ’ TestExpected)

Calculation:

(11.52 âˆ’ 10.53) âˆ’ (10.76 âˆ’ 10.50)

= 0.99 âˆ’ 0.26

= **0.73 percentage points**

---

## 3. Comparison of Both Methods

| Method | Estimated Impact |
|------|------|
Traditional Evaluation | 0.76pp |
Risk-Adjusted Model | 0.73pp |
Difference | 0.03pp |

Interpretation:

Both methods produce **nearly identical estimates of program impact**, indicating that baseline risk differences between cohorts are minimal.

---

## 4. Monthly Cohort Validation

Monthly cohort analysis was conducted to verify the consistency of model predictions.

For each month we compare:

- expected readmission risk
- observed readmission rates
- test vs holdout performance

This helps validate that the **risk-adjusted model captures underlying risk trends** across time.

---

## 5. Key Takeaways

- Traditional evaluation estimated a **0.76pp reduction in readmissions**.
- Risk-adjusted model estimated a **0.73pp reduction**.
- Difference between methods is **only 0.03pp**.
- Baseline risk between cohorts is nearly identical.
- The risk-adjusted model can serve as a **proxy indicator of program performance**.

---

## Conclusion

The risk-adjusted readmission model produces program impact estimates that closely match the NBA evaluation results.  
This suggests the model can provide an **early directional signal of program performance**, particularly in situations where a full evaluation study has not yet been completed.