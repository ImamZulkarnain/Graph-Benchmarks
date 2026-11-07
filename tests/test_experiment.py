import csv
import io
import json
from contextlib import redirect_stdout
from unittest.mock import patch

from src.benchmark import check_coloring, check_cover, load_sample, run_benchmarks
from src.prepare_subgraphs import graph_properties, prepare_subgraphs
from src.plot_benchmarks import load_results, plot_benchmarks, summarize_samples, summarize_sizes
from tests.helpers import FileTestCase


class ExperimentTests(FileTestCase):
    def setUp(self):
        super().setUp()
        self.dataset = self.write_graph()
        self.preparation = self.folder / 'preparation'
        self.output = self.folder / 'benchmark'
        self.properties = self.folder / 'properties'

    def prepare(self):
        with redirect_stdout(io.StringIO()):
            return prepare_subgraphs(self.dataset, self.preparation, [2, 4], self.properties, samples=2)

    def benchmark(self):
        self.prepare()
        with redirect_stdout(io.StringIO()):
            run_benchmarks(self.preparation / 'manifest.json', self.output, runs=2)

    def test_graph_properties(self):
        self.assertEqual(graph_properties([], []),
                         {'vertices': 0, 'edges': 0, 'density': 0, 'mean_degree': 0})
        self.assertEqual(graph_properties([1], [])['density'], 0)
        properties = graph_properties([1, 2, 3, 4], [(1, 2), (2, 3)])
        self.assertAlmostEqual(properties['density'], 1 / 3)
        self.assertEqual(properties['mean_degree'], 1)

    def test_preparation_files_properties_and_reproducibility(self):
        properties, summary = self.prepare()
        self.assertFalse((self.preparation / 'subgraph_properties.csv').exists())
        manifest = json.loads((self.preparation / 'manifest.json').read_text())
        self.assertEqual((self.preparation / manifest['dataset']).resolve(), self.dataset.resolve())
        self.assertEqual(len(properties), 3)
        self.assertEqual([row['samples'] for row in summary], [2, 1])
        before = {p.name: p.read_bytes() for p in (self.preparation / 'subgraphs').glob('*.json')}
        self.prepare()
        self.assertEqual(before, {p.name: p.read_bytes() for p in (self.preparation / 'subgraphs').glob('*.json')})
        for row in properties:
            graph, vertices, edges = load_sample(self.preparation / row['graph_file'])
            expected = [(u, v) for u, v in [(1, 2), (2, 3), (3, 1), (3, 4)]
                        if u in vertices and v in vertices]
            self.assertEqual(edges, expected)
            self.assertEqual(row['edges'], len(expected))
            self.assertEqual(row['vertices'], len(vertices))
        with (self.properties / 'subgraph_properties.csv').open(newline='') as file:
            self.assertEqual(len(list(csv.DictReader(file))), 3)

    def test_preparation_rejects_invalid_settings(self):
        for sizes, samples in [([], 1), ([0], 1), ([5], 1), ([2], 0)]:
            with self.subTest(sizes=sizes, samples=samples), self.assertRaises(ValueError):
                prepare_subgraphs(self.dataset, self.preparation, sizes, self.properties, samples)

    def test_saved_sample_validation(self):
        path = self.folder / 'sample.json'
        cases = [([1, 1], []), ([1, 2], [[1, 1]]), ([1, 2], [[1, 3]]),
                 ([1, 2], [[1, 2], [2, 1]])]
        for vertices, edges in cases:
            path.write_text(json.dumps({'vertices': vertices, 'edges': edges}))
            with self.subTest(vertices=vertices, edges=edges), self.assertRaises(ValueError):
                load_sample(path)

    def test_solution_validation(self):
        check_cover([1, 2, 3], [(1, 2)], {1})
        check_coloring([1, 2, 3], [(1, 2)], {1: 0, 2: 1, 3: 0})
        for cover in [set(), {3}, {1, 4}]:
            with self.assertRaises(ValueError):
                check_cover([1, 2, 3], [(1, 2)], cover)
        for colors in [{1: 0}, {1: 0, 2: 0}, {1: -1, 2: 0},
                       {1: True, 2: 0}, {1: 0.5, 2: 0}, {1: 0, 2: 1, 3: 0}]:
            with self.assertRaises(ValueError):
                check_coloring([1, 2], [(1, 2)], colors)

    def test_benchmark_records_trials_seeds_and_metadata(self):
        self.benchmark()
        rows = load_results(self.output)
        self.assertEqual(len(rows), 24)
        self.assertTrue(all(row['runtime_seconds'] >= 0 for row in rows))
        randomized = [row for row in rows if row['algorithm'] == 'randomized_vertex_cover']
        self.assertEqual([int(row['algorithm_seed']) for row in randomized], list(range(520, 526)))
        for row in rows:
            if row['algorithm'] != 'randomized_vertex_cover':
                self.assertEqual(row['algorithm_seed'], '')
        metadata = json.loads((self.output / 'benchmark_metadata.json').read_text())
        self.assertEqual(metadata['status'], 'completed')
        self.assertEqual(metadata['rows_written'], 24)
        self.assertEqual(len(metadata['graph_hashes']), 3)

    def test_benchmark_rejects_overwrite_and_invalid_runs(self):
        self.prepare()
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            run_benchmarks(self.preparation / 'manifest.json', self.output, runs=1)
        with self.assertRaises(ValueError):
            run_benchmarks(self.preparation / 'manifest.json', self.folder / 'other', runs=0)

    def test_bad_algorithm_result_marks_run_failed(self):
        self.prepare()
        with patch('src.benchmark.basic_vertex_cover', return_value={999}), self.assertRaises(ValueError):
            run_benchmarks(self.preparation / 'manifest.json', self.output, runs=1)
        metadata = json.loads((self.output / 'benchmark_metadata.json').read_text())
        self.assertEqual(metadata['status'], 'failed')
        self.assertEqual(metadata['rows_written'], 0)

    def test_plot_loader_rejects_incomplete_duplicate_and_missing_trials(self):
        self.benchmark()
        csv_path = self.output / 'benchmark_results.csv'
        original = csv_path.read_text()
        lines = original.splitlines()
        for changed in ['\n'.join(lines + [lines[1]]) + '\n', '\n'.join(lines[:-1]) + '\n']:
            csv_path.write_text(changed)
            with self.assertRaises(ValueError):
                load_results(self.output)
        csv_path.write_text(original)
        path = self.output / 'benchmark_metadata.json'
        metadata = json.loads(path.read_text())
        metadata['status'] = 'failed'
        path.write_text(json.dumps(metadata))
        with self.assertRaises(ValueError):
            load_results(self.output)

    def test_summaries_weight_graphs_equally_and_convert_seconds(self):
        rows = []
        for graph, times, sizes in [('a', [0.001, 0.003, 0.100], [2, 3, 4]),
                                    ('b', [0.007], [5])]:
            for elapsed, size in zip(times, sizes):
                rows.append(dict(graph_file=graph, sample_id=graph, vertices=6, edges=8,
                                 algorithm='basic_vertex_cover', runtime_seconds=elapsed, solution_size=size))
        samples = summarize_samples(rows)
        summary = summarize_sizes(samples)[0]
        self.assertEqual(samples[0]['runtime_ms'], 3)
        self.assertEqual(summary['runtime_ms'], 5)
        self.assertEqual(summary['runtime_ms_low'], 3)
        self.assertEqual(summary['runtime_ms_high'], 7)
        self.assertEqual(summary['solution_size'], 4)

    def test_plotting_creates_four_figures_and_full_graph_table(self):
        self.benchmark()
        raw = (self.output / 'benchmark_results.csv').read_bytes()
        with redirect_stdout(io.StringIO()):
            plot_benchmarks(self.output)
        plots = self.output / 'plots'
        self.assertEqual(len(list(plots.glob('*.png'))), 4)
        self.assertEqual(len(list(plots.glob('*.svg'))), 4)
        self.assertTrue(all(path.stat().st_size > 0 for path in plots.iterdir()))
        with (plots / 'full_graph_summary.csv').open(newline='') as file:
            self.assertEqual(len(list(csv.DictReader(file))), 4)
        self.assertNotIn('Valid', (plots / 'full_graph_summary.md').read_text())
        self.assertEqual((self.output / 'benchmark_results.csv').read_bytes(), raw)
