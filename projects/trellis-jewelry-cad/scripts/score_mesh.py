#!/usr/bin/env python3
"""
Geometry QC and scoring for generated jewelry meshes.

Reference-free: scores a mesh on its own merits, so it works on generator output where
no ground-truth CAD exists. Used to rank candidates (seed sweeps, or TRELLIS vs Hunyuan)
before anything reaches Rhino.

Scores are ADVISORY RANKING SIGNALS, not pass/fail gates. A genuine openwork pendant is
correctly non-watertight; a naive "watertight = good" rule would reject exactly the pieces
this project cares most about. Interpret per-metric, in context.

Usage:
    python score_mesh.py mesh.ply [mesh2.ply ...] [--json out.json] [--symmetry-axis x]

Dependencies: numpy, scipy, trimesh
"""

import argparse
import json
import sys

import numpy as np
import trimesh
from scipy.spatial import cKDTree


# ---------------------------------------------------------------- topology

def topology_metrics(mesh: trimesh.Trimesh) -> dict:
    """Connectivity facts that decide whether QuadRemesh/NURBS conversion will cope."""
    edges = mesh.edges_sorted
    _, counts = np.unique(edges, axis=0, return_counts=True)

    # scipy engine avoids a networkx dependency.
    comp_faces = trimesh.graph.connected_components(
        mesh.face_adjacency, nodes=np.arange(len(mesh.faces)), engine="scipy"
    )
    comp_volumes = sorted(
        (float(abs(mesh.submesh([c], append=True).volume)) for c in comp_faces),
        reverse=True,
    ) if len(comp_faces) > 1 else [float(abs(mesh.volume))]

    return {
        "watertight": bool(mesh.is_watertight),
        "winding_consistent": bool(mesh.is_winding_consistent),
        # Edges used by exactly one face — genuine openwork boundaries AND generation
        # tears both land here, which is why this is a signal and not a gate.
        "boundary_edges": int((counts == 1).sum()),
        "nonmanifold_edges": int((counts > 2).sum()),
        "connected_components": int(len(comp_faces)),
        "largest_component_volume_fraction": (
            float(comp_volumes[0] / sum(comp_volumes)) if sum(comp_volumes) > 0 else 0.0
        ),
        "euler_number": int(mesh.euler_number),
    }


def degeneracy_metrics(mesh: trimesh.Trimesh) -> dict:
    """Zero-area and near-zero-area triangles break downstream remeshing."""
    areas = mesh.area_faces
    scale = mesh.scale if mesh.scale > 0 else 1.0
    tiny = (scale ** 2) * 1e-10
    return {
        "faces": int(len(mesh.faces)),
        "vertices": int(len(mesh.vertices)),
        "degenerate_faces": int((areas <= tiny).sum()),
        "duplicate_faces": int(
            len(mesh.faces) - len(np.unique(np.sort(mesh.faces, axis=1), axis=0))
        ),
        "unreferenced_vertices": int(len(mesh.vertices) - len(np.unique(mesh.faces))),
    }


# ---------------------------------------------- self-intersection (sampled)

def _tri_tri_intersect_batch(t1: np.ndarray, t2: np.ndarray, eps: float) -> np.ndarray:
    """
    Vectorised separating-axis test for P triangle pairs.

    t1, t2: (P, 3, 3) vertex arrays. Returns (P,) bool -- True where no separating axis
    exists, i.e. the triangles intersect.

    Vectorised because a Python-loop version is unusable at the mesh sizes TRELLIS.2
    actually emits (400K+ faces).
    """
    if len(t1) == 0:
        return np.zeros(0, dtype=bool)

    e1 = np.stack([t1[:, (i + 1) % 3] - t1[:, i] for i in range(3)], axis=1)  # (P,3,3)
    e2 = np.stack([t2[:, (i + 1) % 3] - t2[:, i] for i in range(3)], axis=1)

    axes = [
        np.cross(t1[:, 1] - t1[:, 0], t1[:, 2] - t1[:, 0]),   # face normal 1
        np.cross(t2[:, 1] - t2[:, 0], t2[:, 2] - t2[:, 0]),   # face normal 2
    ]
    for i in range(3):
        for j in range(3):
            axes.append(np.cross(e1[:, i], e2[:, j]))
    # The classic 11-axis set degenerates for COPLANAR triangles: every edge-edge cross
    # product is parallel to the shared normal, so two disjoint triangles in the same
    # plane report as intersecting. In-plane edge normals resolve that case, and are
    # harmless otherwise.
    for i in range(3):
        axes.append(np.cross(e1[:, i], axes[0]))
        axes.append(np.cross(e2[:, i], axes[1]))
    A = np.stack(axes, axis=1)  # (P, 17, 3)

    lengths = np.linalg.norm(A, axis=2)              # (P,17)
    valid = lengths > eps
    safe = np.where(valid[..., None], A / np.where(lengths[..., None] == 0, 1, lengths[..., None]), 0.0)

    proj1 = np.einsum('pad,pvd->pav', safe, t1)      # (P,17,3)
    proj2 = np.einsum('pad,pvd->pav', safe, t2)

    separated = (
        (proj1.min(axis=2) > proj2.max(axis=2) + eps) |
        (proj2.min(axis=2) > proj1.max(axis=2) + eps)
    ) & valid                                        # (P,17)

    return ~separated.any(axis=1)


