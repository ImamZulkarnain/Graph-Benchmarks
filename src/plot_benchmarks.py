"""Create four comparison plots and summary tables from a completed run."""

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


ALGORITHMS = {
    "basic_vertex_cover": "Basic",
    "randomized_vertex_cover": "Randomized",
    "greedy_graph_coloring": "Greedy",
    "largest_degree_first_coloring": "Largest degree first",
}


def load_results(folder):
    """Read a completed run and reject missing, duplicate, or invalid rows."""
    metadata = json.loads((folder / "benchmark_metadata.json").read_text(encoding="utf-8"))
    if metadata["status"] != "completed":
        raise ValueError("Only completed benchmark runs can be plotted.")
    with open(folder / "benchmark_results.csv", newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    expected_graphs = metadata["source_manifest"]["graphs"]
    expected_runs = set(range(1, metadata["runs_per_graph"] + 1))
    groups = defaultdict(set)
    graph_properties = {}
    for row in rows:
        for key in ["vertices", "edges", "run", "solution_size"]:
            row[key] = int(row[key])
        row["runtime_seconds"] = float(row["runtime_seconds"])
        if (not math.isfinite(row["runtime_seconds"]) or row["runtime_seconds"] < 0
                or min(row["vertices"], row["edges"], row["solution_size"]) < 0
                or row["solution_size"] > row["vertices"]):
            raise ValueError("Invalid measurement in CSV.")
        key = (row["graph_file"], row["algorithm"])
        if row["run"] in groups[key]:
            raise ValueError("Duplicate trial in CSV.")
        groups[key].add(row["run"])
        properties = (row["sample_id"], row["vertices"], row["edges"])
        previous = graph_properties.setdefault(row["graph_file"], properties)
        if properties != previous:
            raise ValueError("Graph properties differ between trials.")

    expected_groups = {(graph, algorithm) for graph in expected_graphs for algorithm in ALGORITHMS}
    if (not rows or len(rows) != metadata["rows_written"] or set(groups) != expected_groups
            or any(runs != expected_runs for runs in groups.values())):
        raise ValueError("CSV does not contain all expected benchmark trials.")
    return rows


def summarize_samples(rows):
    """Compute trial medians and ranges separately for each graph and algorithm."""
    groups = defaultdict(list)
    for row in rows:
        groups[(row["graph_file"], row["algorithm"])].append(row)
    summaries = []
    for (graph, algorithm), trials in groups.items():
        runtimes = [row["runtime_seconds"] * 1000 for row in trials]
        sizes = [row["solution_size"] for row in trials]
        summaries.append({
            "graph_file": graph, "sample_id": trials[0]["sample_id"],
            "vertices": trials[0]["vertices"], "edges": trials[0]["edges"],
            "algorithm": algorithm, "runs": len(trials),
            "runtime_ms": median(runtimes), "runtime_min_ms": min(runtimes),
            "runtime_max_ms": max(runtimes), "solution_size": median(sizes),
            "solution_min": min(sizes), "solution_max": max(sizes),
        })
    return summaries


def summarize_sizes(samples):
    """Give each graph equal weight, using its median across repeated runs."""
    groups = defaultdict(list)
    for row in samples:
        groups[(row["vertices"], row["algorithm"])].append(row)
    summaries = []
    for (vertices, algorithm), group in sorted(groups.items()):
        row = {"vertices": vertices, "algorithm": algorithm, "samples": len(group)}
        for metric in ["runtime_ms", "solution_size"]:
            values = [sample[metric] for sample in group]
            row[metric] = median(values)
            row[metric + "_low"] = min(values)
            row[metric + "_high"] = max(values)
        summaries.append(row)
    return summaries


def save_csv(path, rows):
    """Save summary dictionaries to CSV."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def draw_comparison(summary, algorithms, metric, title, ylabel, output):
    """Save one comparison as PNG and SVG, with ranges across sample medians."""
    fig, ax = plt.subplots(figsize=(7, 4.8))
    for algorithm, color, marker in zip(algorithms, ["#0072B2", "#D55E00"], ["o", "s"]):
        points = sorted((row for row in summary if row["algorithm"] == algorithm),
                        key=lambda row: row["vertices"])
        x = [row["vertices"] for row in points]
        y = [row[metric] for row in points]
        low = [row[metric + "_low"] for row in points]
        high = [row[metric + "_high"] for row in points]
        ax.plot(x, y, color=color, marker=marker, label=ALGORITHMS[algorithm], linewidth=2)
        ax.fill_between(x, low, high, color=color, alpha=0.15)
        ax.errorbar(x, y, yerr=[[a-b for a,b in zip(y,low)], [b-a for a,b in zip(y,high)]],
                    fmt="none", ecolor=color, capsize=3, alpha=0.7)
    ax.set(title=title, xlabel="Number of vertices", ylabel=ylabel)
    ax.set_xticks(sorted({row["vertices"] for row in summary}))
    ax.set_ylim(bottom=0)
    if metric == "solution_size":
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.text(0.5, 0.025, "Lines: median of graph medians. Bands: range across graph medians.\n"
             "One graph at a size gives no between-graph variability band.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    fig.savefig(output.with_suffix(".png"), dpi=300)
    fig.savefig(output.with_suffix(".svg"))
    plt.close(fig)


def plot_benchmarks(folder):
    """Create plots and tables without rerunning any algorithms."""
    folder = Path(folder)
    rows = load_results(folder)
    samples = summarize_samples(rows)
    summary = summarize_sizes(samples)
    output = folder / "plots"
    output.mkdir(exist_ok=True)
    save_csv(output / "sample_summary.csv", samples)
    save_csv(output / "plot_summary.csv", summary)
    cover = ["basic_vertex_cover", "randomized_vertex_cover"]
    coloring = ["greedy_graph_coloring", "largest_degree_first_coloring"]
    figures = [
        (cover, "runtime_ms", "Vertex cover: runtime", "Runtime (ms)", "vertex_cover_runtime"),
        (cover, "solution_size", "Vertex cover: solution size", "Vertices selected", "vertex_cover_size"),
        (coloring, "runtime_ms", "Graph coloring: runtime", "Runtime (ms)", "graph_coloring_runtime"),
        (coloring, "solution_size", "Graph coloring: solution size", "Number of colors", "graph_coloring_size"),
    ]
    for algorithms, metric, title, ylabel, name in figures:
        draw_comparison(summary, algorithms, metric, title, ylabel, output / name)

    full_graph = [row for row in samples if Path(row["graph_file"]).stem.endswith("_full")]
    if full_graph:
        save_csv(output / "full_graph_summary.csv", full_graph)
        table = ["# Full-graph results", "",
                 "| Algorithm | Median runtime (ms) | Median solution size | Solution range |",
                 "|---|---:|---:|---:|"]
        for row in full_graph:
            unit = "vertices" if "vertex_cover" in row["algorithm"] else "colors"
            table.append(f"| {ALGORITHMS[row['algorithm']]} ({unit}) | {row['runtime_ms']:.4f} | "
                         f"{row['solution_size']:g} | {row['solution_min']}-{row['solution_max']} |")
        (output / "full_graph_summary.md").write_text("\n".join(table) + "\n", encoding="utf-8")

    (output / "plot_notes.md").write_text(
        "# Reading the plots\n\n"
        "Each graph is summarized by its median across trials. At each vertex count, the line is "
        "the median of those graph medians; the band is their minimum-to-maximum range. "
        "These are descriptive ranges, not confidence intervals.\n\n"
        "Bands show differences between sampled graphs, not timing noise between repeated runs "
        "or random-seed variability within a graph. The full graph has no between-graph range. "
        "Trial ranges are preserved separately in sample_summary.csv and full_graph_summary.csv.\n\n"
        "Runtime is in milliseconds; raw benchmark CSV times are in seconds. Smaller solution "
        "sizes are better, but they are not approximation ratios or proof of optimality. "
        "All samples originate from one dataset and may overlap.\n",
        encoding="utf-8",
    )
    print(f"Saved four plots (PNG and SVG) and summary tables to {output.resolve()}")
