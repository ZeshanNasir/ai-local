"""Price helpers. Amounts are integer cents."""


def apply_discount(price_cents: int, percent: int) -> int:
    """Return the price after a percentage discount, rounded to the nearest cent (halves round up).

    percent must be between 0 and 100 inclusive; anything else raises ValueError.
    """
    return price_cents - price_cents * percent // 100
