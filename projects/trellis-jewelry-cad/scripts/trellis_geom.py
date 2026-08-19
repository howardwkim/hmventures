#!/usr/bin/env python3
"""
TRELLIS.2 geometry-only runner for the jewelry -> CAD pipeline (Apple Silicon / MLX).

Runs sparse-structure sampling and shape-SLat sampling, then decodes shape directly to a
mesh -- SKIPPING texture-SLat sampling and the GLB texture bake entirely. Everything
downstream (QuadRemesh -> SubD/NURBS -> STEP) discards texture, so generating it is pure
waste: roughly 40% of generation wall-clock at the top tier, plus the texture model's
memory residency and the UV/bake pass in to_glb().

Why this is a separate script rather than a flag: upstream's `run()` has no skip-texture
option, and `decode_latent()` unconditionally calls `decode_tex_slat()` (which fails on
None) and `fill_holes()`. See ../reference/pipeline-architecture.md.

STATUS: WRITTEN AGAINST SOURCE, NOT YET EXECUTED. Authored by reading
pedronaugusto/trellis2-apple @ 1734724; it has never been run, because it requires Apple
Silicon + MLX. Expect to debug it on first contact with real hardware. The stage sequence
it reproduces is verified against upstream source; the MLX-specific wiring is not.

Usage:
    python trellis_geom.py input.png --resolution 1024 --seeds 0,1,2 --outdir out/
"""

import argparse
import json
import os
import pathlib
import sys
import time

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")

RESOLUTIONS = {"512": "512", "1024": "1024_cascade", "1536": "1536_cascade"}


def build_pipeline(weights: str, backend: str):
    """Load the MLX pipeline on Apple Silicon, or the stock CUDA one elsewhere."""
    if backend == "mlx":
        from mlx_backend.pipeline import create_mlx_pipeline
        return create_mlx_pipeline(weights_path=weights)
    from trellis2.pipelines import Trellis2ImageTo3DPipeline
    pipe = Trellis2ImageTo3DPipeline.from_pretrained(weights)
    pipe.cuda()
    return pipe


def sample_geometry(pipeline, image, pipeline_type: str, seed: int,
                    ss_steps: int, shape_steps: int, ss_cfg: float, shape_cfg: float,
                    max_num_tokens: int, fill_holes: bool):
    """
    Reproduce Trellis2ImageTo3DPipeline.run() stages 1, 2 and 4, omitting stage 3
    (texture SLat sampling). Mirrors upstream control flow exactly; see the source at
    trellis2/pipelines/trellis2_image_to_3d.py::run.
    """
    import torch

    image = pipeline.preprocess_image(image)
    torch.manual_seed(seed)

    cond_512 = pipeline.get_cond([image], 512)
    cond_1024 = pipeline.get_cond([image], 1024) if pipeline_type != "512" else None

    ss_res = {"512": 32, "1024": 64, "1024_cascade": 32, "1536_cascade": 32}[pipeline_type]
    ss_params = {"steps": ss_steps, "guidance_strength": ss_cfg}
    shape_params = {"steps": shape_steps, "guidance_strength": shape_cfg}

    coords = pipeline.sample_sparse_structure(cond_512, ss_res, 1, ss_params)

    if pipeline_type == "512":
        shape_slat = pipeline.sample_shape_slat(
            cond_512, pipeline.models["shape_slat_flow_model_512"], coords, shape_params)
        res = 512
    elif pipeline_type == "1024":
        shape_slat = pipeline.sample_shape_slat(
            cond_1024, pipeline.models["shape_slat_flow_model_1024"], coords, shape_params)
        res = 1024
    else:
        target = 1024 if pipeline_type == "1024_cascade" else 1536
        shape_slat, res = pipeline.sample_shape_slat_cascade(
            cond_512, cond_1024,
            pipeline.models["shape_slat_flow_model_512"],
            pipeline.models["shape_slat_flow_model_1024"],
            512, target, coords, shape_params, max_num_tokens)

    # --- texture SLat sampling deliberately omitted here ---

    if hasattr(torch, "mps") and torch.backends.mps.is_available():
        torch.mps.empty_cache()
    elif torch.cuda.is_available():
        torch.cuda.empty_cache()

    meshes, _subs = pipeline.decode_shape_slat(shape_slat, res)
    mesh = meshes[0]

    # Upstream calls fill_holes() unconditionally. For jewelry that is a real hazard:
    # pierced galleries, filigree and prong gaps are holes BY DESIGN, and sealing them
    # yields geometry that renders fine and is wrong to manufacture. Off by default.
    if fill_holes:
        mesh.fill_holes()

    return mesh, res


