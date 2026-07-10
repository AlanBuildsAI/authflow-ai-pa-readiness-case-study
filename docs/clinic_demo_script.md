# Clinic Demo Script — Plenara (10 minutes)

A synthetic-only walkthrough for a clinic operations manager, prior authorization
manager, or revenue cycle manager. Goal: show how Plenara turns fragmented
operational work into one explainable readiness picture — and open a
design-partner conversation.

> Say this up front and keep it visible: **everything is synthetic/mock data —
> no PHI, no real patient/provider/payer/claims data, no integrations, and no
> production use.** Plenara is human-in-the-loop workflow support, not autonomous
> decisions, not clinical decision support, and not approval/denial prediction.

**Setup:** run `PYTHONPATH=src streamlit run streamlit_app.py` (or open the live
demo). Use the sidebar **scenario** selector to pick an operating posture.

---

### 1. Opening — the operational problem (1 min)
"Prior authorization, provider onboarding, and lab-claim readiness usually live in
different systems. Teams lose time finding what's blocked, why, and who owns it.
Let me show a synthetic version of one operations picture that pulls those three
together."

### 2. Synthetic-only framing (30 sec)
"Every number here is fabricated for demonstration. No real patient, provider, or
payer data. The point is the workflow and the analytics, not the specific figures."

### 3. Command center (1 min)
Open **Command center**. "This is the daily starting point — five headline KPIs:
critical blockers, aging claims 60+, unassigned work, synthetic revenue at risk,
and overall readiness rate."

### 4. Top KPIs (1 min)
Walk the five KPI cards. "In this scenario, this is how much work is blocked, how
much is aging, and how much is unowned — the things a lead wants before drilling in."

### 5. Executive insights (1.5 min)
Open **Executive insights**. "These are computed from the data, not hardcoded —
the weakest workflow, the payer with the highest blocked rate, the owner team with
the biggest backlog, the payer carrying the most synthetic revenue at risk, and the
most common blocker. Then a single 'what to prioritize today.'"

### 6. Unified work queue (1.5 min)
Open **Work queue**. "One prioritized queue across all three workflows. Each row
has a severity, an owner, an age, a blocker category, and a recommended next
action. High severity — blocked and aging, high synthetic impact, or unassigned —
sorts to the top."

### 7. One prior auth case (1 min)
Open **Prior auth**, pick a BLOCKED case. "Here's a synthetic PA case: its status,
the specific readiness blockers, the recommended next action, and exactly what
would move it to READY."

### 8. One provider onboarding record (1 min)
Open **Provider onboarding**. "The clinic × payer readiness matrix shows where
onboarding is healthy vs. stuck. The queue lists blocked and aging records with
their blocker category and owner."

### 9. One revenue-cycle claim (1 min)
Open **Revenue cycle**. "Clean-claim readiness, aging buckets, and a denial-risk
category — which is a synthetic operational signal, not a prediction. Pick a claim
to see its blockers and the recommended next action."

### 10. Recommended next actions (30 sec)
"Everything ends in a concrete, human-readable next action — verify eligibility,
request documentation, assign an owner, resolve timely-filing risk. Plenara
prioritizes; your team decides."

### 11. What a real pilot would require (30 sec)
"To use this with real data, we'd need legal, security, and compliance review —
encryption, access controls, audit logging, and appropriate agreements such as a
BAA. Today it's a synthetic prototype by design."

### 12. Design-partner questions (30 sec)
- Where does your team currently lose the most time?
- Which workflow creates the most rework?
- How do you prioritize blocked cases today?
- Who owns PA, onboarding, and claim readiness issues?
- Which metrics would matter most to your team?
- What would make this useful enough to pilot?

---

**Close:** "The goal today isn't to sell a system — it's to learn whether this
readiness picture matches how your team actually works, using synthetic data
until there's a proper path to real data."
