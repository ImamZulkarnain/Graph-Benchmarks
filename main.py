"""Prepare graphs, run benchmarks, and plot results from one entry point."""

import argparse
import json
import re
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
        options.add_argument("--dataset", type=Path, default=root / "data/raw/frb30-15-5/frb30-15-5.mtx")
        options.add_argument("--dataset-name", help="Folder label; defaults to the dataset filename without its extension.")
        options.add_argument("--preparation", type=Path, help="Override the prepared dataset directory.")
        if command in ["all", "prepare"]:
            options.add_argument("--properties", type=Path, help="Override the dataset properties directory.")
            options.add_argument("--sizes", type=int, nargs="+", default=[50, 100, 150, 250, 350, 450])
            options.add_argument("--samples", type=int, default=5)
        if command in ["all", "benchmark"]:
            options.add_argument("--runs", type=int, default=30)
            options.add_argument("--output", type=Path, help="New benchmark directory.")
    plotting = commands.add_parser("plot")
    plotting.add_argument("folder", type=Path, help="Completed benchmark directory.")
    args = parser.parse_args(sys.argv[1:] or ["all"])

    if args.command != "plot":
        name = args.dataset_name or args.dataset.stem
        # A custom preparation folder can identify its source without the raw file.
        if args.command == "benchmark" and args.preparation and not args.dataset_name:
            manifest = json.loads((args.preparation / "manifest.json").read_text(encoding="utf-8"))
            name = manifest.get("dataset_name") or Path(manifest["dataset"]).stem
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name):
            parser.error("Use --dataset-name with letters, numbers, underscores, dots, or hyphens; start with a letter or number.")
        args.preparation = args.preparation or root / "data/prepared" / name
        if args.command in ["all", "prepare"]:
            args.properties = args.properties or root / "results/dataset_properties" / name

    # Import plotting only when needed, before starting any long computation.
    if args.command in ["all", "plot"]:
        from src.plot_benchmarks import plot_benchmarks

    if args.command in ["all", "benchmark"]:
        if args.runs < 1:
            parser.error("--runs must be at least 1.")
        output = args.output or root / "results" / name / ("benchmark_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
        if output.exists():
            parser.error("Benchmark output directory already exists. Choose a new --output.")

    if args.command in ["all", "prepare"]:
        prepare_subgraphs(args.dataset, args.preparation, args.sizes, args.properties, args.samples, args.seed, name)
    if args.command in ["all", "benchmark"]:
        run_benchmarks(args.preparation / "manifest.json", output, args.runs, args.seed)
    if args.command == "all":
        plot_benchmarks(output)
    elif args.command == "plot":
        plot_benchmarks(args.folder)


if __name__ == "__main__":
    main()
