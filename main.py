"""Prepare graphs, run benchmarks, and plot results from one entry point."""

import argparse
import sys
from datetime import datetime
from pathlib import Path

from src.benchmark import run_benchmarks
from src.prepare_subgraphs import prepare_subgraphs


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ["all", "prepare", "benchmark"]:
        options = commands.add_parser(command)
        options.add_argument("--seed", type=int, default=520)
        options.add_argument("--preparation", type=Path, default=root / "data/prepared")
        if command in ["all", "prepare"]:
            options.add_argument("--properties", type=Path, default=root / "results/dataset_properties")
            options.add_argument("--dataset", type=Path, default=root / "data/raw/frb30-15-5/frb30-15-5.mtx")
            options.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 150, 250, 350, 450])
            options.add_argument("--samples", type=int, default=5)
        if command in ["all", "benchmark"]:
            options.add_argument("--runs", type=int, default=30)
            options.add_argument("--output", type=Path, help="New benchmark directory.")
    plotting = commands.add_parser("plot")
    plotting.add_argument("folder", type=Path, help="Completed benchmark directory.")
    args = parser.parse_args(sys.argv[1:] or ["all"])

    # Import plotting only when needed, before starting any long computation.
    if args.command in ["all", "plot"]:
        from src.plot_benchmarks import plot_benchmarks

    if args.command in ["all", "benchmark"]:
        if args.runs < 1:
            parser.error("--runs must be at least 1.")
        output = args.output or root / "results" / ("benchmark_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        if output.exists():
            parser.error("Benchmark output directory already exists. Choose a new --output.")

    if args.command in ["all", "prepare"]:
        prepare_subgraphs(args.dataset, args.preparation, args.sizes, args.properties, args.samples, args.seed)
    if args.command in ["all", "benchmark"]:
        run_benchmarks(args.preparation / "manifest.json", output, args.runs, args.seed)
    if args.command == "all":
        plot_benchmarks(output)
    elif args.command == "plot":
        plot_benchmarks(args.folder)


if __name__ == "__main__":
    main()
