"""Absolute multi-package import and same-name disambiguation fixture."""

from phase_02_7.pkg_alpha.types import Widget as AlphaWidget, AlphaBase, normalize_alpha
from phase_02_7.pkg_beta.types import Widget as BetaWidget, BetaBase, normalize_beta

class CombinedWidget(AlphaBase, BetaBase):
    pass

def merge_widgets(left: AlphaWidget, right: BetaWidget):
    normalize_alpha(left)
    normalize_beta(right)
    return AlphaWidget(), BetaWidget()
