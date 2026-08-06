# MLOps Model Monitoring Platform - Architecture Planning Document

## Objective

Design and build an internal enterprise-grade Model Monitoring Platform inspired by commercial products such as:

- Arize AI
- WhyLabs
- Evidently AI
- Fiddler AI
- SageMaker Model Monitor

The goal is **NOT** to replicate every feature of these products, but to build a lightweight, extensible monitoring platform tailored to our healthcare ML models running on Vertex AI.

Current backend infrastructure already exists:

- Vertex AI Pipelines
- BigQuery
- GCP

Frontend technology is open for experimentation (Streamlit, React, Grafana, etc.). Looker Studio is NOT an option.

---

# Current State

Vertex AI monitoring pipelines already compute standard monitoring metrics.

Pipelines execute on a schedule and store monitoring outputs in BigQuery.

Examples include:

- Drift metrics
- Model performance
- Calibration
- Data quality
- Prediction distribution
- Pipeline execution metadata

Additionally, each model can execute custom SQL files to compute business/clinical KPIs.

---

# Long-term Goal

Build a reusable Model Monitoring Portal capable of supporting many ML models without modifying dashboard code whenever a new model is added.

Adding a new model should ideally require only:

- new SQL files
- metadata/configuration
- no frontend code changes

---

# Design Philosophy

Do NOT hardcode dashboards.

Instead, build a metadata-driven dashboard engine.

Commercial products generally separate the platform into three layers:

Monitoring Layer
↓

Metric Storage
↓

Visualization Layer

Our architecture should follow the same principle.

---

# High-Level Architecture

Vertex AI Pipeline

↓

Monitoring SQL

↓

BigQuery

↓

Metadata Layer

↓

Dashboard Engine

↓

Frontend

---

# Core Components

## 1. Monitoring Engine

Responsible for computing generic monitoring metrics.

Examples

- Drift
- PSI
- KS
- Wasserstein
- Calibration
- ROC
- Precision
- Recall
- Feature importance
- Missing values
- Data quality
- Prediction distribution

These should be reusable across every model.

---

## 2. Business KPI Engine

Each model can define its own KPIs.

Examples

Readmission Model

- Readmission Rate
- Members Identified
- Members Engaged
- Engagement Rate
- Top Hospitals

SNF Model

- Average LOS
- Long Stay %
- Transition Rate

ED Diversion

- ER PMPM
- Avoided ER Visits
- High Risk Members

The framework should allow every model to contribute custom SQL files.

---

## 3. Metadata Layer

This is one of the most important architectural pieces.

Avoid hardcoding:

if model == RAP

Instead define metadata describing:

- pages
- widgets
- SQL source
- visualization
- layout

Example

```yaml
page:
Clinical KPIs

widgets:

- title: Readmission Rate
type: line_chart
query: readmission_rate.sql

- title: Members Identified
type: line_chart
query: identified.sql

- title: Top Hospitals
type: bar_chart
query: top_hospitals.sql
```

The dashboard should read metadata and automatically build the page.

---

# Widget-Based Architecture

Instead of building pages manually, create reusable widgets.

Possible widgets include

- KPI Card
- Line Chart
- Bar Chart
- Histogram
- Scatter Plot
- Pie Chart
- Heatmap
- Gauge
- Data Table
- Feature Importance
- Calibration Curve
- ROC Curve
- PR Curve
- Distribution Plot
- Alert Banner
- Pipeline Timeline

Every page becomes a collection of widgets.

---

# Dashboard Layout

Possible navigation

Overview

Performance

Data Quality

Drift

Calibration

Feature Importance

Pipeline Health

Clinical KPIs

Alerts

Settings

Each page should support reusable widgets.

---

# Generic vs Model-Specific Metrics

Need to distinguish between:

Common Monitoring

Available for every model

Examples

- Drift
- Calibration
- Data Quality
- Performance
- Pipeline Status

Model-specific KPIs

Unique to each model

Examples

Readmission Rate

Average LOS

ER Visits

