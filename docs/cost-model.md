# Cost model

`python -m labbench cost examples/assumptions.example.json`

This is a calculator, not a result. It contains no vendor prices and no organisation's real spend; the example files hold obviously illustrative numbers. A real business case needs your own figures.

## Why two billing shapes

- **per_task** (API tokens): every task solved locally avoids one cloud call, so savings grow with usage.
- **per_seat** (flat licence per user): partial displacement saves nothing. Savings exist only for licences that can actually be cancelled or downgraded (`removable_seat_share`). A workstation that handles 30% of someone's tasks does not reduce a flat licence.

Which one applies decides the whole answer, so state it first.

## Per seat, per month

```
fixed        = hardware_price / service_life_months + power_cost_per_month
               + support_hours_per_month * support_hourly_cost / seats
viable tasks = tasks_per_month * viable_share
failure cost = viable tasks * (1 - local_success_rate) * review_minutes_per_failure / 60 * hourly_cost
avoided      = per_task: viable tasks * local_success_rate * cloud_cost_per_task
               per_seat: removable_seat_share * cloud_seat_price_per_month
net          = avoided - fixed - failure cost
```

A failed local task is retried remotely, so it still incurs the cloud cost and adds human review time. `breakeven_viable_share` (per_task only) is the share of tasks that must be both suitable for local inference and routed to it for net to reach zero. `null` means failures cost more than successes save, so no share works.

## Inputs you must supply

| Input | Where it comes from |
| :--- | :--- |
| `local_success_rate` | Your own measured pass rate on your own tasks. The synthetic suite here is not a substitute. |
| `viable_share` | The share of real work that is the kind of task the local model handled. Needs a sample of real tasks, labelled by someone who knows the work. |
| `cloud_cost_per_task` or `cloud_seat_price_per_month`, `removable_seat_share` | Current contract or price list, dated. |
| `review_minutes_per_failure`, `hourly_cost` | Observed review effort and an agreed internal rate. |
| `hardware_price`, `service_life_months`, `support_*` | Quotes and your support model. Use the *incremental* cost: engineers usually get a laptop anyway, so count only the upgrade (memory, storage) that local inference needs. |

## What it leaves out

Model updates, evaluation effort, security review of the local setup, the cost of a wrong answer that nobody catches, and any quality difference the success rate does not capture. Treat a positive result as a reason to run a pilot, not as a forecast.

## A different machine

A newer or larger workstation changes the hardware price and the speed, not the method. Until that machine is measured with this suite, it is a target profile with estimated figures, not a tested one.
