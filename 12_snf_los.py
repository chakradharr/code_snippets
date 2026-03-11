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