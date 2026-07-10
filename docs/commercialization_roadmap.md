# Commercialization Roadmap — Plenara

A conservative, phased path from a synthetic prototype to a potential healthcare
operations SaaS. Each phase has a goal, what gets built, what is explicitly not
allowed yet, and the evidence needed to advance.

> Handling real PHI would require appropriate legal, security, compliance, and
> operational review — including agreements such as a Business Associate
> Agreement (BAA) where applicable. Nothing in Phases 0–2 touches real PHI.

---

## Phase 0 — Synthetic product demo (current)

- **Goal:** Prove the concept and communicate it clearly on synthetic data.
- **Build:** Three readiness workflows, shared READY/NEEDS REVIEW/BLOCKED states,
  command center, executive insights, unified work queue, data-quality checks,
  SQL portfolio, tests, and documentation.
- **Not allowed yet:** Any real PHI, integrations, submission, auth, or
  production deployment.
- **Evidence to advance:** A reviewer/operator understands the product quickly;
  the synthetic demo is credible and honest.

## Phase 1 — Design-partner discovery, no PHI

- **Goal:** Validate the problem and readiness picture with real operators.
- **Build:** Demo walkthroughs, discovery interviews, a one-page brief, and a
  prioritized list of the highest-friction workflows.
- **Not allowed yet:** Real PHI, integrations, or pilots. Synthetic data only.
- **Evidence to advance:** Multiple operators confirm the pain and the value; a
  clear first workflow to focus on.

## Phase 2 — Workflow mapping with synthetic / de-identified examples

- **Goal:** Map a real workflow in detail without real PHI.
- **Build:** Workflow maps, refined rules for one target workflow, and
  synthetic/de-identified example scenarios that mirror a partner's process.
- **Not allowed yet:** Real PHI ingestion, live integrations, or production infra.
- **Evidence to advance:** A partner agrees the mapped workflow and rules match
  reality and would be useful in practice.

## Phase 3 — Security architecture and legal review

- **Goal:** Design the controls required before any real data.
- **Build:** Security architecture (encryption in transit and at rest, RBAC,
  audit logging, secrets management, data retention), a threat model, and a
  compliance/legal review plan — including BAA scope where applicable.
- **Not allowed yet:** Real PHI until controls and agreements are in place.
- **Evidence to advance:** Approved security design and legal/compliance sign-off
  path; executed agreements where required.

## Phase 4 — Limited pilot under proper agreements

- **Goal:** Run a small, controlled pilot with a design partner.
- **Build:** A minimal, secured deployment for one workflow, with monitoring,
  access controls, audit logging, and human-in-the-loop review — under a signed
  BAA and agreed data-handling terms.
- **Not allowed yet:** Broad rollout, autonomous decisions, approval/denial
  prediction, or claim submission.
- **Evidence to advance:** Pilot demonstrates real operational value with controls
  holding; partner and compliance both satisfied.

## Phase 5 — Production healthcare operations SaaS

- **Goal:** Operate as a real, multi-tenant healthcare operations SaaS.
- **Build:** Production infrastructure, tenancy and access controls, integrations
  as needed, reliability/monitoring, and a supported product — all under ongoing
  security, compliance, and legal governance.
- **Not allowed ever (as scoped here):** Overclaiming; autonomous clinical or
  billing decisions; anything that removes the human from the loop.
- **Evidence to advance:** Sustained value, security, and compliance in production.

---

**Guiding rule:** the product stays explainable and human-in-the-loop, and never
advances a phase without the evidence and controls that phase requires.
