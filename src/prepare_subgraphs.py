"""Prepare reproducible benchmark graphs and their property tables."""

import csv
import hashlib
import json
import os
from pathlib import Path
from statistics import mean

from .data_loader import load_graph, select_subgraph


def graph_properties(vertices, edges):
    """Return vertex count, edge count, density, and mean degree."""
    n = len(vertices)
    m = len(edges)
    return {
        "vertices": n,
        "edges": m,
        "density": 2 * m / (n * (n - 1)) if n > 1 else 0,
        "mean_degree": 2 * m / n if n else 0,
    }


def save_csv(path, rows):
    """Write dictionaries as CSV rows with a header."""
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare_subgraphs(dataset, output, sizes, properties_output, samples=5, base_seed=520):
    """Save induced subgraphs, per-sample properties, and a size summary."""
    vertices, edges = load_graph(dataset)
    sizes = sorted(set(sizes))
    if not sizes or any(size < 1 or size > len(vertices) for size in sizes):
        raise ValueError("Sizes must be between 1 and the dataset vertex count.")
    if samples < 1:
        raise ValueError("At least one sample is required.")

    output = Path(output)
    properties_output = Path(properties_output)
    properties_output.mkdir(parents=True, exist_ok=True)
    graph_folder = output / "subgraphs"
    graph_folder.mkdir(parents=True, exist_ok=True)
    properties = []

    for size in sizes:
        full_graph = size == len(vertices)
        count = 1 if full_graph else samples
        for sample in range(1, count + 1):
            seed = None if full_graph else base_seed + size * samples + sample - 1
            if full_graph:
                sub_vertices, sub_edges = vertices, edges
            else:
                sub_vertices, sub_edges = select_subgraph(vertices, edges, size, seed)

            sample_id = f"n{size}_full" if full_graph else f"n{size}_sample{sample}"
            relative_path = f"subgraphs/{sample_id}.json"
            graph = {
                "sample_id": sample_id,
                "seed": seed,
                "vertices": sub_vertices,
                "edges": sub_edges,
            }
            # Original IDs and edge order are retained for all algorithms.
            with open(output / relative_path, "w", encoding="utf-8") as file:
                json.dump(graph, file)

            row = {"sample_id": sample_id, "seed": seed, "full_graph": full_graph,
                   "graph_file": relative_path}
            row.update(graph_properties(sub_vertices, sub_edges))
            properties.append(row)

    summary = []
    for size in sizes:
        rows = [row for row in properties if row["vertices"] == size]
        summary.append({
            "vertices": size,
            "samples": len(rows),
            "mean_edges": mean(row["edges"] for row in rows),
            "min_edges": min(row["edges"] for row in rows),
            "max_edges": max(row["edges"] for row in rows),
            "mean_density": mean(row["density"] for row in rows),
            "mean_degree": mean(row["mean_degree"] for row in rows),
        })

    save_csv(properties_output / "subgraph_properties.csv", properties)
    save_csv(properties_output / "subgraph_summary.csv", summary)
    metadata = {
        "dataset": Path(os.path.relpath(Path(dataset).resolve(), output.resolve())).as_posix(),
        "dataset_path_base": "manifest directory",
        "dataset_sha256": hashlib.sha256(Path(dataset).read_bytes()).hexdigest(),
        "sizes": sizes,
        "samples_per_smaller_size": samples,
        "base_seed": base_seed,
        "sampling": "Uniform vertex sampling without replacement within each sample; all induced edges retained.",
        "ordering": "Original vertex IDs, vertex order, and edge order retained.",
        "graphs": [row["graph_file"] for row in properties],
    }
    with open(output / "manifest.json", "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    table = [
        "# Subgraph properties", "",
        "| Vertices | Samples | Mean edges | Edge range | Mean density | Mean degree |",
        "|---:|---:|---:|:---|---:|---:|",
    ]
    for row in summary:
        table.append(
            f"| {row['vertices']} | {row['samples']} | {row['mean_edges']:.1f} | "
            f"{row['min_edges']}-{row['max_edges']} | {row['mean_density']:.2%} | "
            f"{row['mean_degree']:.2f} |"
        )
    table.extend(["", "Density = 2E / (V(V-1)); mean degree = 2E / V.", "",
                  "Each smaller graph is an induced random sample of the same source graph. "
                  "Samples may overlap. The full graph appears once. CSV density values are fractions.", "",
                  "Use the manifest.json in the prepared dataset folder to identify the current graphs. Loading a saved JSON graph "
                  "provides vertices and edges ready for the existing algorithms."])
    (properties_output / "subgraph_summary.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    print("\n".join(table[:4 + len(summary)]))
    print(f"\nSaved {len(properties)} graphs to {output.resolve()} and property tables to {properties_output.resolve()}")
    return properties, summary
