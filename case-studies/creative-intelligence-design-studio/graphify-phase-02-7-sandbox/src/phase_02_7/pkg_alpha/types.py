"""Synthetic alpha package declarations."""

class Widget:
    kind = "alpha"

class AlphaBase:
    pass

class AlphaMixin:
    pass

def normalize_alpha(value: Widget) -> Widget:
    return value
