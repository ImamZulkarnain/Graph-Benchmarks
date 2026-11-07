import unittest
from itertools import combinations

from src.graph_coloring import build_neighbors, greedy_graph_coloring, largest_degree_first_coloring


class GraphColoringTests(unittest.TestCase):
    def test_empty_and_isolated_vertices(self):
        for algorithm in [greedy_graph_coloring, largest_degree_first_coloring]:
            self.assertEqual(algorithm([]), {})
            self.assertEqual(algorithm([], [1, 2, 3]), {1: 0, 2: 0, 3: 0})

    def test_known_color_counts(self):
        cases = [([(1, 2)], [1, 2], 2),
                 ([(1, 2), (2, 3), (3, 1)], [1, 2, 3], 3),
                 ([(1, 2), (2, 3), (3, 4), (4, 1)], [1, 2, 3, 4], 2),
                 (list(combinations(range(5), 2)), list(range(5)), 5)]
        for algorithm in [greedy_graph_coloring, largest_degree_first_coloring]:
            for edges, vertices, expected in cases:
                with self.subTest(algorithm=algorithm.__name__, edges=edges):
                    colors = algorithm(edges, vertices)
                    self.assertEqual(len(set(colors.values())), expected)
                    self.assertTrue(all(colors[u] != colors[v] for u, v in edges))

    def test_greedy_respects_vertex_order(self):
        edges = [(1, 2), (2, 3), (3, 4)]
        self.assertEqual(greedy_graph_coloring(edges, [1, 4, 2, 3]), {1: 0, 4: 0, 2: 1, 3: 2})
        self.assertEqual(len(set(greedy_graph_coloring(edges, [1, 2, 3, 4]).values())), 2)

    def test_largest_degree_first_and_stable_ties(self):
        colors = largest_degree_first_coloring([(1, 2), (1, 3), (1, 4)], [4, 3, 2, 1])
        self.assertEqual(list(colors), [1, 4, 3, 2])
        self.assertEqual(colors, {1: 0, 4: 1, 3: 1, 2: 1})

    def test_neighbors_are_undirected_and_deduplicated(self):
        self.assertEqual(build_neighbors([(1, 2), (2, 1), (1, 2)], [3]),
                         {3: set(), 1: {2}, 2: {1}})

    def test_self_loops_are_rejected(self):
        for algorithm in [greedy_graph_coloring, largest_degree_first_coloring]:
            with self.assertRaises(ValueError):
                algorithm([(1, 1)])

    def test_all_four_vertex_graphs_are_properly_colored_without_mutation(self):
        vertices = list(range(4))
        possible_edges = list(combinations(vertices, 2))
        for mask in range(1 << len(possible_edges)):
            edges = [edge for i, edge in enumerate(possible_edges) if mask & (1 << i)]
            original = edges.copy()
            for algorithm in [greedy_graph_coloring, largest_degree_first_coloring]:
                colors = algorithm(edges, vertices)
                self.assertEqual(set(colors), set(vertices))
                self.assertTrue(all(type(color) is int and color >= 0 for color in colors.values()))
                self.assertTrue(all(colors[u] != colors[v] for u, v in edges))
                self.assertEqual(edges, original)
                self.assertEqual(vertices, list(range(4)))