def self_intersection_metrics(mesh: trimesh.Trimesh, max_pairs: int = 400_000,
                              seed: int = 0) -> dict:
    """
    Sampled self-intersection count. Surfaces that fused where they should be separate --
    prongs merging into a stone, adjacent gallery walls touching -- show up here. This is
    one of the failure modes that looks fine in a render and is fatal in manufacture.

    Candidate pairs come from a KD-tree radius query on face centroids, excluding faces
    that share a vertex (adjacent faces always "touch"). Capped for runtime, so the result
    is a sampled lower bound on the true intersecting-pair count, not an exhaustive audit.
    """
    tris = mesh.triangles
    if len(tris) < 2:
        return {"self_intersecting_pairs": 0, "pairs_tested": 0, "sampled": False}

    centroids = tris.mean(axis=1)
    # Radius ~ typical triangle size: catches near neighbours without exploding pair count.
    radius = float(np.sqrt(mesh.area / len(tris))) * 2.0
    if radius <= 0:
        return {"self_intersecting_pairs": 0, "pairs_tested": 0, "sampled": False}

    tree = cKDTree(centroids)
    pairs = tree.query_pairs(r=radius, output_type="ndarray")
    if len(pairs) == 0:
        return {"self_intersecting_pairs": 0, "pairs_tested": 0, "sampled": False}

    faces = mesh.faces
    a, b = faces[pairs[:, 0]], faces[pairs[:, 1]]
    shares_vertex = (a[:, :, None] == b[:, None, :]).any(axis=(1, 2))
    pairs = pairs[~shares_vertex]

    sampled = len(pairs) > max_pairs
    if sampled:
        rng = np.random.default_rng(seed)
        pairs = pairs[rng.choice(len(pairs), max_pairs, replace=False)]

    eps = mesh.scale * 1e-9
    hits = 0
    for start in range(0, len(pairs), 50_000):      # chunked to bound peak memory
        chunk = pairs[start:start + 50_000]
        hits += int(_tri_tri_intersect_batch(
            tris[chunk[:, 0]], tris[chunk[:, 1]], eps).sum())

    return {
        "self_intersecting_pairs": int(hits),
        "pairs_tested": int(len(pairs)),
        "sampled": bool(sampled),
    }


# ------------------------------------------------------ thin-feature probe

def thickness_metrics(mesh: trimesh.Trimesh, samples: int = 2000,
                      seed: int = 0) -> dict:
    """
    Wall/prong thickness probe: cast a ray inward from surface points along -normal and
    measure the distance to the next surface. Thin tails flag prongs or walls that would
    be unmanufacturable in metal.

    Reported in mesh units. TRELLIS.2 outputs are normalised to roughly a unit bounding
    box, so divide by the intended real-world size to interpret in mm.
    """
    if len(mesh.faces) == 0:
        return {"thickness_p01": None, "thickness_p05": None,
                "thickness_median": None, "thickness_samples": 0}

    pts, face_idx = trimesh.sample.sample_surface(mesh, samples, seed=seed)
    normals = mesh.face_normals[face_idx]
    eps = mesh.scale * 1e-5
    origins = pts - normals * eps

    locs, ray_idx, _ = mesh.ray.intersects_location(
        ray_origins=origins, ray_directions=-normals, multiple_hits=False
    )
    if len(ray_idx) == 0:
        return {"thickness_p01": None, "thickness_p05": None,
                "thickness_median": None, "thickness_samples": 0}

    dists = np.linalg.norm(locs - origins[ray_idx], axis=1)
    dists = dists[dists > eps]
    if len(dists) == 0:
        return {"thickness_p01": None, "thickness_p05": None,
                "thickness_median": None, "thickness_samples": 0}

    return {
        "thickness_p01": float(np.percentile(dists, 1)),
        "thickness_p05": float(np.percentile(dists, 5)),
        "thickness_median": float(np.median(dists)),
        "thickness_samples": int(len(dists)),
    }


