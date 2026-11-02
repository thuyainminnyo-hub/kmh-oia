from pkg_alpha.types import Widget as AlphaWidget, AlphaBase
from pkg_beta.types import Widget as BetaWidget, BetaBase

class Combined(AlphaBase, BetaBase):
    pass

def accept_both(left: AlphaWidget, right: BetaWidget) -> dict[str, AlphaWidget | BetaWidget]:
    return {"left": left, "right": right}
