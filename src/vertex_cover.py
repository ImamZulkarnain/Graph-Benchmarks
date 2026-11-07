"""Basic and randomized vertex cover for undirected edges (u, v)."""

import random


def basic_vertex_cover(edges):
    """Take edges and return a set covering them, choosing both endpoints."""
    cover = set()
    for u, v in edges:
        # Skip edges that already have an endpoint in the cover.
        if u not in cover and v not in cover:
            cover.add(u)
            cover.add(v)
    return cover


def randomized_vertex_cover(edges, seed=None):
    """Return a cover by choosing one endpoint randomly per uncovered edge.

    Use the same seed and edge order to repeat a result.
    """
    rng = random.Random(seed)
    cover = set()
    for u, v in edges:
        if u not in cover and v not in cover:
            cover.add(rng.choice((u, v)))
    return cover
