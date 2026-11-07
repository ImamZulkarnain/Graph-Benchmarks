from src.data_loader import load_graph, select_subgraph
from tests.helpers import FileTestCase


class DataLoaderTests(FileTestCase):
    def test_comments_duplicates_order_and_isolated_vertices(self):
        path = self.write_graph('% comment\n\n4 4 4\n2 1\n1 2\n  % another comment\n2 3\n2 3\n')
        self.assertEqual(load_graph(path), ([1, 2, 3, 4], [(2, 1), (2, 3)]))

    def test_empty_graph(self):
        self.assertEqual(load_graph(self.write_graph('0 0 0\n')), ([], []))

    def test_unsupported_header(self):
        path = self.folder / 'invalid.mtx'
        path.write_text('%%MatrixMarket matrix coordinate real general\n2 2 1\n1 2 1\n')
        with self.assertRaises(ValueError):
            load_graph(path)

    def test_invalid_dimensions_edges_and_counts(self):
        cases = ['', '3 3\n', '3 4 0\n', '-1 -1 0\n', '3 3 -1\n',
                 '3 3 1\n1 1\n', '3 3 1\n0 2\n', '3 3 1\n1 4\n',
                 '3 3 1\n1 2 3\n', '3 3 1\na b\n', '3 3 1\n',
                 '3 3 0\n1 2\n']
        for body in cases:
            with self.subTest(body=body), self.assertRaises(ValueError):
                load_graph(self.write_graph(body))

    def test_sampling_is_reproducible_induced_and_preserves_order(self):
        vertices = [5, 1, 4, 2, 3, 6]
        edges = [(5, 1), (1, 4), (4, 2), (2, 3), (5, 3)]
        original = (vertices.copy(), edges.copy())
        sampled, kept = select_subgraph(vertices, edges, 4, 520)
        self.assertEqual((sampled, kept), select_subgraph(vertices, edges, 4, 520))
        self.assertEqual(len(sampled), 4)
        self.assertEqual(sampled, [v for v in vertices if v in sampled])
        self.assertEqual(kept, [edge for edge in edges if set(edge).issubset(sampled)])
        self.assertEqual((vertices, edges), original)

    def test_sampling_zero_oversize_and_negative_sizes(self):
        self.assertEqual(select_subgraph([1, 2, 3], [(1, 2)], 0), ([], []))
        self.assertEqual(select_subgraph([1, 2, 3], [(1, 2)], 10), ([1, 2, 3], [(1, 2)]))
        with self.assertRaises(ValueError):
            select_subgraph([1], [], -1)
