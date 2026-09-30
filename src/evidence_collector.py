"""Stage 14 deterministic evidence collector."""
from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceItem:
    name: str
    value: str

@dataclass(frozen=True)
class EvidencePackage:
    items: tuple[EvidenceItem, ...]
    complete: bool

class EvidenceCollector:
    """Collect explicitly supplied evidence without fabricating production facts."""
    def collect(self, evidence: dict[str, str], *, required: tuple[str, ...]) -> EvidencePackage:
        if not required: raise ValueError("required evidence keys are required")
        items=[]
        for name in required:
            value=evidence.get(name, "")
            if not isinstance(value, str): raise ValueError("evidence values must be strings")
            items.append(EvidenceItem(name, value.strip()))
        complete=all(item.value for item in items)
        return EvidencePackage(tuple(items), complete)
    def require_complete(self, package: EvidencePackage) -> None:
        if not package.complete:
            missing=", ".join(item.name for item in package.items if not item.value)
            raise RuntimeError(f"evidence package incomplete: {missing}")
