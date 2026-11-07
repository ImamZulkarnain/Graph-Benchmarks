"""Greedy coloring for undirected edges (u, v). Colors start at 0."""


def build_neighbors(edges, vertices=None):
    """Build neighbor sets. Optionally supply vertices to include isolated ones."""
    neighbors = {}
    if vertices is not None:
        for vertex in vertices:
            neighbors[vertex] = set()

    for u, v in edges:
        if u == v:
            raise ValueError("A graph with a self-loop cannot be colored.")
        neighbors.setdefault(u, set()).add(v)
        neighbors.setdefault(v, set()).add(u)
    return neighbors


def color_in_order(neighbors, order):
    """Return a vertex-to-color dictionary using the given vertex order."""
    colors = {}
    for vertex in order:
        used_colors = set()
        for neighbor in neighbors[vertex]:
            if neighbor in colors:
                used_colors.add(colors[neighbor])

        # Choose the smallest color not used by a colored neighbor.
        color = 0
        while color in used_colors:
            color += 1
        colors[vertex] = color
    return colors


def greedy_graph_coloring(edges, vertices=None):
    """Return vertex colors in input order, or first-seen order in edges.

    Supply vertices to set the order and include isolated vertices.
    """
    neighbors = build_neighbors(edges, vertices)
    return color_in_order(neighbors, neighbors)


def largest_degree_first_coloring(edges, vertices=None):
    """Return vertex colors by coloring higher-degree vertices first.

    Equal degrees keep input order. Optional vertices include isolated ones.
    """
    neighbors = build_neighbors(edges, vertices)
    order = sorted(neighbors, key=lambda vertex: len(neighbors[vertex]), reverse=True)
    return color_in_order(neighbors, order)
