import unittest

from tsp.io import parse_csv, parse_instance, parse_tsplib
from tsp.models import City
from tsp.solver import (
    build_distance_matrix,
    choose_start_indices,
    improve_route,
    nearest_neighbor_route,
    route_distance,
    solve_tsp,
)


class DatasetParsingTests(unittest.TestCase):
    def test_csv_with_headers_and_ids(self) -> None:
        instance = parse_csv("id,x,y\nA,0,0\nB,3,4\n", "cities.csv")
        self.assertEqual([city.identifier for city in instance.cities], ["A", "B"])
        self.assertEqual(instance.name, "cities")
        self.assertFalse(instance.round_distances)

    def test_csv_without_header_and_with_ids(self) -> None:
        instance = parse_csv("A,0,0\nB,3,4\n")
        self.assertEqual([(city.x, city.y) for city in instance.cities], [(0, 0), (3, 4)])

    def test_tsplib_euc_2d_rounds_distances(self) -> None:
        instance = parse_tsplib(
            "NAME: tiny\nTYPE: TSP\nDIMENSION: 2\n"
            "EDGE_WEIGHT_TYPE: EUC_2D\nNODE_COORD_SECTION\n"
            "1 0 0\n2 1 1\nEOF\n"
        )
        self.assertEqual(instance.name, "tiny")
        self.assertTrue(instance.round_distances)
        distances = build_distance_matrix(instance.cities, instance.round_distances)
        self.assertEqual(distances[0][1], 1.0)

    def test_tsplib_rejects_unsupported_edge_weight_type(self) -> None:
        with self.assertRaisesRegex(ValueError, "Only TSPLIB"):
            parse_tsplib(
                "DIMENSION: 2\nEDGE_WEIGHT_TYPE: GEO\n"
                "NODE_COORD_SECTION\n1 0 0\n2 1 1\n"
            )

    def test_parser_rejects_non_finite_coordinates(self) -> None:
        with self.assertRaisesRegex(ValueError, "finite"):
            parse_csv("x,y\n0,0\ninf,1\n")

    def test_tsplib_requires_declared_dimension(self) -> None:
        with self.assertRaisesRegex(ValueError, "DIMENSION"):
            parse_tsplib("EDGE_WEIGHT_TYPE: EUC_2D\nNODE_COORD_SECTION\n1 0 0\n")


class SolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cities = (
            City("A", 0, 0),
            City("B", 2, 6),
            City("C", 5, 3),
            City("D", 6, 8),
            City("E", 8, 1),
            City("F", 10, 5),
            City("G", 3, 10),
            City("H", 9, 10),
        )
        self.distances = build_distance_matrix(self.cities)

    def test_nearest_neighbor_visits_every_city_once(self) -> None:
        route = nearest_neighbor_route(self.distances, 0)
        self.assertEqual(sorted(route), list(range(len(self.cities))))

    def test_multistart_is_deterministic_and_clamped_to_city_count(self) -> None:
        self.assertEqual(choose_start_indices(5, 3), [0, 1, 3])
        result = solve_tsp(self.cities, requested_starts=100)
        self.assertEqual(result.starts_used, len(self.cities))

    def test_improvement_never_increases_route_length(self) -> None:
        initial = nearest_neighbor_route(self.distances, 0)
        improved = improve_route(initial, self.distances)
        self.assertLessEqual(
            route_distance(improved, self.distances),
            route_distance(initial, self.distances) + 1e-9,
        )
        self.assertEqual(sorted(improved), list(range(len(self.cities))))

    def test_solver_reports_consistent_metrics(self) -> None:
        result = solve_tsp(self.cities, requested_starts=4)
        self.assertLessEqual(result.final_distance, result.initial_distance + 1e-9)
        self.assertGreaterEqual(result.elapsed_seconds, 0)
        self.assertGreaterEqual(result.improvement_percent, -1e-9)

    def test_two_city_cycle_counts_the_return_edge(self) -> None:
        cities = (City("A", 0, 0), City("B", 3, 4))
        result = solve_tsp(cities, requested_starts=2)
        self.assertEqual(result.initial_distance, 10.0)
        self.assertEqual(result.final_distance, 10.0)

    def test_parse_instance_dispatches_from_file_extension(self) -> None:
        instance = parse_instance(
            "tiny.tsp",
            "DIMENSION: 2\nEDGE_WEIGHT_TYPE: EUC_2D\n"
            "NODE_COORD_SECTION\n1 0 0\n2 1 1\n",
        )
        self.assertEqual(instance.source_format, "TSPLIB EUC_2D")


if __name__ == "__main__":
    unittest.main()
