hey i working as medicare care management lead data scientist for aetna; what im trying to do is create a touch point of a member journey right from inapetient admission till discharge and post ; calls emails and text sent to members and time of engagement and various programs the member is identified targeted and engaged etc... main aim to find how the engagement is happening after we identify a member for a program lets say readmission avoidance etc... hwo to track and find insights and layout a better staretegy than what we are doing now : what tools and things might be helpful 
    
    Got it. What you’re describing is basically “member engagement telemetry + journey analytics” for care management: every member has a timeline of clinical events + outreach events + program states, and you want to understand what actually happens after identification (and how to improve it).

Here’s a very practical blueprint (tools + data model + insights you can generate).

⸻

1) Build a single “Member Journey Event Stream”

Think of everything as an event on a timeline.

Event types (examples):

* Clinical: IP admit, transfer, discharge, ED revisit, SNF admit, auth created/approved, etc.
* Program ops: identified → targeted → assigned → attempted → reached → engaged → enrolled → completed → closed
* Outreach: call placed, call connected, voicemail, SMS sent/delivered/replied, email sent/opened/clicked
* Care manager actions: notes created, referrals, case opened/closed
* Barriers: wrong phone, language, declined, no consent, unreachable, competing program overload

Minimum fields for every event (super important):

* member_id
* event_ts (timestamp) + event_dt
* event_type + event_subtype
* source_system (Compass/CRM, dialer, SMS vendor, auth system, claims, etc.)
* program_id / program_name (if applicable)
* channel (call/sms/email/in-app/mail)
* agent_id (if staff-driven)
* outcome (connected, left VM, replied, scheduled, declined)
* metadata (JSON: facility, discharge disposition, language, reason codes, etc.)

Tooling to do this well (in Aetna-style GCP world):

* BigQuery as the canonical event store (partition on event_dt, cluster on member_id, program_id)
* Dataform/dbt to standardize + version your transformation logic
* Cloud Composer/Airflow for orchestration + SLAs
* Looker/Looker Studio for self-serve dashboards (journey funnels + cohorts)
* Optional but powerful:
    * Pub/Sub + Dataflow if you want near-real-time events (e.g., engagement within hours of discharge)
    * Vertex AI for response propensity / next-best-action models

⸻

2) Create “Program State” tables (so you can measure funnels cleanly)

Event streams are great, but leaders want simple answers. So derive a state table per member per program episode.

Example: member_program_episode

* member_id
* episode_id (e.g., an IP admission-driven episode)
* program_name
* identified_ts
* targeted_ts
* assigned_ts
* first_outreach_ts
* first_contact_ts (connected / replied)
* engaged_ts (your definition)
* enrolled_ts
* closed_ts
* close_reason

This is what makes “where are we losing people?” measurable.

⸻

3) Define your “episode anchor” (otherwise leakage + confusion happens)

For readmission avoidance, anchor to something like:

* IP discharge date/time (most common), or
* Admission (if that’s when you first identify), but then you must clearly define pre/post windows.

Then you build episodes:

* One episode per discharge, with a clean post window (e.g., 0–30 days)
* Link outreach/engagement events to the episode using:
    * event timestamp within episode window, and
    * program match + team match rules

⸻

4) Metrics that immediately create insights (and action)

A) Funnel + speed metrics (these change behavior fast)

* Coverage: % identified members with any outreach attempt within 24h / 48h
* Time-to-first-attempt (median + p90)
* Time-to-first-contact
* Contact rate = contacted / attempted
* Engagement rate = engaged / contacted (or / identified, but be consistent)
* Drop-off reasons (wrong number, declined, no consent, etc.)

B) Channel effectiveness (but not “vanity”)

* Calls vs SMS vs email: contact probability and engagement probability
* “Sequence” performance: call→sms vs sms→call, etc.
* Optimal outreach cadence: too many touches can reduce engagement (fatigue)

C) Operational performance

* By facility, discharge disposition, language, region, day of week, time of day
* By care manager team / vendor / dialer (but be careful: adjust for member mix)

D) “Program collision” insights

Members often get targeted by multiple programs.

* % of members contacted by 2+ programs in same 7 days
* Engagement/decline rate when multi-targeted
* Build a “priority + coordination” strategy from this

⸻

5) Strategy improvements you can drive from the data

These are common “wins” once the journey tracking exists:

1. Fix the “speed to touch” gap
    * If first attempt is happening 3–7 days after discharge, you’ll often see a big drop in engagement.
    * Set operational SLAs: “attempt within 24h for high-risk discharges”.
