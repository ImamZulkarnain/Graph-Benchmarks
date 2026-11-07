import random
import unittest
from itertools import combinations

from src.vertex_cover import basic_vertex_cover, randomized_vertex_cover


class VertexCoverTests(unittest.TestCase):
    def test_empty_graph(self):
        self.assertEqual(basic_vertex_cover([]), set())
        self.assertEqual(randomized_vertex_cover([], seed=520), set())

    def test_basic_selects_both_endpoints_and_skips_covered_edges(self):
        self.assertEqual(basic_vertex_cover([(1, 2), (2, 3), (3, 4)]), {1, 2, 3, 4})
        self.assertEqual(basic_vertex_cover([(1, 2), (1, 3), (1, 4)]), {1, 2})

    def test_randomized_selects_one_endpoint_per_disjoint_edge(self):
        edges = [(1, 2), (3, 4), (5, 6)]
        for seed in range(20):
            cover = randomized_vertex_cover(edges, seed)
            self.assertEqual(len(cover), 3)
            self.assertTrue(all(len(cover & set(edge)) == 1 for edge in edges))

    def test_seed_reproduces_result_without_changing_global_randomness(self):
        edges = [(1, 2), (2, 3), (3, 4), (4, 5)]
        state = random.getstate()
        self.assertEqual(randomized_vertex_cover(edges, 520), randomized_vertex_cover(edges, 520))
        self.assertEqual(random.getstate(), state)

    def test_inputs_are_preserved_and_duplicate_edges_are_allowed(self):
        edges = [(1, 2), (2, 1), (1, 2), (2, 3)]
        original = edges.copy()
        for algorithm in [basic_vertex_cover, randomized_vertex_cover]:
            cover = algorithm(edges)
            self.assertTrue(all(u in cover or v in cover for u, v in edges))
            self.assertEqual(edges, original)

    def test_all_four_vertex_graphs_against_brute_force_optimum(self):
        vertices = list(range(4))
        possible_edges = list(combinations(vertices, 2))
        for mask in range(1 << len(possible_edges)):
            edges = [edge for i, edge in enumerate(possible_edges) if mask & (1 << i)]
            optimum = next(size for size in range(5)
                           if any(all(u in subset or v in subset for u, v in edges)
                                  for subset in combinations(vertices, size)))
            with self.subTest(edges=edges):
                basic = basic_vertex_cover(edges)
                self.assertLessEqual(len(basic), 2 * optimum)
                for cover in [basic] + [randomized_vertex_cover(edges, seed) for seed in range(5)]:
                    self.assertTrue(cover.issubset(vertices))
                    self.assertTrue(all(u in cover or v in cover for u, v in edges))
                    self.assertGreaterEqual(len(cover), optimum)