# ------------------------------------------------------------- symmetry

def symmetry_metrics(mesh: trimesh.Trimesh, axis: str = "auto",
                     samples: int = 20000, seed: int = 0) -> dict:
    """
    Mirror-symmetry error: reflect sampled surface points through a plane at the centroid
    and measure two-sided Chamfer distance to the original surface, normalised by scale.

    This is the cheap, measurable stand-in for the SymTRELLIS concern. A ring that should
    be mirror-symmetric but shows 2% excess error is annoying as manufacturing geometry
    even if it renders beautifully.

    Two things this gets right that a naive version does not:

    1. **A noise floor is subtracted.** Random surface sampling means reflected points
       never land exactly on sampled points, so even a perfectly symmetric mesh scores
       nonzero. We measure that floor directly — Chamfer between two independent samples
       of the same mesh — and report `excess` above it. Without this the real signal sits
       under the noise.

    2. **'auto' never picks the minimum for scoring.** A piece asymmetric about x is still
       symmetric about y and z, so min-across-axes reports every mesh as symmetric — the
       exact opposite of what we want. 'auto' reports all three axes for inspection and
       marks the result unscored. To score symmetry, name the plane the design is actually
       supposed to be symmetric about.
    """
    scale = mesh.scale if mesh.scale > 0 else 1.0
    pts_a, _ = trimesh.sample.sample_surface(mesh, samples, seed=seed)
    pts_b, _ = trimesh.sample.sample_surface(mesh, samples, seed=seed + 1)
    centre = pts_a.mean(axis=0)
    a, b = pts_a - centre, pts_b - centre
    tree_a = cKDTree(a)

    # Noise floor: two independent samples of the same surface.
    floor = float((tree_a.query(b)[0].mean()) / scale)

    def err_for(ax: int) -> float:
        reflected = b.copy()
        reflected[:, ax] *= -1.0
        d_fwd = tree_a.query(reflected)[0].mean()
        d_rev = cKDTree(reflected).query(a)[0].mean()
        return float(((d_fwd + d_rev) / 2.0) / scale)

    axis_map = {"x": 0, "y": 1, "z": 2}
    raw = {name: err_for(i) for name, i in axis_map.items()}
    excess = {k: max(0.0, v - floor) for k, v in raw.items()}

    if axis == "auto":
        # Reported for inspection; deliberately NOT scored (see docstring).
        return {
            "symmetry_axis": None,
            "symmetry_error": None,
            "symmetry_excess_all": excess,
            "symmetry_raw_all": raw,
            "noise_floor": floor,
            "scored": False,
        }
    return {
        "symmetry_axis": axis,
        "symmetry_error": excess[axis],
        "symmetry_excess_all": excess,
        "symmetry_raw_all": raw,
        "noise_floor": floor,
        "scored": True,
    }


# ----------------------------------------------------------------- scoring

def score(metrics: dict) -> dict:
    """
    Roll metrics into a 0-1 ranking score. Deliberately simple and readable — this exists
    to order candidates, not to certify manufacturability.

    Weights are a starting point to be re-tuned once we have real jewelry meshes and know
    which failures actually cost Rhino time.
    """
    t, d, s = metrics["topology"], metrics["degeneracy"], metrics["self_intersection"]
    sym = metrics["symmetry"]
    faces = max(d["faces"], 1)

    penalties = {
        # Fragmentation: detached prongs / floating shards.
        "fragmentation": min(1.0, (t["connected_components"] - 1) / 10.0),
        # Non-manifold edges break QuadRemesh and NURBS conversion outright.
        "nonmanifold": min(1.0, t["nonmanifold_edges"] / (faces * 0.01)),
        "degenerate": min(1.0, d["degenerate_faces"] / (faces * 0.01)),
        "self_intersection": min(1.0, s["self_intersecting_pairs"] / (faces * 0.01)),
    }
    weights = {
        "fragmentation": 0.25,
        "nonmanifold": 0.30,
        "degenerate": 0.15,
        "self_intersection": 0.30,
    }
    if sym["scored"]:
        # 2% excess asymmetry ~= half penalty; 4%+ ~= full.
        penalties["asymmetry"] = min(1.0, sym["symmetry_error"] / 0.04)
        weights = {k: v * 0.85 for k, v in weights.items()}
        weights["asymmetry"] = 0.15
    total = sum(penalties[k] * weights[k] for k in weights)
    return {"score": round(1.0 - total, 4), "penalties":
            {k: round(v, 4) for k, v in penalties.items()}}