2. Segment outreach scripts + channels
    * Example: older members might respond better to calls; caregivers may respond better to SMS.
    * Language + time zone + known preferences matter.
3. Next Best Action rules
    * If 2 failed calls → SMS with callback link
    * If SMS replied “later” → auto-schedule call window
    * If wrong number → route to address/phone verification workflow
4. Reduce program overwhelm
    * Create a “member-level orchestration layer”:
        * one primary program owner
        * coordinated messaging
        * avoid 3 different teams calling same person

⸻

6) Analytics methods that work well for your use case

* Journey funnel dashboards (identified → attempted → contacted → engaged)
* Cohort analysis (by discharge week/month)
* Survival/time-to-event curves for time-to-engage (very intuitive for ops)
* Sequence mining (what outreach sequences lead to engagement)
* Causal / quasi-experimental:
    * If you roll out a new cadence/script by market: DiD
    * If assignment is “as-if random” around a cutoff: regression discontinuity
    * Otherwise: propensity + IPW (but keep it simple for stakeholders)

⸻

7) Practical “tool stack” recommendations

If you’re staying mostly in the GCP ecosystem:

* BigQuery: event store + episode tables + metrics
* Dataform/dbt: maintainable transformations + testing
* Composer: scheduling and dependencies
* Looker:
    * Journey funnel explorer
    * SLA dashboards (24h attempt, contact rate)
    * Drill-down to member-level timelines (with PHI-safe controls)
* Vertex AI (phase 2):
    * engagement propensity
    * best channel/time
    * uplift modeling (who benefits from outreach vs would engage anyway)

If your org has a CRM (Salesforce/Genesys/etc.), still keep BigQuery as the analytics layer and ingest those interaction logs.

⸻

8) One thing that makes or breaks this: consistent definitions

Before you scale, standardize:

* What exactly counts as “attempt”?
* What exactly counts as “contact”?
* What exactly counts as “engagement”?
* What is an “episode” start and end?

If definitions vary by program/vendor, the insights will be noisy and people won’t trust the dashboards.

⸻

If you tell me what systems you currently have for: (1) IP admit/discharge feed, (2) outreach logs (dialer/SMS/email), and (3) program state/CRM, I can propose a concrete data model (tables + key joins) and a starter dashboard layout (funnel + SLA + channel + collision + outcomes).

#####
Great question — this is exactly the right next step once you have journey tracking.

I’ll explain uplift modeling in your care-management context, step by step, and how to actually implement it without over-engineering.

⸻

What “uplift modeling” really means (plain English)

Right now, most programs answer:

“Who is likely to engage?”

Uplift modeling answers a much more valuable question:

“Who is more likely to engage because we contacted them?”

That distinction matters a lot.

Why standard models fail here

A regular engagement model will often pick:

* motivated members
* people who would have engaged anyway
* people who are easy to reach

But outreach doesn’t change their behavior — you just get credit.

Uplift modeling finds:

* members who would NOT engage if untreated
* BUT WOULD engage if we intervene

That’s where ROI lives.

⸻

The 4 member types (this will click instantly)

Uplift modeling implicitly classifies members into 4 groups:

Group	Outreach Effect	What to do
Persuadables	Outreach helps	✅ PRIORITIZE
Sure things	Would engage anyway	De-prioritize
Lost causes	Won’t engage even if contacted	Avoid wasting effort
Do-not-disturb	Outreach reduces engagement	🚫 Avoid

Your goal = find Persuadables

⸻

Step 1: You MUST have a treatment & control concept

This is non-negotiable.

Treatment = outreach

Examples:

* Call/SMS/email within 48h of discharge
* Assigned care manager contact
* Multi-touch sequence

Control = no outreach (or delayed outreach)

Ways to get this without violating ethics:

* Capacity constraints (not everyone reached)
* Timing variation (weekend vs weekday)
* Regional rollout
* Vendor differences
* Missed contacts (valid natural control)

👉 Key point: Control does NOT mean “ignore people on purpose” — it means natural variation.

⸻

Step 2: Define a clean outcome

Pick one clear outcome for the first model.

Good examples:

* Engaged within 7 days
* Enrolled within 14 days
* Attended follow-up appointment
* No readmission within 30 days (advanced)

Start with engagement, not readmission — cleaner signal.

Binary outcome:

Y = 1 if engaged
Y = 0 otherwise

⸻

Step 3: Feature rules (VERY IMPORTANT)

