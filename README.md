# Graph Algorithms: COSC 520 Assignment 3

Compare four manually implemented algorithms: basic vertex cover, randomized vertex cover, greedy graph coloring, and largest degree first coloring. The benchmark measures runtime and solution size on sampled subgraphs.

- Download `frb100-40.mtx` from the [dataset folder](https://drive.google.com/drive/folders/10s-_qutMS6hMNjHOo81g_OwFv4a1wGLp?usp=sharing)

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

A successful run ends with `OK`. The suite contains 38 tests covering algorithms, loading, sampling, benchmark validation, plotting, and command routing.

## 3. Run a small experiment

The source graph is located at `data/raw/frb100-40/frb100-40.mtx`. If missing, download it using the link above and extract it to that location.

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
| Source graph | `frb100-40`, undirected and unweighted |
| Full graph | 4,000 vertices, 7,425,226 edges |
| Graph sizes | 500, 1,000, 1,500, 2,000, 3,000, 4,000 vertices |
| Samples | Five per smaller size; full graph once |
| Trials | 30 per algorithm per graph |
| Base seed | 520 |

Run preparation, benchmarking, and plotting together using the defaults:

```bash
python main.py
```

The equivalent explicit command is:

```bash
python main.py all --dataset data/raw/frb100-40/frb100-40.mtx --sizes 500 1000 1500 2000 3000 4000 --samples 5 --runs 30 --seed 520
```

This produces 26 graphs and 3,120 measurements. Each benchmark creates a new `results/frb100-40/benchmark_<timestamp>/` folder.

To benchmark the included prepared graphs without regenerating them:

```bash
python main.py benchmark
python main.py plot results/frb100-40/benchmark_<timestamp>
```

Replace `<timestamp>` with the actual folder name printed by the benchmark.

To regenerate the prepared graphs and properties tables only:

```bash
python main.py prepare
```

Graph files and the manifest are saved in `data/prepared/<dataset_name>/`. Properties tables go to `results/dataset_properties/<dataset_name>/`. Benchmark runs contain raw measurements, metadata, four comparison plots, and a full-graph results table.

### Reproducibility

Keep the original dataset and its input order unchanged. Sampling uses fixed seeds derived from base seed 520; the manifest records the settings and source checksum. Each sample records its own seed. The benchmark records randomized algorithm seeds, source hashes, graph hashes, and Python/platform information.

Use the same Python version, dataset, settings, and code to regenerate the samples. Benchmarking the included prepared files uses exactly those graphs. Runtime measurements will vary across computers.

Plot lines show medians of per-graph trial medians. Bands show the range between those graph medians, not confidence intervals. Each algorithm receives one untimed warmup per graph, and execution order rotates between trials. Timing includes the complete algorithm call, including adjacency construction and degree sorting for coloring. Loading, sampling, validation, solution counting, and file writing are excluded. Only completed runs should be used for analysis.

## Project layout

| Location | Purpose |
|---|---|
| `main.py` | Only application entry point |
| `requirements.txt` | Pinned plotting dependency |
| `src/` | Algorithms, loading, preparation, benchmarking, and plotting |
| `tests/` | Unit tests and small workflow checks |
| `data/raw/` | Original downloaded dataset |
| `data/prepared/<dataset_name>/` | Prepared subgraphs and manifest, included in Git |
| `results/dataset_properties/<dataset_name>/` | Generated graph properties and summary tables |
| `results/frb100-40/benchmark_<timestamp>/` | Measurements, metadata, plots, and summaries for one run |
| `docs/` | Local assignment and benchmark documentation, excluded from Git |
| `tmp/` | Temporary checks and quick-run data, excluded from Git |

Generated results are excluded from Git, so `results/` may be absent in a fresh clone. Its output folders are created when their commands run. `tmp/` and `docs/` are local-only folders and are not required for the benchmark workflow. Git does not store empty folders.

The `.gitignore` excludes generated results, temporary files, Python caches, local environments, editor settings, local documentation under `docs/`, and local secrets. Raw and prepared datasets remain eligible for tracking. Measurement CSVs, metadata, and plots remain in the ignored `results/` folder.

## Completed benchmark

The completed run is `results/frb100-40/benchmark_20261106_195223_136378/`. It contains 3,120 measurements. For the full graph:

| Algorithm | Median runtime (ms) | Median solution size |
|---|---:|---:|
| Basic vertex cover | 261.09 | 3,998 |
| Randomized vertex cover | 271.88 | 3,972.5 |
| Greedy coloring | 3,611.55 | 100 |
| Largest degree first coloring | 4,310.46 | 155 |

Each median summarizes 30 trials. The randomized cover median can be fractional because the two middle integer sizes are averaged. Solution sizes are cover vertices or colors, respectively, and are not approximation ratios. These timings describe the recorded machine and will differ on another PC. The historical run directory is local and is not included in a fresh clone under the current ignore rules.

## Using a different dataset

Place the new Matrix Market file under `data/raw/`. The loader expects an
undirected, unweighted file with the header `%%MatrixMarket matrix coordinate pattern symmetric`.
For example, for a graph with 1,000 vertices:

```bash
python main.py all --dataset data/raw/new_graph/new_graph.mtx --sizes 50 100 250 500 1000
```

The dataset filename determines the folder name automatically:

- `data/prepared/new_graph/`: subgraphs and manifest.
- `results/dataset_properties/new_graph/`: properties tables.
- `results/new_graph/benchmark_<timestamp>/`: measurements, metadata, and plots.

Choose sizes no larger than the source graph. Include its full vertex count
if you want the full-graph summary table. Defaults remain the six sizes for
`frb100-40`; new datasets should supply appropriate `--sizes`.

To benchmark an already-prepared dataset, without loading the raw file:

```bash
python main.py benchmark --dataset-name new_graph
```

Use `--dataset-name` to give datasets with identical filenames distinct labels.
Use the same label for preparation and benchmarking. Reusing a label during
preparation replaces matching prepared files and properties for that label;
benchmark runs always get a new timestamped directory. Explicit `--preparation`,
`--properties`, and `--output` paths still override the default locations.
Existing benchmark run folders remain readable by the plotting command.
