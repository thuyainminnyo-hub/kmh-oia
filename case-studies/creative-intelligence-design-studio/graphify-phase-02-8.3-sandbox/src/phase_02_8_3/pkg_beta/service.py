from .types import Widget as BetaWidget, BetaBase


def beta_outer():
    def beta_inner(value: BetaWidget):
        return value
    return beta_inner


class BetaChild(BetaBase):
    pass