Allowed features (pre-treatment only)

✅ Demographics
✅ Clinical history
✅ Prior utilization
✅ Risk scores
✅ Facility characteristics
✅ Discharge disposition

Forbidden features (leakage!)

🚫 Outreach attempts
🚫 Contact success
🚫 Notes text
🚫 Anything after first outreach

If it happens after treatment, it CANNOT be a feature.

⸻

Step 4: Start simple (don’t jump to fancy models)

Option A (Recommended): Two-Model (T-Learner) approach

This works very well in healthcare ops.

1. Split data:
    * Treated group (outreach)
    * Control group (no outreach)
2. Train two models:

Model_T: P(engage | outreach)
Model_C: P(engage | no outreach)

3. Uplift score:

uplift = P_T - P_C

Interpretation:

* +0.20 → outreach increases engagement by 20pp
* −0.05 → outreach hurts engagement

This is easy to explain to leadership.

⸻

Option B: Single-model with interaction (good for SQL / explainability)

engaged ~ treatment
        + features
        + treatment × features

Works well if stakeholders want coefficients.

⸻

Step 5: Validate uplift (this is where people mess up)

DO NOT evaluate with AUC.

Instead:

1️⃣ Rank members by uplift score

Split into deciles (or quintiles).

2️⃣ For each decile, compute:

Engagement_rate_treated - Engagement_rate_control

3️⃣ Plot uplift curve

Top deciles should show:

* big positive lift
* bottom deciles near zero or negative

If top 20% shows +15–25pp uplift → you won

⸻

Step 6: Turn uplift into strategy (this is the payoff)

Outreach targeting

Instead of:

“Call top 30% risk”

You do:

“Call top 30% uplift”

That often means:

* fewer calls
* higher engagement
* less member fatigue
* better care manager morale

⸻

Channel optimization

Train separate uplift models per channel:

* Call uplift
* SMS uplift
* Email uplift

Now you can say:

“This member responds to SMS, not calls”

⸻

Capacity-aware prioritization

Create tiers:

* Tier 1: High uplift → immediate outreach
* Tier 2: Medium uplift → automated SMS
* Tier 3: Low/negative uplift → suppress or delay

⸻

Step 7: Governance & rollout (important in Aetna-type orgs)

* Start as shadow model (no decisioning)
* Compare:
    * Current strategy vs uplift-based
* Pilot in 1–2 markets
* Measure:
    * Engagement per 100 outreaches
    * Cost per engagement
    * Member complaints / opt-outs

⸻

Common pitfalls (watch out)

❌ Using post-outreach features
❌ No true control group
❌ Measuring readmission first (too noisy)
❌ Optimizing uplift without ops buy-in

⸻

How this fits perfectly with your journey work

Your journey event stream already gives you:

* Treatment timing
* Outcome timing
* Channel
* Program exposure

Uplift modeling is the natural next layer, not a separate project.

⸻

If you want, next I can:

* Draft a BigQuery table design for uplift modeling
* Write pseudo-SQL / Python for T-learner
* Help you frame this for leadership (ROI story)
* Show how to combine uplift with readmission risk (who to call FIRST)

Just tell me which one you want next.


######

Great question — this is the exact conceptual jump people struggle with, so let’s slow it down and make it very concrete.

You asked:

“How is ‘Who will engage because we contacted them?’ answered after we build an engagement prediction model?”

Short answer:
👉 It is not answered by an engagement prediction model alone.
But the engagement model is a necessary stepping stone that makes that final question answerable.

Let me explain this cleanly.

⸻

1️⃣ What an engagement prediction model actually answers

Your engagement model answers this question:

“If we contact this member, how likely are they to engage?”

Mathematically:

P(Engage | Outreach)

That’s it.

It does NOT tell you:

* whether outreach caused the engagement
* whether they would have engaged anyway

So engagement models optimize efficiency, not causality.

⸻

2️⃣ Why that is still very valuable (but incomplete)

With only a readmission model, you rank members like this:

High clinical risk → outreach

With an engagement model layered on top, you can do:

High readmission risk
AND
High engagement probability
→ prioritize

This already improves:

* contact rates
* enrollment rates
* care manager productivity

But it still cannot answer the highlighted question.

⸻

3️⃣ The missing counterfactual (this is the key idea)

To answer:

“Who will engage because we contacted them?”

You must be able to compare two worlds for the same type of member:

World	Outcome
Contacted	Engaged?
Not contacted	Engaged anyway?

