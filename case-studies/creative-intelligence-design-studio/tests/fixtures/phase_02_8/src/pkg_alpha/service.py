from .types import Widget as AlphaWidget, AlphaBase, AlphaMixin, normalize_alpha

class AlphaChild(AlphaBase, AlphaMixin):
    pass

def parameter_only(value: AlphaWidget):
    return value

def return_only() -> AlphaWidget:
    return AlphaWidget()

def same_line(value: AlphaWidget) -> AlphaWidget:
    return value

annotated_value: AlphaWidget

def outer():
    def inner(value: AlphaWidget) -> AlphaWidget:
        return normalize_alpha(value)
    return inner


def forward_reference(value: "AlphaWidget") -> "AlphaWidget":
    return value

def generic_reference(values: list[AlphaWidget]) -> dict[str, AlphaWidget]:
    return {str(index): value for index, value in enumerate(values)}
