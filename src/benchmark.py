"""Run repeated benchmarks on the graphs listed in data/prepared/manifest.json."""

import csv
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from .graph_coloring import greedy_graph_coloring, largest_degree_first_coloring
from .prepare_subgraphs import graph_properties
from .vertex_cover import basic_vertex_cover, randomized_vertex_cover


def check_cover(vertices, edges, cover):
    """Reject unknown vertices or uncovered edges."""
    if not set(cover).issubset(vertices):
        raise ValueError("Cover contains an unknown vertex.")
    if any(u not in cover and v not in cover for u, v in edges):
        raise ValueError("An edge is not covered.")


def check_coloring(vertices, edges, colors):
    """Reject missing vertices, invalid colors, or adjacent matching colors."""
    if set(colors) != set(vertices):
        raise ValueError("Coloring must include every vertex exactly once.")
    if any(type(color) is not int or color < 0 for color in colors.values()):
        raise ValueError("Colors must be nonnegative integers.")
    if any(colors[u] == colors[v] for u, v in edges):
        raise ValueError("Adjacent vertices have the same color.")


def load_sample(path):
    """Load a saved graph and check its vertices and edges before timing."""
    graph = json.loads(path.read_text(encoding="utf-8"))
    vertices = graph["vertices"]
    edges = [tuple(edge) for edge in graph["edges"]]
    vertex_set = set(vertices)
    if len(vertex_set) != len(vertices):
        raise ValueError("Duplicate vertex IDs in sample.")
    seen = set()
    for u, v in edges:
        if u not in vertex_set or v not in vertex_set or u == v:
            raise ValueError("Invalid edge in sample.")
        edge = (min(u, v), max(u, v))
        if edge in seen:
            raise ValueError("Duplicate edge in sample.")
        seen.add(edge)
    return graph, vertices, edges


def run_benchmarks(manifest_path, output, runs=30, base_seed=520):
    """Time all four algorithms, validate every result, and save raw CSV rows."""
    if runs < 1:
        raise ValueError("Runs must be at least 1.")
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not manifest["graphs"] or len(set(manifest["graphs"])) != len(manifest["graphs"]):
        raise ValueError("Manifest must list distinct graph files.")

    # A separate directory prevents overwriting earlier measurements.
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    metadata_path = output / "benchmark_metadata.json"
    root = Path(__file__).parent
    metadata = {
        "status": "running", "started_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "platform": platform.platform(),
        "processor": platform.processor(), "runs_per_graph": runs,
        "base_seed": base_seed, "source_manifest": manifest,
        "timer": "time.perf_counter; seconds",
        "timing": "Complete algorithm call, including coloring adjacency construction and degree sorting. "
                  "Excludes loading, sampling, validation, solution counting, and CSV writing.",
        "execution_order": "Rotate algorithm order each trial; preserve vertex and edge input order.",
        "random_seed_rule": "base_seed + graph_index * runs + trial_index (indices start at zero)",
        "warmups": "One untimed call per algorithm per graph, using the first trial seed.",
        "source_hashes": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                          for name in ["benchmark.py", "vertex_cover.py", "graph_coloring.py", "prepare_subgraphs.py"]},
        "graph_hashes": {},
        "rows_written": 0,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    fields = ["sample_id", "graph_file", "vertices", "edges", "density", "mean_degree",
              "sample_seed", "algorithm", "problem", "run", "execution_position",
              "algorithm_seed", "runtime_seconds", "solution_size"]
    try:
        with open(output / "benchmark_results.csv", "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            for graph_index, relative_path in enumerate(manifest["graphs"]):
                path = manifest_path.parent / relative_path
                graph, vertices, edges = load_sample(path)
                metadata["graph_hashes"][relative_path] = hashlib.sha256(path.read_bytes()).hexdigest()
                properties = graph_properties(vertices, edges)
                algorithms = [
                    ("basic_vertex_cover", "vertex_cover", basic_vertex_cover, (edges,)),
                    ("randomized_vertex_cover", "vertex_cover", randomized_vertex_cover, None),
                    ("greedy_graph_coloring", "graph_coloring", greedy_graph_coloring, (edges, vertices)),
                    ("largest_degree_first_coloring", "graph_coloring", largest_degree_first_coloring, (edges, vertices)),
                ]
                first_seed = base_seed + graph_index * runs
                for name, problem, algorithm, arguments in algorithms:
                    result = algorithm(*(arguments if arguments is not None else (edges, first_seed)))
                    if problem == "vertex_cover":
                        check_cover(vertices, edges, result)
                    else:
                        check_coloring(vertices, edges, result)
                    del result

                for trial in range(runs):
                    offset = trial % len(algorithms)
                    order = algorithms[offset:] + algorithms[:offset]
                    for position, (name, problem, algorithm, arguments) in enumerate(order, 1):
                        seed = first_seed + trial if arguments is None else None
                        arguments = (edges, seed) if arguments is None else arguments
                        start = perf_counter()
                        result = algorithm(*arguments)
                        elapsed = perf_counter() - start

                        # Validation and result counting are outside the timed call.
                        if problem == "vertex_cover":
                            check_cover(vertices, edges, result)
                            size = len(result)
                        else:
                            check_coloring(vertices, edges, result)
                            size = len(set(result.values()))
                        writer.writerow({
                            "sample_id": graph["sample_id"], "graph_file": relative_path,
                            **properties, "sample_seed": graph["seed"], "algorithm": name,
                            "problem": problem, "run": trial + 1, "execution_position": position,
                            "algorithm_seed": seed, "runtime_seconds": elapsed, "solution_size": size,
                        })
                        metadata["rows_written"] += 1
                        del result
                file.flush()
                print(f"[{graph_index + 1}/{len(manifest['graphs'])}] {graph['sample_id']}: {runs} runs per algorithm", flush=True)
        metadata["status"] = "completed"
    except BaseException as error:
        metadata["status"] = "failed"
        metadata["error"] = str(error)
        raise
    finally:
        metadata["finished_utc"] = datetime.now(timezone.utc).isoformat()
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Saved {metadata['rows_written']} measurements to {output.resolve()}")
