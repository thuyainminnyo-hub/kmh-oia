"""Relative-import and alias-resolution fixture for package beta."""

from .types import Widget as BetaWidget, BetaBase, normalize_beta

class BetaChild(BetaBase):
    pass

def build_beta(value: BetaWidget) -> BetaWidget:
    normalized = normalize_beta(value)
    return BetaWidget()
