from dataclasses import dataclass
from collections import defaultdict

@dataclass(frozen=True)
class InstanceAnomaly:
    instance_id: str
    metric: str
    severity: str
    delta: float

@dataclass(frozen=True)
class SystemicAnomaly:
    metric: str
    instance_count: int
    instances: tuple[str, ...]
    mean_delta: float
    severity: str
    systemic: bool

class CrossInstanceAnomalyCorrelator:
    def correlate(self, anomalies, minimum_instances=2):
        if minimum_instances < 1:
            raise ValueError('minimum_instances must be positive')
        groups = defaultdict(list)
        for item in anomalies:
            if not item.instance_id or not item.metric:
                raise ValueError('instance_id and metric are required')
            groups[item.metric].append(item)
        rank = {'NONE': 0, 'MEDIUM': 1, 'HIGH': 2}
        result = []
        for metric, items in sorted(groups.items()):
            instances = tuple(sorted({x.instance_id for x in items}))
            mean_delta = sum(x.delta for x in items) / len(items)
            severity = max((x.severity for x in items), key=lambda x: rank.get(x, 0))
            result.append(SystemicAnomaly(metric, len(instances), instances, mean_delta, severity, len(instances) >= minimum_instances))
        return tuple(result)
