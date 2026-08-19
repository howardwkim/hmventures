#!/usr/bin/env python3
"""
Tests for score_mesh.py. Run: python test_score_mesh.py

Covers the two things that were actually wrong when this scorer was first written:
  1. The 11-axis triangle-triangle SAT degenerates on COPLANAR triangles, reporting
     disjoint coplanar pairs as intersecting.
  2. Symmetry scoring with axis='auto' picked the MINIMUM error across axes, so an
     asymmetric mesh always looked symmetric about some other plane.
Both are easy to reintroduce while refactoring, hence the tests.
"""

import sys

import numpy as np
import trimesh

from score_mesh import _tri_tri_intersect_batch, symmetry_metrics, evaluate


def _check(name, got, want):
    status = "OK  " if got == want else "FAIL"
    print(f"  [{status}] {name}: got {got}, want {want}")
    return got == want


def test_sat() -> bool:
    print("triangle-triangle SAT")
    base = np.array([[[0, 0, 0], [2, 0, 0], [0, 2, 0]]], float)
    cases = {
        "piercing":             ([[0.5, 0.5, -1], [0.5, 0.5, 1], [0.9, 0.5, 1]], True),
        "far apart":            ([[0, 0, 5], [1, 0, 5], [0, 1, 5]], False),
        "coplanar disjoint":    ([[5, 5, 0], [6, 5, 0], [5, 6, 0]], False),
        "coplanar overlapping": ([[0.2, 0.2, 0], [1.2, 0.2, 0], [0.2, 1.2, 0]], True),
        "edge touching":        ([[0, 0, 0], [-1, 0, 0], [0, -1, 0]], True),
    }
    t1 = np.repeat(base, len(cases), axis=0)
    t2 = np.array([np.array(v[0], float) for v in cases.values()])
    got = _tri_tri_intersect_batch(t1, t2, 1e-12)
    return all(_check(n, bool(g), w) for (n, (_, w)), g in zip(cases.items(), got))


def test_symmetry() -> bool:
    print("symmetry detection")
    ring = trimesh.creation.torus(major_radius=1.0, minor_radius=0.25,
                                  major_sections=96, minor_sections=32)
    skew = ring.copy()
    v = skew.vertices.copy()
    v[v[:, 0] > 0, 1] *= 1.35          # break mirror symmetry about x only
    skew.vertices = v

    clean_x = symmetry_metrics(ring, axis="x")["symmetry_error"]
    skew_x = symmetry_metrics(skew, axis="x")["symmetry_error"]
    auto = symmetry_metrics(skew, axis="auto")

    ok = True
    ok &= _check("symmetric ring is near zero about x", clean_x < 0.005, True)
    ok &= _check("skewed ring is detected about x", skew_x > 0.008, True)
    ok &= _check("skew scores well above clean", skew_x > clean_x * 5, True)
    # The regression that mattered: auto must not silently score the easiest axis.
    ok &= _check("auto mode is unscored", auto["scored"], False)
    ok &= _check("auto still reports x as worst axis",
                 max(auto["symmetry_excess_all"], key=auto["symmetry_excess_all"].get), "x")
    return ok


def test_ranking(tmpdir="/tmp") -> bool:
    print("candidate ranking")
    import os
    ring = trimesh.creation.torus(major_radius=1.0, minor_radius=0.25,
                                  major_sections=96, minor_sections=32)
    shard = trimesh.creation.icosphere(radius=0.06)
    shard.apply_translation([2.5, 0, 0])
    frag = trimesh.util.concatenate([ring, shard])

    paths = {}
    for name, m in {"clean": ring, "frag": frag}.items():
        p = os.path.join(tmpdir, f"_score_test_{name}.ply")
        m.export(p)
        paths[name] = p

    clean = evaluate(paths["clean"], symmetry_axis="x")
    frag_r = evaluate(paths["frag"], symmetry_axis="x")
    ok = True
    ok &= _check("clean outranks fragmented", clean["score"] > frag_r["score"], True)
    ok &= _check("fragmentation is counted",
                 frag_r["topology"]["connected_components"], 2)
    for p in paths.values():
        os.unlink(p)
    return ok


def main() -> int:
    results = [test_sat(), test_symmetry(), test_ranking()]
    print()
    if all(results):
        print("all tests passed")
        return 0
    print("FAILURES")
    return 1


if __name__ == "__main__":
    sys.exit(main())
