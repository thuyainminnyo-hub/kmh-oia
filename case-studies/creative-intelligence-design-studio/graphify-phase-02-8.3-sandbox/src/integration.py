from phase_02_8_3.pkg_alpha.types import Widget as AlphaWidget, AlphaBase
from phase_02_8_3.pkg_beta.types import Widget as BetaWidget, BetaBase


class Combined(AlphaBase, BetaBase):
    pass


def combine(a: AlphaWidget, b: BetaWidget) -> tuple[AlphaWidget, BetaWidget]:
    return a, b
