import math
import time

from tsp.models import City, SolveResult

DistanceMatrix = list[list[float]]


def build_distance_matrix(
    cities: tuple[City, ...] | list[City],
    round_distances: bool = False,
) -> DistanceMatrix:
    count = len(cities)
    distances = [[0.0] * count for _ in range(count)]
    for first in range(count):
        for second in range(first + 1, count):
            distance = math.hypot(
                cities[first].x - cities[second].x,
                cities[first].y - cities[second].y,
            )
            if round_distances:
                distance = float(math.floor(distance + 0.5))
            distances[first][second] = distance
            distances[second][first] = distance
    return distances


def route_distance(route: list[int] | tuple[int, ...], distances: DistanceMatrix) -> float:
    if len(route) < 2:
        return 0.0
    return sum(
        distances[route[index]][route[(index + 1) % len(route)]]
        for index in range(len(route))
    )


def nearest_neighbor_route(distances: DistanceMatrix, start: int) -> list[int]:
    count = len(distances)
    if not 0 <= start < count:
        raise ValueError("Starting city index is out of range.")

    route = [start]
    unvisited = set(range(count))
    unvisited.remove(start)
    while unvisited:
        current = route[-1]
        next_city = min(
            unvisited,
            key=lambda city: (distances[current][city], city),
        )
        route.append(next_city)
        unvisited.remove(next_city)
    return route


def _two_opt_improve(route: list[int], distances: DistanceMatrix) -> bool:
    count = len(route)
    for first_edge in range(count - 1):
        for second_edge in range(first_edge + 2, count):
            if first_edge == 0 and second_edge == count - 1:
                continue
            first = route[first_edge]
            next_first = route[first_edge + 1]
            second = route[second_edge]
            next_second = route[(second_edge + 1) % count]
            gain = (
                distances[first][next_first]
                + distances[second][next_second]
                - distances[first][second]
                - distances[next_first][next_second]
            )
            if gain > 1e-9:
                route[first_edge + 1 : second_edge + 1] = reversed(
                    route[first_edge + 1 : second_edge + 1]
                )
                return True
    return False


def _relocate_improve(route: list[int], distances: DistanceMatrix) -> bool:
    count = len(route)
    if count < 3:
        return False

    for source_index in range(count):
        city = route[source_index]
        before = route[source_index - 1]
        after = route[(source_index + 1) % count]
        removal_change = distances[before][after] - distances[before][city] - distances[
            city
        ][after]

        shortened = route[:source_index] + route[source_index + 1 :]
        for insertion_index in range(count):
            if insertion_index == source_index:
                continue
            left = shortened[insertion_index - 1]
            right = shortened[insertion_index % len(shortened)]
            insertion_change = (
                distances[left][city]
                + distances[city][right]
                - distances[left][right]
            )
            if removal_change + insertion_change < -1e-9:
                route[:] = (
                    shortened[:insertion_index]
                    + [city]
                    + shortened[insertion_index:]
                )
                return True
    return False


def improve_route(route: list[int], distances: DistanceMatrix) -> list[int]:
    improved = route.copy()
    while True:
        changed = False
        while _two_opt_improve(improved, distances):
            changed = True
        while _relocate_improve(improved, distances):
            changed = True
        if not changed:
            return improved


def choose_start_indices(city_count: int, requested_starts: int) -> list[int]:
    if city_count < 1:
        raise ValueError("At least one city is required.")
    if requested_starts < 1:
        raise ValueError("The number of starting points must be positive.")
    start_count = min(city_count, requested_starts)
    return [(index * city_count) // start_count for index in range(start_count)]


def solve_tsp(
    cities: tuple[City, ...] | list[City],
    requested_starts: int = 12,
    round_distances: bool = False,
) -> SolveResult:
    if not cities:
        raise ValueError("At least one city is required.")

    started = time.perf_counter()
    distances = build_distance_matrix(cities, round_distances)
    starts = choose_start_indices(len(cities), requested_starts)
    initial_route = min(
        (nearest_neighbor_route(distances, start) for start in starts),
        key=lambda route: route_distance(route, distances),
    )
    initial_distance = route_distance(initial_route, distances)
    best_route = improve_route(initial_route, distances)
    final_distance = route_distance(best_route, distances)
    improvement = (
        100.0 * (initial_distance - final_distance) / initial_distance
        if initial_distance > 0
        else 0.0
    )

    return SolveResult(
        initial_route=tuple(initial_route),
        route=tuple(best_route),
        initial_distance=initial_distance,
        final_distance=final_distance,
        improvement_percent=improvement,
        elapsed_seconds=time.perf_counter() - started,
        starts_used=len(starts),
    )
