import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from unittest.mock import patch

import main
from tests.helpers import FileTestCase


class MainTests(FileTestCase):
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