Members Identified

The framework should support both seamlessly.

---

# Visualization Metadata

Different KPIs require different visualization types.

Examples

Members Identified

→ Line Chart

Readmission Rate

→ Line Chart

Top Hospitals

→ Horizontal Bar Chart

Average LOS by Facility

→ Bar Chart

Regional Distribution

→ Pie Chart

Prediction Distribution

→ Histogram

Visualization choice should be defined in metadata rather than code.

---

# BigQuery Data Model

Think carefully about table design.

Potential tables

model_metrics

drift_metrics

feature_metrics

pipeline_runs

alerts

prediction_distribution

business_metrics

dashboard_metadata

widget_metadata

Need to determine:

- normalized vs denormalized
- partitioning
- clustering
- querying efficiency
- scalability

---

# Metadata Questions

Determine where metadata should live.

Possible options

YAML

JSON

BigQuery

Firestore

Cloud Storage

Pros and cons of each.

Need a recommendation.

---

# Dashboard Engine

Need a rendering engine that can:

Load metadata

↓

Execute SQL

↓

Load dataframe

↓

Determine widget type

↓

Render visualization

This should work for any model.

---

# Extensibility

When a new model is onboarded, the desired process is:

Create SQL

↓

Register metadata

↓

Pipeline computes metrics

↓

Dashboard automatically displays new pages

No frontend changes.

---

# Frontend Evaluation

Evaluate frontend technologies.

Candidates

## Streamlit

Pros

- Python
- Rapid development
- Plotly integration
- BigQuery integration
- Easy deployment

Cons

- Less polished than React

---

## React / Next.js

Pros

- Maximum flexibility
- Excellent UX
- Enterprise feel

Cons

- Much larger development effort

---

## Grafana

Evaluate whether Grafana could serve as visualization layer while keeping BigQuery backend.

Investigate

- plugins
- custom dashboards
- flexibility
- metadata-driven rendering

---

Need recommendation based on:

- maintainability
- scalability
- developer productivity
- enterprise UX

---

# Future Features

Potential future roadmap

AI-generated monitoring summaries

Root Cause Analysis

Model comparison

Pipeline lineage

Drill-down views

Alert management

Email/Slack notifications

Threshold configuration

User roles

Model ownership

Audit logs

Download reports

PDF generation

Executive dashboard

SHAP visualization

Feature attribution

Model registry integration

Vertex AI integration

---

# Scalability Considerations

Architecture should support

- 20+
- 50+
- 100+

models without dashboard rewrites.

Need recommendations on

- metadata design
- plugin architecture
- widget architecture
- SQL execution strategy
- caching
- performance optimization

---

# Deliverables Expected From Planning

Please produce:

1. Overall system architecture
2. Component diagram
3. BigQuery schema recommendations
4. Metadata architecture
5. Widget architecture
6. Dashboard architecture
7. Frontend recommendation
8. Backend recommendation
9. Plugin/extension mechanism
10. Folder structure
11. Technology stack recommendation
12. Scalability considerations
13. Trade-offs between Streamlit, React, Grafana
14. Enterprise-grade architecture recommendations inspired by Arize, WhyLabs, Fiddler, and Evidently
15. Suggested implementation roadmap (MVP → v2 → v3)

    The solution should prioritize maintainability, extensibility, and minimal code changes when onboarding new ML models.
    
I think one additional area is worth including because it’s something commercial platforms spend a lot of effort on:

Monitoring SDK / Plugin API

Instead of thinking only about dashboards, define what a model owner must provide.

For example, every model package could expose:

model/
├── metadata.yaml
├── dashboard.yaml
├── kpis/
│   ├── identified.sql
│   ├── engagement.sql
│   └── readmission.sql
├── thresholds.yaml
├── alerts.yaml
└── README.md


Then onboarding a new model becomes a registration process rather than a development project. I would encourage the planning agent to design this plugin architecture first, because it will influence the dashboard, metadata, and BigQuery schema, and it will make the platform much easier to extend over time.

    
    
    