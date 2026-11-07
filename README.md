# Graph Algorithms: COSC 520 Assignment 3

Compare four manually implemented algorithms: basic vertex cover, randomized vertex cover, greedy graph coloring, and largest degree first coloring. The benchmark measures runtime and solution size on sampled subgraphs.

- Download the dataset from [here](https://drive.google.com/drive/folders/10s-_qutMS6hMNjHOo81g_OwFv4a1wGLp?usp=sharing)

## 1. Get the project and install dependencies

Clone the GitHub repository or download and extract its ZIP. Open a terminal in the folder containing `main.py`.

### Conda setup (Windows, macOS, and Linux)

On Windows, open Anaconda Prompt. On macOS or Linux, open a terminal where Conda is available. Run these commands one at a time:

```bash
conda create -n graph-benchmarks python=3.12.12 pip
conda activate graph-benchmarks
python -m pip install -r requirements.txt
```

Tested with Python 3.12.12 and Matplotlib 3.9.2. Matplotlib is used for plotting; the graph algorithms use Python's standard library.

Keep the terminal in the project root for the commands below.

## 2. Run the unit tests

Tests use small temporary graphs and do not need a dataset download:

```bash
python -m unittest discover -s tests -v
```

A successful run ends with `OK`. The suite contains 34 tests covering algorithms, loading, sampling, benchmark validation, plotting, and command routing.

## 3. Run a small experiment

The original graph is located at `data/raw/frb30-15-5/frb30-15-5.mtx`. If missing, download it using the link above and extract it to that location.

Use two small graph sizes, two samples per size, and two trials:

```bash
python main.py all --sizes 10 20 --samples 2 --runs 2 --preparation tmp/quick_data --properties results/quick_properties --output results/quick_run
```

Expected outputs:

- `tmp/quick_data/`: four sampled graphs and their manifest, separate from the main prepared dataset.
- `results/quick_properties/`: graph properties and summary tables.
- `results/quick_run/benchmark_results.csv`: 32 measurement rows plus the header.
- `results/quick_run/plots/`: four comparison figures in PNG and SVG, plus summary tables. This quick run does not include the full graph, so it has no full-graph results table.

**Rerunning:** choose a new `--output` directory, such as `results/quick_run_2`. Preparation replaces files with matching names at its output locations; benchmarks never overwrite an existing output directory.

## 4. Run the full benchmark workload

| Setting | Value |
|---|---|
| Source graph | `frb30-15-5`, undirected and unweighted |
| Full graph | 450 vertices, 83,231 edges |
| Graph sizes | 50, 100, 150, 250, 350, 450 vertices |
| Samples | Five per smaller size; full graph once |
| Trials | 30 per algorithm per graph |
| Base seed | 520 |

Run preparation, benchmarking, and plotting together:

```bash
python main.py
```

This produces 26 graphs and 3,120 measurements. Each benchmark creates a new `results/benchmark_<timestamp>/` folder.

To benchmark the included prepared graphs without regenerating them:

```bash
python main.py benchmark
python main.py plot results/benchmark_<timestamp>
```

Replace `<timestamp>` with the actual folder name printed by the benchmark.

To regenerate the prepared graphs and properties tables only:

```bash
python main.py prepare
```

Graph files and the manifest are saved in `data/prepared/`. Properties tables go to `results/dataset_properties/`. Benchmark runs contain raw measurements, metadata, four comparison plots, and a full-graph results table.

### Reproducibility

Keep the original dataset and its input order unchanged. Sampling uses fixed seeds derived from base seed 520; the manifest records the settings and source checksum. Each sample records its own seed. The benchmark records randomized algorithm seeds, source hashes, graph hashes, and Python/platform information.

Use the same Python version, dataset, settings, and code to regenerate the samples. Benchmarking the included prepared files uses exactly those graphs. Runtime measurements will vary across computers.

Plot lines show medians of per-graph trial medians. Bands show the range between those graph medians, not confidence intervals. See [benchmark details](docs/BENCHMARKS.md) for more information.

## Project layout

| Location | Purpose |
|---|---|
| `main.py` | Only application entry point |
| `requirements.txt` | Pinned plotting dependency |
| `src/` | Algorithms, loading, preparation, benchmarking, and plotting |
| `tests/` | Unit tests and small workflow checks |
| `data/raw/` | Original downloaded dataset |
| `data/prepared/` | Prepared subgraphs and manifest, included in Git |
| `results/dataset_properties/` | Generated graph properties and summary tables |
| `results/benchmark_<timestamp>/` | Measurements, metadata, plots, and summaries for one run |
| `docs/` | Assignment and benchmark documentation |
| `docs/archive/` | Old delivery ZIPs, excluded from Git |
| `tmp/` | Temporary checks and quick-run data, excluded from Git |

In a fresh clone, `results/` contains only an explanation file because generated results are ignored. Its output subfolders are created when their commands run. `tmp/` and `docs/archive/` are absent unless created locally; they are not required for the full workflow. Git does not store empty folders.

The `.gitignore` excludes generated results, temporary files, Python caches, local environments, editor settings, and local secrets. Raw and prepared datasets remain eligible for tracking. Selected results used in the report can be copied to a separate `report_results/` folder for inclusion in Git.
