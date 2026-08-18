Metric

One-line meaning

🟢 Green

🟡 Yellow

🔴 Red

PSI

Measures how much the population has shifted between predefined bins.

< 0.10

0.10–0.25

> 0.25

KS Statistic

Measures the largest difference between the training and production cumulative distributions.

< 0.05

0.05–0.10

> 0.10

KS p-value

Measures whether the observed KS difference is statistically distinguishable from zero; lower = stronger statistical evidence of difference.

≥ 0.05

0.01–0.05

< 0.01

JS Divergence

Measures the overall difference between the two probability distributions.

< 0.10

0.10–0.25

> 0.25

Wasserstein Distance

Measures how far the production distribution must be shifted to match the reference distribution.

< 0.10 SD

0.10–0.25 SD

> 0.25 SD

The simplest interpretation for your UI

You could literally display:

* PSI: Population shift
* KS: Maximum distribution difference
* KS p-value: Statistical significance of distribution difference
* JS: Overall distribution difference
* Wasserstein: Distance between distributions

And one key rule for your dashboard:

Don’t make KS p-value alone trigger a red alert, especially with your very large healthcare cohorts. Your screenshot is a perfect example: p-values are essentially zero while PSI is <0.007, meaning statistically detectable but very small drift.

For your platform, I’d think about the metrics as answering different questions:

KS

“Is there a maximum separation between distributions?”

PSI

“How much did the population move across predefined bins?”

JS

“How different are the distributions overall?”

Wasserstein

“How far did the distribution move in the feature’s actual units?”

KS p-value

“Is the observed difference statistically distinguishable from zero?”

Then combine them.

Level

Rule

Meaning

🟡 Warning

KS ≥ 0.05 AND PSI ≥ 0.10

Meaningful drift; investigate

🔴 Critical

KS ≥ 0.10 AND PSI ≥ 0.25

Strong drift; immediate investigation

⚪ Statistical only

p < 0.05 but above thresholds not met

Don’t alert; record only

**Feature drift is an early-warning signal, not proof of model degradation.**

For example:

Feature Drift → Investigate → Check Data Quality → Check Prediction Drift → Check Model Performance → Determine Business Impact

A monitoring framework should ideally connect multiple layers.

Layer 1 — Data Quality

Monitor:

• Missingness
• Null rates
• Invalid values
• Range violations
• Duplicate records
• Unexpected categories
• Pipeline failures

Layer 2 — Feature Drift

Monitor:

• KS
• PSI
• JS distance
• Other distribution-distance metrics

Layer 3 — Prediction Drift

Monitor:

• Prediction distribution
• Score distribution
• Percentage above intervention threshold
• Average prediction
• Prediction quantiles

Layer 4 — Model Performance

When labels become available, monitor:

• AUROC
• AUPRC
• Calibration
• Precision
• Recall
• Sensitivity
• Specificity
• Brier score
• Other model-specific metrics

Layer 5 — Clinical/Business KPIs

For a healthcare model, monitor relevant outcomes such as:

• Number of patients identified
• Percentage of population identified
• Engagement rate
• Readmission rate
• Intervention rate
• Outcomes among identified patients
• Other program-specific KPIs

────────

13. Example Interpretation

Suppose a feature has:

• KS = 0.24
• PSI = 0.31
• JS Distance = 0.18

Interpretation:

KS = 0.24

Red.

There is a substantial difference in the cumulative distribution.

PSI = 0.31

Red.

The population has shifted substantially across the predefined bins.

JS = 0.18

Yellow.

The overall distributions show moderate divergence.

Overall conclusion

Because multiple metrics indicate drift, the feature should be investigated rather than relying on only one metric.

The fact that KS and PSI are red while JS is yellow does not necessarily represent a contradiction. Each metric measures distributional differences differently.

────────

14. Combining Multiple Metrics

A useful monitoring strategy is to avoid triggering major action based on a single metric alone.

For example:

Green

All major metrics are green.

Yellow

At least one metric is yellow and none are strongly red.

Red

Multiple metrics are red, or one highly critical feature has severe drift.

An example rule:

> **Red alert if ≥2 drift metrics are red, or if a critical feature has a red result on any primary drift metric.**

Another possible rule:

> **Yellow alert if ≥1 metric is yellow; Red alert if ≥1 metric is red and the drift persists for multiple monitoring periods or is confirmed by another metric.**

This reduces false alarms caused by one noisy metric.






