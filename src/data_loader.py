"""Load unweighted, undirected graphs from Matrix Market files."""


def load_graph(filename):
    """Return (vertices, edges), keeping vertex IDs from 1 to n."""
    with open(filename, encoding="utf-8") as file:
        header = file.readline().strip().lower()
        if header != "%%matrixmarket matrix coordinate pattern symmetric":
            raise ValueError("Expected a symmetric, unweighted Matrix Market file.")

        # Ignore comments and blank lines after the header.
        rows = (line.split() for line in file if line.strip() and not line.lstrip().startswith("%"))
        dimensions = next(rows, [])
        if len(dimensions) != 3:
            raise ValueError("Missing or invalid graph dimensions.")
        n, columns, edge_count = map(int, dimensions)
        if n < 0 or columns != n or edge_count < 0:
            raise ValueError("Graph dimensions must be square and nonnegative.")

        edges = []
        seen = set()
        entries = 0
        for row in rows:
            if len(row) != 2:
                raise ValueError("Each edge must contain two vertex IDs.")
            u, v = map(int, row)
            if not (1 <= u <= n and 1 <= v <= n):
                raise ValueError("Vertex ID is outside the graph dimensions.")
            if u == v:
                raise ValueError("Self-loops are not supported for graph coloring.")
            entries += 1
            edge = (min(u, v), max(u, v))
            if edge not in seen:
                seen.add(edge)
                edges.append((u, v))

        if entries != edge_count:
            raise ValueError("Edge count does not match the file header.")

    return list(range(1, n + 1)), edges


def select_subgraph(vertices, edges, size=15, seed=520):
    """Sample vertices and keep every edge between them, including isolated vertices."""
    import random

    if size < 0:
        raise ValueError("Subgraph size cannot be negative.")
    selected = set(random.Random(seed).sample(vertices, min(size, len(vertices))))
    sub_vertices = [vertex for vertex in vertices if vertex in selected]
    sub_edges = [(u, v) for u, v in edges if u in selected and v in selected]
    return sub_vertices, sub_edges