That second row is the counterfactual.

An engagement prediction model only sees the first world.

⸻

4️⃣ Where engagement prediction ENABLES uplift (but doesn’t replace it)

Here’s the progression:

Step A — Engagement model

You estimate:

P(Engage | Outreach)

You learn:

* Who is easy to engage
* Who never engages
* Which features predict engagement

This gives you:

* strong features
* clean outcomes
* trusted data pipelines

Without this, uplift modeling will fail.

⸻

Step B — Introduce a natural control group

Now suppose (naturally, not artificially):

* Some members were not contacted
    * capacity limits
    * weekend discharges
    * late identification
    * unreachable routing

Now you can also estimate:

P(Engage | No Outreach)

This is impossible without clean engagement tracking.

⸻

Step C — The actual answer to the highlighted question

Now you can compute:

Uplift = P(Engage | Outreach) − P(Engage | No Outreach)

This value answers:

“How much did outreach change the probability of engagement?”

This is the only moment when the highlighted sentence becomes true.

⸻

5️⃣ Concrete example (numbers make it click)

Let’s say after building your engagement model and adding controls:

Member Type	P(Engage | Outreach)	P(Engage | No Outreach)	Uplift
A	0.70	0.65	+0.05
B	0.45	0.10	+0.35
C	0.30	0.28	+0.02
D	0.20	0.25	−0.05

Interpretation:

* A: would engage anyway → not worth priority
* B: engages because of outreach → ⭐ gold
* C: weak effect → low ROI
* D: outreach hurts → avoid

An engagement model alone would rank A highest.
Uplift ranks B highest.

That’s the difference.

⸻

6️⃣ Why you CANNOT skip the engagement model

People sometimes ask:

“Why not jump straight to uplift?”

Because without an engagement model:

* outcomes are noisy
* features are wrong
* ops don’t trust results
* leadership won’t approve pilots

Engagement modeling:

* stabilizes signals
* validates definitions
* creates credibility
* builds ops muscle

Think of it as instrumentation before experimentation.

⸻

7️⃣ How to explain this to leadership (very important)

Use this ladder — it lands well:

Level 1: Who is at risk? (readmission model)
Level 2: Who will respond if we reach out? (engagement model)
Level 3: Who responds because we reached out? (uplift)

Then add:

“We cannot answer Level 3 responsibly until Level 2 is solid.”

This sounds mature, not slow.

⸻

8️⃣ Summary (one-glance takeaway)

* ❌ Engagement prediction ≠ uplift
* ✅ Engagement prediction enables uplift
* 🔑 The highlighted question requires treatment vs control
* 📈 Your next real win is Layer 2, not jumping to Layer 3

⸻

If you want, next I can:

* Draw a simple diagram showing readmission → engagement → uplift
* Help you define control groups you already have (without new experiments)
* Show how to combine readmission risk × engagement × uplift into one prioritization score
* Help you draft a technical design doc for Phase 1–2

Just tell me what would help you most next.



######

Absolutely — here is a clean, executive-ready summary you can use for yourself or directly turn into a 1-pager / deck slide.
I’ll keep it crisp, structured, and grounded in your current reality.

⸻

Problem Statement

Today, Care Management relies primarily on a readmission risk model that identifies members likely to readmit within 30 days.

However, after identification:

* We have limited visibility into how members are actually contacted
* We do not systematically track engagement journeys
* We cannot distinguish:
    * members who would engage anyway
    * members who engage because of outreach
    * members who never engage despite outreach

As a result:

* Outreach effort is not optimally targeted
* Care manager capacity may be misallocated
* Engagement variability across facilities, channels, and timing is not well understood
* Program effectiveness is hard to attribute to member engagement vs selection bias

⸻

Core Gaps Identified

1. No unified member journey view
    * Outreach, engagement, and program events are siloed across systems
2. No engagement measurement framework
    * Engagement definitions and SLAs vary by program/vendor
3. No behavioral response modeling
    * Readmission risk ≠ likelihood to engage
4. Limited ability to optimize outreach strategy
    * Channel, timing, cadence decisions are largely heuristic
5. No causal understanding of outreach impact
    * Unable to quantify which members benefit because of outreach

⸻

Proposed Solution (Phased & Practical)

Phase 1 — Build Member Journey Analytics (Foundational)

Goal: Make engagement visible and measurable

What to build:

* Unified Member Journey Event Table
    * Clinical events (admit/discharge)
    * Outreach attempts (call/SMS/email)
    * Contact outcomes
    * Program state transitions

