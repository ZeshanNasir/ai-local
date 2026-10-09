"""Break-even arithmetic for local versus cloud inference. It computes; it does not know anyone's prices.

Two billing shapes, because they behave differently:

per_task  cloud cost scales with usage (API tokens). Each locally-solved task avoids one cloud call.
per_seat  cloud cost is a flat licence per user. Partial displacement saves nothing; only licences that
          can actually be cancelled (removable_seat_share) count as savings.

Local failures cost human review time in both shapes. Hardware, power and support are fixed per seat."""


def _fixed_per_seat(a):
    return (a["hardware_price"] / a["service_life_months"] + a["power_cost_per_month"]
            + a["support_hours_per_month"] * a["support_hourly_cost"] / a["seats"])


def evaluate(a):
    """Monthly figures per seat. For per_task billing also the local-viable share at which a seat breaks even."""
    fixed = _fixed_per_seat(a)
    viable_tasks = a["tasks_per_month"] * a["viable_share"]
    failure_cost = viable_tasks * (1 - a["local_success_rate"]) * a["review_minutes_per_failure"] / 60 * a["hourly_cost"]
    billing = a.get("cloud_billing", "per_task")
    if billing == "per_seat":
        avoided = a["removable_seat_share"] * a["cloud_seat_price_per_month"]
        breakeven = None
    else:
        avoided = viable_tasks * a["local_success_rate"] * a["cloud_cost_per_task"]
        gain = a["local_success_rate"] * a["cloud_cost_per_task"]
        loss = (1 - a["local_success_rate"]) * a["review_minutes_per_failure"] / 60 * a["hourly_cost"]
        breakeven = fixed / (a["tasks_per_month"] * (gain - loss)) if gain > loss else None
    net = avoided - fixed - failure_cost
    return {
        "billing": billing,
        "monthly_fixed_local_cost_per_seat": round(fixed, 2),
        "monthly_cloud_cost_avoided_per_seat": round(avoided, 2),
        "monthly_failure_review_cost_per_seat": round(failure_cost, 2),
        "monthly_net_per_seat": round(net, 2),
        "breakeven_viable_share": None if breakeven is None else round(breakeven, 3),
        "breakeven_possible": breakeven is not None and breakeven <= 1,
    }


def sensitivity(a, success_rates=(0.5, 0.6, 0.7, 0.8, 0.9)):
    return {r: evaluate({**a, "local_success_rate": r})["monthly_net_per_seat"] for r in success_rates}
