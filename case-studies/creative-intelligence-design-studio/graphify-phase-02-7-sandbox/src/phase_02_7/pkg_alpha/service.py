"""Relative-import and alias-resolution fixture for package alpha."""

from .types import Widget as AlphaWidget, AlphaBase, AlphaMixin, normalize_alpha

class AlphaChild(AlphaBase, AlphaMixin):
    pass

def build_alpha(value: AlphaWidget) -> AlphaWidget:
    normalized = normalize_alpha(value)
    return AlphaWidget()
