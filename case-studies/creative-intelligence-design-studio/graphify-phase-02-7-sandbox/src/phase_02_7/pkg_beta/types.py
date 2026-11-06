"""Synthetic beta declarations intentionally reuse the Widget name."""

class Widget:
    kind = "beta"

class BetaBase:
    pass

def normalize_beta(value: Widget) -> Widget:
    return value