Key outputs:

* Journey funnels (Identify → Attempt → Contact → Engage)
* Time-to-touch SLAs
* Drop-off diagnostics by facility, channel, timing

Value delivered:

* Immediate operational insights
* Identification of systemic delays and leakage
* Trustworthy engagement metrics

⸻

Phase 2 — Engagement Prediction Model (Efficiency Optimization)

Goal: Improve care manager efficiency

Model answers:

“Among members we contact, who is likely to engage?”

Approach:

* Population: members identified by readmission model
* Outcome: engagement within X days
* Features: pre-outreach only
* Model used for prioritization under capacity constraints

Value delivered:

* Higher engagement per outreach
* Reduced wasted effort
* Better channel and timing decisions

⸻

Phase 3 — Uplift Modeling (Causal Optimization)

Goal: Maximize ROI and member experience

Model answers:

“Who engages because we contacted them?”

Approach:

* Leverage natural control groups (missed, delayed, weekend discharges)
* Compare:
    * P(Engage | Outreach)
    * P(Engage | No Outreach)
* Target members with highest incremental lift

Value delivered:

* Outreach focused on “persuadable” members
* Reduced member fatigue
* Strong causal narrative for leadership

⸻

Strategic Framing (Leadership-Friendly)

Readmission model tells us who needs help
Journey analytics tells us whether help reaches them
Engagement modeling tells us how to deploy limited capacity
Uplift modeling tells us where outreach truly changes outcomes

⸻

Immediate Next Steps (Next 60–90 Days)

1️⃣ Data & Definitions

* Finalize definitions for:
    * Outreach attempt
    * Contact
    * Engagement
    * Episode start/end
* Inventory outreach & program data sources

2️⃣ Build Core Tables

* Member journey event table
* Program episode table (discharge-anchored)
* SLA metrics (time to first attempt/contact)

3️⃣ Deliver Early Insights

* Funnel dashboard for readmission-identified members
* Engagement leakage by facility/channel/timing
* Executive summary of key gaps

4️⃣ Prep for Modeling

* Establish clean engagement outcome labels
* Validate pre-treatment feature availability
* Identify natural control segments

⸻

Success Criteria

* ≥ X% improvement in engagement per outreach
* Reduced time-to-first-touch for high-risk discharges
* Fewer redundant member contacts across programs
* Clear evidence of operational ROI

⸻

If you want, I can:

* Turn this into a 1-slide exec summary
* Draft a technical design doc
* Propose KPIs + dashboard wireframes
* Help you pitch this to VP / Care Ops leadership

Just tell me which one you want next.


#####
Great question. I’ll make this tangible by showing what the outputs actually look like and how leadership uses them to make decisions. I’ll focus specifically on Phase 3 (Uplift / causal optimization) since that’s what you highlighted—but I’ll anchor it to outputs leadership already understands.

⸻

What the OUTPUT actually looks like (not theory)

1️⃣ Executive-level output (this is what VPs care about)

A. Uplift segmentation table

This is usually the first slide leadership understands.

Segment	% of Members	Incremental Engagement Lift	Recommendation
High Uplift (“Persuadable”)	25%	+18 pp	Call within 24h
Medium Uplift	35%	+6 pp	SMS + delayed call
Neutral	25%	+1 pp	Low-touch / deprioritize
Negative Uplift	15%	−5 pp	Suppress outreach

What this answers for leadership:

* “Where does outreach actually work?”
* “Can we safely not call everyone?”
* “How much engagement are we creating vs just observing?”

This alone reframes outreach from volume-based to impact-based.

⸻

B. ROI framing (very powerful)

Leadership thinks in per-100 or per-1,000 members.

Example:

For every 1,000 members contacted:

Strategy	Engagements	Incremental Gain
Current (risk-only)	210	—
Uplift-targeted	310	+100 engagements

Then translate:

* Fewer calls
* Same staffing
* Higher engagement
* Better member experience

This is the “why change behavior?” slide.

⸻

2️⃣ Program-owner / ops output (this drives action)

C. Who-to-call list (ranked by uplift)

At the member level (not shown broadly, but used operationally):

Member	Readmit Risk	Engagement Prob	Uplift Score	Action
A	High	Medium	+0.32	Priority call
B	High	High	+0.04	SMS only
C	Medium	Low	−0.08	Do not call

Key insight:
Leadership sees that:

* High clinical risk ≠ high outreach value
* Some high-risk members should not be called first

