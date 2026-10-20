# Model Monitoring Diagnostic Agent: Design and Architecture

## 1. Design approach

Build a workflow-first diagnostic service around the existing Flask/Python monitoring dashboard. Use deterministic code to compute metrics and identify candidate anomalies, and use Claude to correlate evidence, propose incident priorities, explain findings, and recommend investigation steps.

Start with one Claude call per model and evaluation window. Add bounded, read-only investigation tools only when additional context is needed. A multi-agent architecture is not required for the initial version.

## 2. High-level architecture

```text
Daily/weekly scheduler or dashboard trigger
                  |
                  v
Background job queue and Python worker
                  |
                  v
Metrics and context collector
  - Current metrics and historical baselines
  - Sample sizes and label maturity
  - Model, feature, and segment metadata
  - Recent deployments and known incidents
                  |
                  v
Deterministic anomaly engine
  - Threshold and baseline comparisons
  - Persistence and sample-size checks
  - Candidate alerts and hard-failure detection
                  |
                  v
Claude diagnostic service
  - Correlate related signals
  - Propose priority and likely explanations
  - Identify missing evidence
  - Recommend next actions
                  |
                  v
Schema validation and policy enforcement
  - Verify evidence references
  - Apply mandatory escalation rules
  - Deduplicate incidents and apply cooldowns
                  |
                  v
Incident store --> Flask dashboard
                  |
                  v
Notification service --> Immediate escalation or digest
                  |
                  v
Human review and feedback
```

Keep long-running diagnostic jobs outside Flask request handlers. A dashboard request should enqueue a job and return a run ID; the dashboard can retrieve its status and results.

## 3. Component responsibilities

### 3.1 Trigger and orchestration

Supported triggers:

- Daily operational review.
- Weekly trend review.
- Manual diagnosis for a selected model and date range.

Each job records the model ID, model version, evaluation window, baseline definition, policy version, and input snapshot ID. Use an idempotency key to avoid duplicate processing of the same snapshot and configuration.

### 3.2 Metrics and context collector

Reuse the existing metrics store or Python metric functions rather than scraping dashboard pages.

| Category | Example inputs |
|---|---|
| Data quality | Missingness, freshness, schema violations, duplicates, out-of-range values |
| Drift | PSI, KS, distribution shifts, categorical population changes |
| Scores | Mean score, quantiles, distribution, score bands, top-X% cutoff |
| Performance | PPV, recall, lift, confusion-matrix counts, operating-threshold metrics |
| Segments | Metrics and population counts by monitored group |
| Context | Feature importance, owners, criticality, releases, maintenance windows |

For each metric, include its identifier, definition, current value, baseline value, sample size, evaluation window, baseline window, threshold policy, and recent history.

For performance metrics, include label availability, maturity, and cohort definition. Do not compare incomplete recent labels with fully matured historical labels as though they were equivalent.

For top-X% metrics, record X, the selection population, cutoff policy, selected count, and tie-handling policy. This helps distinguish model behavior from changes in selection or cohort composition.

### 3.3 Deterministic anomaly engine

Python owns calculations and candidate detection. Claude should not invent thresholds or serve as the sole detector of critical failures.

Configurable checks may include:

- Absolute and relative changes versus a baseline.
- Historical variation or uncertainty bounds.
- Persistence across consecutive windows.
- Minimum sample size and minimum positive-event counts.
- Feature and segment business criticality.
- Mandatory hard failures, such as missing scoring data or schema breaks.

Thresholds must be calibrated for each model and metric. Example PSI or PPV cutoffs are configuration examples, not universal defaults.

Do not restrict all context to breached metrics. Include a compact summary of relevant healthy metrics so Claude can assess counterevidence.

### 3.4 Claude diagnostic service

Input:

- Versioned diagnostic instructions.
- Explicit severity policy.
- Candidate alerts.
- Relevant healthy metrics and historical context.
- Recent incidents and deployment changes.
- Required output schema.

