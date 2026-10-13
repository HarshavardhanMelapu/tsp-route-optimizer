from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    identifier: str
    x: float
    y: float


@dataclass(frozen=True)
class TspInstance:
    name: str
    cities: tuple[City, ...]
    round_distances: bool = False
    source_format: str = "CSV"


@dataclass(frozen=True)
class SolveResult:
    initial_route: tuple[int, ...]
    route: tuple[int, ...]
    initial_distance: float
    final_distance: float
    improvement_percent: float
    elapsed_seconds: float
    starts_used: int