This supports capacity-aware decisioning.

⸻

D. Channel strategy output

Uplift by channel (this is gold for ops leaders):

Channel	Incremental Lift
Phone call	+14 pp
SMS	+9 pp
Email	+2 pp

And even better:

Segment	Best Channel
SNF discharges	Phone
Younger duals	SMS
Repeat decliners	None

Leadership takeaway:

“We’re not just calling less — we’re calling smarter.”

⸻

3️⃣ Analytical output (for trust & governance)

E. Uplift curve (proof of causality)

This is how you prove the model is real.

Conceptually:

* Rank members by uplift score
* Split into deciles
* Plot:

Engagement(treated) − Engagement(control)

Leadership-friendly interpretation:

“The top 20% of members account for ~60% of the engagement lift.”

This builds confidence that:

* Outreach caused the engagement
* Not just correlation or cherry-picking

⸻

4️⃣ How leadership actually USES this

Decision 1: Capacity planning

“If we can only reach 40% of members, which 40% gives us the biggest return?”

Before: random or risk-only
After: uplift-ranked

⸻

Decision 2: Program design

“Do we need the same outreach for everyone?”

Result:

* High uplift → intensive care management
* Low uplift → automated or passive support

This leads to tiered program models, which leadership loves.

⸻

Decision 3: Vendor / ops accountability

“Is low engagement because members don’t respond — or because outreach doesn’t help?”

Uplift separates:

* bad execution
* from low causal impact

This prevents blaming the wrong teams.

⸻

Decision 4: Strategic narrative

This is the line that resonates most:

“We moved from predicting risk to optimizing intervention impact.”

That’s a maturity jump leadership recognizes.

⸻

5️⃣ How this ties back to readmission outcomes (eventually)

Leadership will ask:

“Does this reduce readmissions?”

Your honest answer (and this is good science):

* First: prove engagement lift
* Then: show engaged → lower readmission
* Finally: combine into clinical ROI

Because now you can say:

“This many readmissions were prevented because outreach happened.”

That’s the endgame.

⸻

One-slide leadership summary (you can reuse this)

Before:
We contacted members based on risk alone.

Now:
We prioritize members where outreach changes behavior.

Result:
Fewer contacts, higher engagement, better member experience, clearer ROI.

⸻

If you want next, I can:

* Mock a real dashboard layout (tabs + metrics)
* Help you design a “who to call today” operational view
* Draft exact leadership slide titles
* Show how to combine readmission risk × uplift into one score

Just tell me which one you want to see.

#####
This is a great follow-up, because this is exactly where your idea becomes a Thinkubator / GenAI-first story, not “just analytics”.

Below I’ll be very concrete: what GenAI/LLMs/agents do, where they plug into your journey, and how leadership sees the value.

⸻

Where GenAI / LLMs / AI Agents Actually Improve Outcomes

Think of GenAI as solving three hard problems you currently have:

1. Understanding messy engagement data
2. Helping care teams decide what to do next
3. Scaling human judgment, not replacing it

⸻

1️⃣ GenAI for Member Journey Understanding (Sense-Making)

Problem today

* Engagement data is:
    * fragmented
    * noisy
    * text-heavy (notes, call outcomes, free text)
* Leaders and care managers cannot mentally reconstruct journeys at scale

GenAI solution: Journey Summarization Agent

What it does

* Takes structured events + unstructured notes
* Produces a concise, clinical-safe narrative of:
    * why the member was identified
    * what outreach occurred
    * what worked / failed
    * current engagement status

Example output

“Member discharged from SNF on 3/12. Identified as high readmission risk due to CHF and prior ED utilization. Two call attempts within 48h were unsuccessful; SMS sent and replied requesting callback. Engaged on 3/15, enrolled in Readmission Avoidance. No further outreach required.”

Why leadership cares

* Faster case review
* Reduced care manager cognitive load
* Consistent storytelling across teams

LLM role

* Summarization
* Contextualization
* Standardized language across programs

⸻

2️⃣ GenAI for Engagement Pattern Discovery (Why things work)

Problem today

* You know what happened
* You don’t know why it worked or failed

GenAI solution: Engagement Insight Agent

What it does

* Reads:
    * journey events
    * call outcomes
    * notes
    * program metadata
* Clusters journeys into behavioral archetypes

Example archetypes

* “Responds only to SMS after missed calls”
* “Engages once caregiver involved”
* “Declines repeatedly after multi-program outreach”
* “Late engager post-discharge day 5–7”