Responsibilities:

1. Group related candidate alerts into incident hypotheses.
2. Explain observed changes using supplied evidence.
3. Propose High, Medium, or Low priority.
4. Distinguish observations from possible causes.
5. Identify missing evidence and suggest the next investigation.

A correlated drift and performance change does not prove causation. Reports should use language such as “possible upstream data issue” unless additional evidence supports a stronger conclusion.

### 3.5 Validation and policy enforcement

After Claude returns a result:

- Validate the response against a typed schema.
- Verify that referenced metric and alert IDs exist.
- Check numerical statements against the input snapshot.
- Require an explanation for suppressed candidate alerts.
- Prevent the model from suppressing mandatory critical alerts.
- Apply final routing policy in Python.
- Retain both the proposed priority and final policy-enforced priority.

Schema compliance alone does not establish factual correctness.

If Claude fails or returns an invalid response, preserve the run failure, retry within a bounded policy, and fall back to deterministic handling. Critical rule-based alerts must still reach their owners.

### 3.6 Incident persistence and notification

Store incidents separately from metric-level alerts. One incident may reference multiple alerts.

Track incident lifecycle:

```text
New -> Open -> Acknowledged -> Resolved
            -> Suppressed with reason and expiry
```

Use stable incident fingerprints based on model, affected metric family, segment, and issue type. Update an existing incident rather than sending a new email for every repeated breach.

Notification policy:

| Priority | Default routing |
|---|---|
| High | Immediate owner notification, subject to deduplication |
| Medium | Daily or weekly digest |
| Low | Dashboard only |

Re-notify when an incident materially worsens, changes scope, or remains unacknowledged beyond its escalation policy.

## 4. Severity policy

Keep severity, evidence sufficiency, and notification routing separate.

| Priority | Interpretation |
|---|---|
| High | Critical data/scoring failure, material confirmed performance degradation, or substantial exposure requiring prompt investigation |
| Medium | Meaningful change requiring investigation, but impact is limited or not yet established |
| Low | Minor or expected variation with limited actionable impact |

Insufficient data should be represented explicitly, not automatically treated as Low. Missing labels or stale monitoring data can themselves warrant escalation.

Persistence is useful for suppressing noise, but must not delay hard-failure alerts. Feature importance is supporting context, not a sufficient reason to dismiss data-quality or group-level issues.

## 5. Example diagnostic output

The following is illustrative; IDs and values are fictional.

```json
{
  "run_id": "run-example-001",
  "model_id": "example_model",
  "evaluation_window": "example_week",
  "overall_status": "needs_attention",
  "incidents": [
    {
      "incident_key": "example_model:income_quality:overall",
      "title": "Income data-quality change with score and PPV movement",
      "proposed_priority": "high",
      "evidence_sufficiency": "moderate",
      "related_alert_ids": ["alert_01", "alert_02", "alert_03"],
      "evidence": [
        {
          "metric_id": "income_missing_rate",
          "current_value": 0.064,
          "baseline_value": 0.002
        },
        {
          "metric_id": "ppv_top_10_percent",
          "current_value": 0.58,
          "baseline_value": 0.72
        }
      ],
      "hypotheses": [
        "An upstream income-data change may be contributing to score movement."
      ],
      "limitations": [
        "The supplied evidence does not establish causality."
      ],
      "recommended_actions": [
        "Check recent income-pipeline changes.",
        "Confirm label maturity and cohort comparability.",
        "Compare affected and unaffected segments."
      ],
      "owner_hint": "model_owner"
    }
  ],
  "suppressed_candidates": [],
  "data_limitations": []
}
```

The application adds final priority, notification disposition, and lifecycle state after validation and policy enforcement.

## 6. Optional investigation tools

Begin with a fixed snapshot. If this is insufficient, expose a small set of read-only tools:

| Tool | Purpose |
|---|---|
| `get_metric_history` | Retrieve a bounded historical series |
| `get_segment_metrics` | Inspect affected and unaffected groups |
| `get_feature_metadata` | Retrieve feature definition and criticality |
| `get_recent_deployments` | Retrieve release and pipeline-change records |
| `get_related_incidents` | Retrieve prior diagnoses and reviewer feedback |

Your Python service validates arguments, authorizes access, executes queries, and returns results. Enforce model/date scoping, result-size limits, tool-call limits, deadlines, and token budgets.

Keep report persistence and notification outside the LLM tool loop initially. Do not expose arbitrary SQL, shell access, threshold modification, retraining, or pipeline changes.

## 7. SDK choice

For the MVP, use the Anthropic Python API SDK for a bounded request with structured output. If additional investigation is needed, add an application-controlled tool-use loop.

Consider the Claude Agent SDK when you specifically need its managed agent loop and permission controls. It is not a prerequisite for this diagnostic architecture.

## 8. Flask/Python implementation layout

```text
monitoring_dashboard/
|-- app/
|   |-- routes/
|   |   |-- dashboard_routes.py
|   |   `-- diagnostic_routes.py
|   |-- services/
|   |   |-- metrics_collector.py
|   |   |-- anomaly_engine.py
|   |   |-- diagnostic_orchestrator.py
|   |   |-- claude_diagnostic_service.py
|   |   |-- report_validator.py
|   |   |-- incident_service.py
|   |   `-- notification_service.py
|   |-- schemas/
|   |   |-- metric_snapshot.py
|   |   |-- candidate_alert.py
|   |   `-- diagnostic_report.py
|   |-- prompts/
|   |   `-- diagnostic_agent_v1.md
|   `-- jobs/
|       `-- run_diagnostic_job.py
|-- config/
|   |-- severity_policy.yaml
|   `-- notification_policy.yaml
`-- tests/
```

Suggested endpoints:

- `POST /diagnostic-runs`: enqueue a run and return its ID.
- `GET /diagnostic-runs/<run_id>`: retrieve status and results.
- `GET /incidents`: list and filter incidents.
- `POST /incidents/<incident_id>/feedback`: record reviewer feedback.

## 9. Auditability and security

Retain input snapshots, metric definitions, baseline definitions, prompt and policy versions, model identifier, tool results, validated reports, notification events, latency, token usage, and reviewer feedback.

Use aggregate metrics by default. Minimize sensitive data sent to the LLM, enforce authorization at the service layer, and treat retrieved text as untrusted input rather than instructions.

Record concise evidence and rationale; do not require or store private internal reasoning.

## 10. Evaluation and rollout

Before enabling automated notifications, replay historical windows with known incidents and run in shadow mode.

Measure:

- Recall of critical incidents.
- Accuracy of priority assignments.
- False-positive and missed-incident rates.
- Reduction in notifications relative to the current system.
- Evidence-reference validity and unsupported-claim rate.
- Consistency across repeat runs.
- Cost and latency per model-window.

Review suppression decisions, not just escalated incidents. Fewer emails is only a success if critical problems remain visible.

Recommended rollout:

1. Version metric snapshots and candidate-alert rules.
2. Implement one bounded Claude call per model-window.
3. Validate reports and display them without notifications.
4. Collect data-scientist feedback and calibrate policies.
5. Enable policy-controlled notifications and fallback alerts.
6. Add read-only investigation tools only for demonstrated gaps.

## Documentation used in the architecture discussion

- Claude workflow versus agent concepts: https://academy.claude.com/courses/building-with-the-claude-api/workflows-vs-agents
- Claude tool-use execution model: https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works
- Claude structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Claude Agent SDK agent loop: https://code.claude.com/docs/en/agent-sdk/agent-loop

These documents describe platform capabilities. The architecture, severity policy, deployment layout, and rollout plan above are proposed application designs, not vendor-prescribed requirements.