def evaluate(path: str, symmetry_axis: str = "auto", skip_slow: bool = False) -> dict:
    mesh = trimesh.load(path, force="mesh", process=False)
    if not isinstance(mesh, trimesh.Trimesh):
        raise ValueError(f"{path}: not a triangle mesh")

    metrics = {
        "path": path,
        "topology": topology_metrics(mesh),
        "degeneracy": degeneracy_metrics(mesh),
        "bounds": {
            "extents": [float(x) for x in mesh.extents],
            "scale": float(mesh.scale),
            "volume": float(mesh.volume),
            "surface_area": float(mesh.area),
        },
    }
    if skip_slow:
        metrics["self_intersection"] = {"self_intersecting_pairs": 0,
                                        "pairs_tested": 0, "sampled": False}
        metrics["thickness"] = {"thickness_p01": None, "thickness_p05": None,
                                "thickness_median": None, "thickness_samples": 0}
    else:
        metrics["self_intersection"] = self_intersection_metrics(mesh)
        metrics["thickness"] = thickness_metrics(mesh)
    metrics["symmetry"] = symmetry_metrics(mesh, axis=symmetry_axis)
    metrics.update(score(metrics))
    return metrics


def format_report(m: dict) -> str:
    t, d, b, s = m["topology"], m["degeneracy"], m["bounds"], m["self_intersection"]
    th, sym = m["thickness"], m["symmetry"]
    thin = ("n/a" if th["thickness_p01"] is None
            else f"{th['thickness_p01']:.5f} (p01) / {th['thickness_median']:.5f} (median)")
    return "\n".join([
        f"{m['path']}",
        f"  score              {m['score']}",
        f"  faces / verts      {d['faces']:,} / {d['vertices']:,}",
        f"  watertight         {t['watertight']}   boundary edges {t['boundary_edges']:,}",
        f"  non-manifold edges {t['nonmanifold_edges']:,}",
        f"  components         {t['connected_components']} "
        f"(largest {t['largest_component_volume_fraction']:.1%} of volume)",
        f"  degenerate faces   {d['degenerate_faces']:,}",
        f"  self-intersect     {s['self_intersecting_pairs']:,} pairs "
        f"of {s['pairs_tested']:,} tested{' (sampled)' if s['sampled'] else ''}",
        f"  thickness          {thin}",
        f"  symmetry excess    " + (
            f"{sym['symmetry_error']:.5f} (axis {sym['symmetry_axis']})"
            if sym["scored"] else
            ", ".join(f"{k}={v:.5f}" for k, v in sym["symmetry_excess_all"].items())
            + "  [unscored: pass --symmetry-axis]"
        ),
        f"  extents            {b['extents'][0]:.4f} x {b['extents'][1]:.4f} "
        f"x {b['extents'][2]:.4f}",
        f"  penalties          " + ", ".join(f"{k}={v}" for k, v in m["penalties"].items()),
    ])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("meshes", nargs="+", help="mesh files (PLY/STL/OBJ/GLB)")
    ap.add_argument("--json", help="write full metrics to this JSON file")
    ap.add_argument("--symmetry-axis", default="auto", choices=["auto", "x", "y", "z"])
    ap.add_argument("--skip-slow", action="store_true",
                    help="skip self-intersection and thickness probes")
    args = ap.parse_args()

    results = []
    for path in args.meshes:
        try:
            results.append(evaluate(path, args.symmetry_axis, args.skip_slow))
        except Exception as exc:  # keep going across a batch
            print(f"{path}: FAILED — {exc}", file=sys.stderr)

    if not results:
        return 1

    for m in sorted(results, key=lambda r: r["score"], reverse=True):
        print(format_report(m))
        print()

    if len(results) > 1:
        best = max(results, key=lambda r: r["score"])
        print(f"best: {best['path']} (score {best['score']})")

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(results, fh, indent=2)
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
