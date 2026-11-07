import io
import json
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

import main
from tests.helpers import FileTestCase


class MainTests(FileTestCase):
    def test_datasets_have_separate_outputs_and_repeated_runs(self):
        for name in ['first', 'second', 'first']:
            dataset = self.folder / (name + '.mtx')
            dataset.write_text('%%MatrixMarket matrix coordinate pattern symmetric\n3 3 2\n1 2\n2 3\n')
            arguments = ['main.py', 'all', '--dataset', str(dataset), '--sizes', '2', '3',
                         '--samples', '1', '--runs', '1']
            with patch('main.__file__', str(self.folder / 'main.py')), \
                 patch('sys.argv', arguments), patch('src.plot_benchmarks.plot_benchmarks'), \
                 redirect_stdout(io.StringIO()):
                main.main()
        for name, count in [('first', 2), ('second', 1)]:
            manifest = self.folder / 'data/prepared' / name / 'manifest.json'
            self.assertEqual(json.loads(manifest.read_text())['dataset_name'], name)
            self.assertTrue((self.folder / 'results/dataset_properties' / name / 'subgraph_summary.csv').exists())
            runs = list((self.folder / 'results' / name).glob('benchmark_*'))
            self.assertEqual(len(runs), count)
            self.assertTrue(all((run / 'benchmark_results.csv').exists() for run in runs))

    def test_benchmark_label_selects_matching_prepared_graphs(self):
        with patch('sys.argv', ['main.py', 'benchmark', '--dataset-name', 'another_graph']), \
             patch('main.run_benchmarks') as benchmark:
            main.main()
        manifest, output, runs, seed = benchmark.call_args.args
        self.assertEqual(manifest.parent.name, 'another_graph')
        self.assertEqual(output.parent.name, 'another_graph')

    def test_custom_preparation_uses_manifest_label(self):
        (self.folder / 'manifest.json').write_text(json.dumps({'dataset_name': 'original', 'dataset': 'source.mtx'}))
        with patch('sys.argv', ['main.py', 'benchmark', '--preparation', str(self.folder)]), \
             patch('main.run_benchmarks') as benchmark:
            main.main()
        self.assertEqual(benchmark.call_args.args[1].parent.name, 'original')

    def test_dataset_label_cannot_escape_output_directory(self):
        with patch('sys.argv', ['main.py', 'prepare', '--dataset-name', '../outside']), \
             redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main.main()

    def test_default_command_runs_all_stages_in_order(self):
        calls = []
        with patch('sys.argv', ['main.py']), \
             patch('main.prepare_subgraphs', side_effect=lambda *args: calls.append(('prepare', args))), \
             patch('main.run_benchmarks', side_effect=lambda *args: calls.append(('benchmark', args))), \
             patch('src.plot_benchmarks.plot_benchmarks', side_effect=lambda *args: calls.append(('plot', args))):
            main.main()
        self.assertEqual([name for name, args in calls], ['prepare', 'benchmark', 'plot'])
        self.assertEqual(calls[1][1][1], calls[2][1][0])
        self.assertEqual(calls[1][1][2], 30)

    def test_individual_commands_call_only_the_requested_stage(self):
        for command in ['prepare', 'benchmark', 'plot']:
            arguments = ['main.py', command]
            if command == 'plot':
                arguments.append(str(self.folder))
            with self.subTest(command=command), patch('sys.argv', arguments), \
                 patch('main.prepare_subgraphs') as prepare, \
                 patch('main.run_benchmarks') as benchmark, \
                 patch('src.plot_benchmarks.plot_benchmarks') as plot:
                main.main()
                self.assertEqual(prepare.call_count, int(command == 'prepare'))
                self.assertEqual(benchmark.call_count, int(command == 'benchmark'))
                self.assertEqual(plot.call_count, int(command == 'plot'))

    def test_existing_output_is_rejected_before_preparation(self):
        with patch('sys.argv', ['main.py', 'all', '--output', str(self.folder)]), \
             patch('main.prepare_subgraphs') as prepare, redirect_stderr(io.StringIO()), \
             self.assertRaises(SystemExit) as error:
            main.main()
        self.assertEqual(error.exception.code, 2)
        prepare.assert_not_called()

    def test_invalid_run_count_is_rejected(self):
        with patch('sys.argv', ['main.py', 'benchmark', '--runs', '0']), \
             redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main.main()
        self.assertEqual(error.exception.code, 2)