Why leadership cares

* Moves strategy from heuristics → evidence
* Enables program design changes, not just reporting

LLM role

* Pattern abstraction
* Semantic clustering
* Human-readable explanations

⸻

3️⃣ GenAI-Assisted Next Best Action (Decision Support)

Problem today

Care managers ask:

“What should I do next for this member?”

And answers are inconsistent.

GenAI solution: Next-Best-Action Copilot

Inputs

* Readmission risk score
* Engagement prediction score
* Journey context
* Program rules
* Past outreach outcomes

Outputs

* Recommended channel (call/SMS/email)
* Recommended timing
* Suggested script / framing
* Confidence + rationale

Example

“Recommend SMS outreach within next 24h. Member previously responded to SMS after missed calls. Avoid concurrent outreach from other programs.”

Why leadership cares

* Standardizes best practices
* Reduces variation across teams
* Scales expert judgment

Important
👉 This is decision support, not auto-action (safer + compliant).

⸻

4️⃣ AI Agents for Operational Monitoring & Governance

Problem today

* Issues discovered late:
    * SLA breaches
    * outreach delays
    * sudden engagement drops
* Requires manual investigation

AI Agent solution: Operational Watchdog Agent

What it does

* Continuously monitors journey metrics
* Detects anomalies:
    * delayed outreach for high-risk discharges
    * facility-specific engagement drops
    * channel failures

Example alert

“Engagement rate for CHF discharges from Facility X dropped 22% in the past 7 days. Primary driver: delayed first outreach (>72h).”

Why leadership cares

* Early warning system
* Proactive ops management
* Prevents downstream readmissions

⸻

5️⃣ GenAI for Uplift & Strategy Explanation (Trust Builder)

Problem today

Advanced models are hard to explain.

GenAI solution: Model Explainer Agent

What it does

* Translates:
    * uplift scores
    * engagement predictions
    * causal findings
        into plain English

Example

“Members discharged to home with CHF and prior ED visits show the highest incremental engagement when contacted within 48h via phone. Outreach has limited impact beyond day 5.”

Why leadership cares

* Transparency
* Adoption
* Faster decision cycles

⸻

6️⃣ How this improves outcomes (end-to-end)

Without GenAI

* Data exists but is under-used
* Insights lag reality
* Strategy changes are slow

With GenAI + agents

* Faster engagement
* Fewer wasted touches
* Better care manager experience
* Higher program ROI
* Stronger causal story

⸻

7️⃣ How to frame this for Thinkubator (this line works)

“We are using GenAI and agent-based intelligence to transform fragmented care-management touchpoints into actionable, real-time guidance—augmenting care managers’ judgment and improving engagement outcomes for high-risk members.”

⸻

8️⃣ Practical & safe rollout (important)

You can say this explicitly to leadership:

* Phase 1: Read-only summarization & insights
* Phase 2: Decision support (human-in-the-loop)
* Phase 3: Selective automation with guardrails

This shows maturity and responsibility.

⸻

If you want next, I can:

* Map GenAI components → exact GCP tools (Vertex, Gemini, BigQuery)
* Write Thinkubator-style one-paragraph GenAI justification
* Propose metrics to prove GenAI value
* Help you position this as augmenting CM, not replacing them

Just tell me what you want next.






















Title: Leveraging GenAI, LLMs, and AI Agents to Improve Care Management Engagement Outcomes

Overview:
This document outlines how Generative AI (GenAI), Large Language Models (LLMs), and AI agents can be applied to improve member engagement outcomes in Care Management programs, particularly for readmission avoidance. The focus is on augmenting human decision-making, improving operational efficiency, and enabling data-driven strategy.

---------------------------------------------------------------------

1. GenAI for Member Journey Understanding (Sense-Making)

Problem:
Engagement data is fragmented, noisy, and often stored in unstructured formats (notes, call outcomes, free text). It is difficult for care managers and leadership to reconstruct member journeys at scale.

Solution: Journey Summarization Agent

What it does:
- Combines structured data (events, timestamps) with unstructured data (notes)
- Generates concise summaries of member journeys
- Standardizes communication across teams

Example Output:
"Member discharged from SNF on 3/12. Identified as high readmission risk due to CHF and prior ED utilization. Two call attempts within 48h were unsuccessful; SMS sent and replied requesting callback. Engaged on 3/15, enrolled in Readmission Avoidance. No further outreach required."

Value:
- Faster case reviews
- Reduced cognitive load for care managers
- Consistent storytelling across teams