def export(mesh, out_base: pathlib.Path, formats) -> list:
    """Write raw vertices/faces. No UVs, no attributes, no texture -- that is the point."""
    import numpy as np
    import trimesh

    verts = mesh.vertices.detach().cpu().numpy() if hasattr(mesh.vertices, "detach") \
        else np.asarray(mesh.vertices)
    faces = mesh.faces.detach().cpu().numpy() if hasattr(mesh.faces, "detach") \
        else np.asarray(mesh.faces)

    tm = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    written = []
    for fmt in formats:
        path = out_base.parent / f"{out_base.name}.{fmt}"
        tm.export(path)
        written.append(str(path))
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("image")
    ap.add_argument("--resolution", default="1024", choices=list(RESOLUTIONS))
    ap.add_argument("--seeds", default="0",
                    help="comma-separated seeds; each produces one candidate mesh")
    ap.add_argument("--outdir", default="out")
    ap.add_argument("--weights", default="weights/TRELLIS.2-4B")
    ap.add_argument("--backend", default="mlx", choices=["mlx", "cuda"])
    ap.add_argument("--formats", default="ply", help="comma-separated: ply,stl,obj")
    ap.add_argument("--ss-steps", type=int, default=25)
    ap.add_argument("--shape-steps", type=int, default=25)
    ap.add_argument("--ss-cfg", type=float, default=7.5)
    ap.add_argument("--shape-cfg", type=float, default=3.0)
    ap.add_argument("--max-num-tokens", type=int, default=49152,
                    help="cascade memory bound; lower this first if a tier will not fit")
    ap.add_argument("--fill-holes", action="store_true",
                    help="re-enable upstream fill_holes() (seals openwork -- see docs)")
    args = ap.parse_args()

    from PIL import Image

    outdir = pathlib.Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    formats = [f.strip() for f in args.formats.split(",") if f.strip()]
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    pipeline_type = RESOLUTIONS[args.resolution]

    print(f"loading pipeline ({args.backend}, {args.weights})", file=sys.stderr)
    t0 = time.time()
    pipeline = build_pipeline(args.weights, args.backend)
    print(f"pipeline loaded in {time.time() - t0:.1f}s", file=sys.stderr)

    image = Image.open(args.image)
    stem = pathlib.Path(args.image).stem
    manifest = []

    for seed in seeds:
        t0 = time.time()
        mesh, res = sample_geometry(
            pipeline, image, pipeline_type, seed,
            args.ss_steps, args.shape_steps, args.ss_cfg, args.shape_cfg,
            args.max_num_tokens, args.fill_holes)
        elapsed = time.time() - t0

        base = outdir / f"{stem}_r{args.resolution}_s{seed}"
        written = export(mesh, base, formats)
        record = {
            "source_image": args.image,
            "seed": seed,
            "resolution": args.resolution,
            "pipeline_type": pipeline_type,
            "decode_resolution": res,
            "backend": args.backend,
            "fill_holes": args.fill_holes,
            "ss_steps": args.ss_steps,
            "shape_steps": args.shape_steps,
            "ss_cfg": args.ss_cfg,
            "shape_cfg": args.shape_cfg,
            "max_num_tokens": args.max_num_tokens,
            "generation_seconds": round(elapsed, 2),
            "files": written,
        }
        manifest.append(record)
        print(f"seed {seed}: {elapsed:.1f}s -> {', '.join(written)}", file=sys.stderr)

    # Every run is reproducible: seed, tier and params travel with the mesh.
    manifest_path = outdir / f"{stem}_manifest.json"
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"wrote {manifest_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
