"""Illustrative procurement controls, not a legal compliance determination."""

from decimal import Decimal, ROUND_HALF_UP
from datetime import date, timedelta

SCENARIOS = {
    "pricing": {
        "label": "JOC price assurance",
        "owner": "Facilities project manager",
        "operation": "register_reviewed_work_order",
        "department": "General Services",
        "title": "Civic facility cooling repair",
        "amount_cents": 14102400,
        "source": "D1",
        "evidence": {
            "catalog_basis": False,
            "funding_review": False,
            "conflict_review": False,
        },
        "inputs": {
            "base_cents": 12000000,
            "coefficient": "1.04",
            "approved_index": "1.08",
            "submitted_index": "1.13",
        },
    },
    "invoice": {
        "label": "Invoice evidence",
        "owner": "Department contract administrator",
        "operation": "register_invoice_review_packet",
        "department": "General Services",
        "title": "Roof maintenance payment application",
        "amount_cents": 4800000,
        "source": "D2",
        "evidence": {
            "signed_work_order": True,
            "acceptance_record": False,
            "invoice_support": False,
            "compliance_review": False,
        },
        "inputs": {
            "contract_cents": 12000000,
            "prior_paid_cents": 3600000,
            "accepted_cumulative_cents": 8400000,
            "invoice_cents": 4800000,
        },
    },
    "emergency": {
        "label": "Emergency justification",
        "owner": "Chief Procurement Officer",
        "operation": "register_emergency_review_packet",
        "department": "Public Works • fictional scenario",
        "title": "Stormwater pump stabilization",
        "amount_cents": 18500000,
        "source": "D3",
        "evidence": {
            "incident_summary": False,
            "cost_ceiling": False,
            "cpo_determination": False,
            "council_path_review": False,
        },
        "inputs": {"elapsed_hours": 26, "contact_hour": None, "form_hour": None},
    },
    "renewal": {
        "label": "Renewal readiness",
        "owner": "Procurement contract manager",
        "operation": "register_renewal_review_task",
        "department": "Citywide services • fictional scenario",
        "title": "Facility inspection services",
        "amount_cents": 24000000,
        "source": "D4",
        "evidence": {
            "clause_review": False,
            "performance_review": False,
            "budget_review": False,
            "competition_path_review": False,
        },
        "inputs": {"as_of": "2026-10-07", "end_date": "2027-01-15", "notice_days": 90},
    },
}
EVIDENCE = {
    "catalog_basis": "Catalog and index basis checked",
    "funding_review": "Funding authority checked",
    "conflict_review": "Conflict disclosure reviewed",
    "signed_work_order": "Signed work order reference",
    "acceptance_record": "Service acceptance evidence",
    "invoice_support": "Invoice support checklist",
    "compliance_review": "Applicable compliance review",
    "incident_summary": "Nature, cause and impact documented",
    "cost_ceiling": "Not-to-exceed estimate reviewed",
    "cpo_determination": "CPO determination recorded (simulation)",
    "council_path_review": "Council approval path reviewed",
    "clause_review": "Extracted notice clause verified",
    "performance_review": "Performance evaluation reviewed",
    "budget_review": "Funding reviewed",
    "competition_path_review": "Competition / renewal authority reviewed",
}


def money(base, coefficient, index):
    return int(
        (Decimal(base) * Decimal(coefficient) * Decimal(index)).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )


def evaluate(record):
    kind = record["kind"]
    x = record["inputs"]
    ev = record["evidence"]
    blockers = [EVIDENCE[k] for k, v in ev.items() if not v]
    metrics = {}
    warnings = []
    if kind == "pricing":
        expected = money(x["base_cents"], x["coefficient"], x["approved_index"])
        submitted = money(x["base_cents"], x["coefficient"], x["submitted_index"])
        metrics = {
            "expected_cents": expected,
            "submitted_cents": submitted,
            "variance_cents": submitted - expected,
        }
        if submitted != expected:
            blockers.append("Resolve pricing variance before review approval")
        warnings.append(
            "Illustrative index formula and values; verify the actual contract calculation and effective quarter."
        )
    elif kind == "invoice":
        available = x["accepted_cumulative_cents"] - x["prior_paid_cents"]
        metrics = {
            "available_cents": available,
            "invoice_cents": x["invoice_cents"],
            "remaining_contract_cents": x["contract_cents"]
            - x["prior_paid_cents"]
            - x["invoice_cents"],
        }
        if available < 0 or x["accepted_cumulative_cents"] > x["contract_cents"]:
            blockers.append("Accepted value falls outside contract bounds")
        if x["invoice_cents"] > available:
            blockers.append("Invoice exceeds accepted unpaid value")
        warnings.append(
            "Readiness recommendation only; does not release funds or post a payable."
        )
    elif kind == "emergency":
        for key, limit in [("contact_hour", 8), ("form_hour", 24)]:
            value = x[key]
            label = "CPO contact" if key == "contact_hour" else "Justification form"
            status = (
                ("overdue" if x["elapsed_hours"] > limit else "due")
                if value is None
                else ("late" if value > limit else "recorded")
            )
            metrics[key] = {
                "limit_hours": limit,
                "recorded_hour": value,
                "status": status,
            }
            if value is None:
                blockers.append(label + " evidence missing")
            if value is not None and value > x["elapsed_hours"]:
                blockers.append(label + " cannot be in the future")
            if status in ("late", "overdue"):
                warnings.append(
                    label
                    + " missed the illustrative fixture interval; escalate and preserve the actual timestamp."
                )
        warnings.append(
            "Synthetic 8-hour/24-hour fixture targets; clock is an evidence aid. CPO determines emergency qualification; current authority and council requirements need confirmation."
        )
    else:
        deadline = date.fromisoformat(x["end_date"]) - timedelta(days=x["notice_days"])
        left = (deadline - date.fromisoformat(x["as_of"])).days
        metrics = {
            "notice_deadline": deadline.isoformat(),
            "days_to_notice": left,
            "notice_days": x["notice_days"],
        }
        if left < 0:
            warnings.append(
                "Notice deadline has passed in the illustrative clause; obtain legal review, never backdate."
            )
        warnings.append(
            "90-day notice is a synthetic contract term, not a citywide rule. Dates use calendar days."
        )
    return {
        "ready": not blockers,
        "blockers": blockers,
        "metrics": metrics,
        "warnings": warnings,
    }
