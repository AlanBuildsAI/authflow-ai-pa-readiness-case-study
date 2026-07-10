"""
Deterministic executive insights for Plenara.

Turns the current synthetic scenario into a small set of plain-English,
data-derived insights an operations leader could read at a glance. Every insight
is computed from the bundled/generated synthetic data — nothing is hardcoded.

This module contains analysis logic only (no Streamlit, no I/O). The Streamlit
app imports and renders these results.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from . import metrics
from .readiness import BLOCKED, READY
from .workqueue import build_unified_work_queue, summarize_top_actions

# Minimum group size before a payer/clinic is eligible to be "highlighted",
# so a tiny group with one bad record doesn't dominate the narrative.
MIN_GROUP_SIZE = 5


@dataclass
class Insight:
    """One executive insight: a sentence plus the supporting value."""

    text: str
    metric: str = ""
    value: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {"text": self.text, "metric": self.metric, "value": self.value}


def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def _money(x: float) -> str:
    return f"${x:,.0f}"


def _payer_status_frame(onb_df: pd.DataFrame, claims_df: pd.DataFrame) -> pd.DataFrame:
    """Stack onboarding + claims into one (payer, status) frame."""
    frames = []
    if not onb_df.empty and {"payer_name_mock", "readiness_status"} <= set(onb_df.columns):
        frames.append(onb_df[["payer_name_mock", "readiness_status"]].rename(columns={"readiness_status": "status"}))
    if not claims_df.empty and {"payer_name_mock", "claim_readiness_status"} <= set(claims_df.columns):
        frames.append(claims_df[["payer_name_mock", "claim_readiness_status"]].rename(columns={"claim_readiness_status": "status"}))
    if not frames:
        return pd.DataFrame(columns=["payer_name_mock", "status"])
    return pd.concat(frames, ignore_index=True)


def highest_blocked_rate_payer(onb_df: pd.DataFrame, claims_df: pd.DataFrame) -> Insight:
    frame = _payer_status_frame(onb_df, claims_df)
    if frame.empty:
        return Insight("No payer data available in the current scenario.", "blocked_rate", None)
    grp = frame.groupby("payer_name_mock")["status"]
    rate = grp.apply(lambda s: (s == BLOCKED).mean())
    counts = grp.size()
    eligible = rate[counts >= MIN_GROUP_SIZE]
    if eligible.empty:
        eligible = rate
    payer = eligible.idxmax()
    value = float(eligible.max())
    return Insight(
        f"{payer} has the highest blocked rate ({_pct(value)}) across onboarding and claims.",
        "blocked_rate",
        {"payer": payer, "rate": round(value, 4)},
    )


def weakest_readiness_workflow(pa_df: pd.DataFrame, onb_df: pd.DataFrame, claims_df: pd.DataFrame) -> Insight:
    rates = {
        "Prior authorization": metrics.readiness_rate(pa_df) if not pa_df.empty else None,
        "Provider onboarding": metrics.readiness_rate(onb_df) if not onb_df.empty else None,
        "Revenue cycle": metrics.readiness_rate(claims_df, "claim_readiness_status") if not claims_df.empty else None,
    }
    rates = {k: v for k, v in rates.items() if v is not None}
    if not rates:
        return Insight("No workflow data available in the current scenario.", "ready_rate", None)
    workflow = min(rates, key=rates.get)
    value = rates[workflow]
    return Insight(
        f"{workflow} has the weakest readiness rate in the current scenario ({_pct(value)} ready).",
        "ready_rate",
        {"workflow": workflow, "ready_rate": round(value, 4)},
    )


def largest_owner_workqueue(pa_df: pd.DataFrame, onb_df: pd.DataFrame, claims_df: pd.DataFrame) -> Insight:
    queue = build_unified_work_queue(pa_df, onb_df, claims_df)
    if queue.empty:
        return Insight("There is no non-ready work in the current scenario.", "workqueue", None)
    counts = queue["owner_team"].astype(str).value_counts()
    owner = counts.idxmax()
    value = int(counts.max())
    return Insight(
        f"Owner team '{owner}' carries the largest non-ready workload ({value} items).",
        "workqueue",
        {"owner_team": owner, "items": value},
    )


def highest_revenue_at_risk_payer(claims_df: pd.DataFrame) -> Insight:
    by_payer = metrics.revenue_at_risk_by_payer(claims_df)
    if not by_payer:
        return Insight("No synthetic revenue at risk in the current scenario.", "revenue_at_risk", None)
    payer = max(by_payer, key=by_payer.get)
    value = by_payer[payer]
    return Insight(
        f"{payer} carries the highest synthetic revenue-at-risk ({_money(value)}).",
        "revenue_at_risk",
        {"payer": payer, "amount": round(value, 2)},
    )


def most_common_blocker_category(pa_df: pd.DataFrame, onb_df: pd.DataFrame, claims_df: pd.DataFrame) -> Insight:
    queue = build_unified_work_queue(pa_df, onb_df, claims_df)
    if queue.empty:
        return Insight("No blockers in the current scenario.", "blocker_category", None)
    cats = queue.loc[queue["blocker_category"].astype(str) != "none", "blocker_category"].value_counts()
    if cats.empty:
        return Insight("No blocking categories in the current scenario.", "blocker_category", None)
    category = str(cats.idxmax())
    value = int(cats.max())
    return Insight(
        f"The most common blocker category is '{category}' ({value} records).",
        "blocker_category",
        {"category": category, "count": value},
    )


def aging_work_summary(claims_df: pd.DataFrame) -> Insight:
    if claims_df.empty:
        return Insight("No claims to age in the current scenario.", "aging", None)
    buckets = metrics.aging_bucket_distribution(claims_df)
    aged = int(buckets.get("61-90", 0) + buckets.get("90+", 0))
    total = len(claims_df)
    share = aged / total if total else 0.0
    return Insight(
        f"Aging work is concentrated in {aged} claims older than 60 days ({_pct(share)} of claims).",
        "aging",
        {"aged_60_plus": aged, "share": round(share, 4)},
    )


def prioritize_today(pa_df: pd.DataFrame, onb_df: pd.DataFrame, claims_df: pd.DataFrame) -> str:
    """Single 'what to prioritize today' line from the top work-queue action."""
    queue = build_unified_work_queue(pa_df, onb_df, claims_df)
    actions = summarize_top_actions(queue, limit=1)
    if not actions:
        return "No high-priority actions in the current scenario."
    a = actions[0]
    impact = f" (synthetic impact {_money(a['synthetic_impact'])})" if a["synthetic_impact"] else ""
    return f"[{a['module']}] {a['recommended_action']} — {a['affected_records']} record(s){impact}."


def build_executive_insights(
    pa_df: pd.DataFrame,
    onb_df: pd.DataFrame,
    claims_df: pd.DataFrame,
) -> list[Insight]:
    """Return the five headline executive insights for the current scenario."""
    return [
        weakest_readiness_workflow(pa_df, onb_df, claims_df),
        highest_blocked_rate_payer(onb_df, claims_df),
        largest_owner_workqueue(pa_df, onb_df, claims_df),
        highest_revenue_at_risk_payer(claims_df),
        most_common_blocker_category(pa_df, onb_df, claims_df),
    ]