---------------------------------------------------------------------

2. GenAI for Engagement Pattern Discovery

Problem:
We can see what happened but not why it worked or failed.

Solution: Engagement Insight Agent

What it does:
- Analyzes journeys, notes, and outreach outcomes
- Identifies behavioral patterns and archetypes

Example Archetypes:
- Responds only to SMS after missed calls
- Engages once caregiver is involved
- Declines after multiple program contacts
- Late engager (day 5â7 post-discharge)

Value:
- Enables data-driven program design
- Moves strategy from heuristics to evidence

---------------------------------------------------------------------

3. GenAI-Assisted Next Best Action (Decision Support)

Problem:
Care managers lack consistent guidance on what to do next.

Solution: Next-Best-Action Copilot

Inputs:
- Readmission risk score
- Engagement prediction score
- Journey context
- Program rules
- Past outreach outcomes

Outputs:
- Recommended channel (call/SMS/email)
- Timing recommendations
- Suggested scripts
- Confidence and rationale

Example:
"Recommend SMS outreach within next 24h. Member previously responded to SMS after missed calls. Avoid concurrent outreach from other programs."

Value:
- Standardized best practices
- Reduced variability
- Improved efficiency

Note: This is decision support, not full automation.

---------------------------------------------------------------------

4. AI Agents for Operational Monitoring

Problem:
Operational issues (delays, drops in engagement) are detected late.

Solution: Operational Watchdog Agent

What it does:
- Monitors engagement metrics continuously
- Detects anomalies and SLA breaches

Example Alert:
"Engagement rate for CHF discharges from Facility X dropped 22% in the past 7 days due to delayed outreach (>72h)."

Value:
- Early detection of issues
- Proactive management
- Prevents downstream negative outcomes

---------------------------------------------------------------------

5. GenAI for Model Explanation and Trust

Problem:
Advanced models are difficult for stakeholders to understand.

Solution: Model Explainer Agent

What it does:
- Converts model outputs into plain-language explanations

Example:
"Members discharged with CHF and prior ED visits show highest engagement when contacted within 48h via phone. Limited impact after day 5."

Value:
- Increased trust and adoption
- Faster decision-making

---------------------------------------------------------------------

6. End-to-End Impact

Without GenAI:
- Fragmented insights
- Slow strategy updates
- Inefficient outreach

With GenAI and AI agents:
- Faster engagement
- Reduced wasted effort
- Improved care manager experience
- Higher ROI
- Clearer causal understanding

---------------------------------------------------------------------

7. Strategic Positioning Statement

"We are using GenAI and agent-based intelligence to transform fragmented care management touchpoints into actionable, real-time guidance, augmenting care managersâ decision-making and improving engagement outcomes for high-risk members."

---------------------------------------------------------------------

8. Safe Rollout Approach

Phase 1:
- Read-only summarization and insights

Phase 2:
- Decision support with human-in-the-loop

Phase 3:
- Selective automation with guardrails

This ensures compliance, trust, and controlled scaling.

---------------------------------------------------------------------




mmm
Yiwei has been a strong manager in providing clarity and direction for the team. She communicates expectations clearly and ensures everyone understands priorities and deliverables. She does an excellent job during sprint planning and backlog grooming by organizing work effectively, prioritizing high-impact items, and helping the team stay focused on what matters most. Her structured approach to planning has improved team alignment and execution.

Opportunity Area:
One opportunity for growth could be in creating even more visibility into longer-term strategic goals and cross-team dependencies. While short-term planning and prioritization are strong, additional context on broader roadmap direction could help the team anticipate future needs, align proactively, and make more strategic decisions.


Strength:
Yiwei has been a strong manager in providing clarity and direction for the team. She communicates expectations clearly and ensures everyone understands priorities and deliverables. She does an excellent job during sprint planning and backlog grooming by organizing work effectively, prioritizing high-impact items, and helping the team stay focused on what matters most. She is also thoughtful about longer-term strategic goals and cross-team dependencies, often working closely with DE teams and other stakeholders to ensure alignment and smooth execution.

Opportunity Area:
As the team continues to grow, one opportunity could be to further expand delegation of strategic ownership across team leads. Creating more opportunities for leads to drive certain planning and decision-making discussions could help strengthen leadership within the team and improve scalability.

This reads very strong because:

* Strengths are concrete and credible.
* Opportunity area is positive (not criticism).
* Shows you respect her leadership while suggesting growth.






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
