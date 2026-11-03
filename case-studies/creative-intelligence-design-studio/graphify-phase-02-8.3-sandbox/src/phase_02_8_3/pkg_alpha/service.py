from .types import Widget as AlphaWidget, AlphaBase, AlphaMixin


def module_outer():
    def module_inner(value: AlphaWidget) -> AlphaWidget:
        return value
    return module_inner


def local_outer():
    from .types import Widget as LocalWidget
    def local_inner(value: LocalWidget):
        return value
    return local_inner


class AlphaChild(AlphaBase, AlphaMixin):
    pass
