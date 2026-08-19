# Pipeline architecture — where we cut TRELLIS.2 for CAD

**Written 2026-08-19** against `pedronaugusto/trellis2-apple` @ `1734724`
(`trellis2/pipelines/trellis2_image_to_3d.py`).

## The seam

`Trellis2ImageTo3DPipeline.run()` is four stages:

```python
coords          = self.sample_sparse_structure(cond_512, ss_res, num_samples, ...)   # 1
shape_slat, res = self.sample_shape_slat_cascade(cond_512, cond_1024, ...)           # 2  ← geometry
tex_slat        = self.sample_tex_slat(cond_1024, tex_model, shape_slat, ...)        # 3  ← DISCARD
out_mesh        = self.decode_latent(shape_slat, tex_slat, res)                      # 4
```

Stage 3 is a full flow-model sampling pass that exists only to produce surface attributes.
**We want stages 1, 2, 4 and not 3.** That is the entire architectural insight of this
project, and it is a clean cut — `tex_slat` is not consumed by the shape path at all, only by
`decode_latent`.

Cost avoided: ~40% of generation wall-clock at the top tier (25s of 60s on H100), the texture
model's memory residency, plus the UV-unwrap and texture bake inside `to_glb()`.

## Why it needs a small patch rather than a flag

`decode_latent` takes both latents and unconditionally decodes texture:

```python
def decode_latent(self, shape_slat, tex_slat, resolution):
    meshes, subs = self.decode_shape_slat(shape_slat, resolution)
    tex_voxels   = self.decode_tex_slat(tex_slat, subs)     # ← would fail on None
    for m, v in zip(meshes, tex_voxels):
        m.fill_holes()                                      # ← see below
        out_mesh.append(MeshWithVoxel(m.vertices, m.faces, ..., attrs=v.feats, ...))
```

There is no `skip_texture` argument anywhere in `run()`. So the geometry-only path is a
~30-line reimplementation of `run()` that stops at `decode_shape_slat` and returns raw
vertices/faces. That is `scripts/trellis_geom.py`.

`decode_shape_slat` returns meshes with `.vertices` and `.faces` directly — everything CAD
needs. No `MeshWithVoxel` wrapper, no attribute volume, no GLB.

## `fill_holes()` is a real risk for jewelry

`decode_latent` calls `m.fill_holes()` on every mesh, unconditionally.

For a generic asset that's desirable — it produces watertight output. For **jewelry it is
actively dangerous**: pierced galleries, filigree, openwork, and the gaps between prongs are
holes *by design*. A hole-filling pass that seals them produces a mesh that looks fine in a
render and is wrong as manufacturing geometry.

`scripts/trellis_geom.py` therefore exposes `--fill-holes/--no-fill-holes` and **defaults to
off**, and the QC scorer counts boundary loops so the difference is measurable rather than a
matter of opinion. Which default is correct is an empirical question to settle on the first
real openwork test piece — not one to guess now.

## Export format

Skip `o_voxel.postprocess.to_glb()` entirely. It bundles three things:

- `decimation_target` (default 1M faces) — decimation we may not want
- `texture_size` / UV unwrap / bake — pure waste here
- `remesh=True` — **this one may actually be worth keeping**

That last point deserves a real A/B rather than a reflex. `remesh` cleans up topology, and
cleaner topology upstream of QuadRemesh may beat feeding QuadRemesh raw marching-cubes output.
But it is coupled to the texture path in `to_glb`, so testing it means calling it separately.

For CAD handoff we write **PLY** (binary, compact, exact) and optionally **STL**. Both carry
vertices and faces and nothing else, which is the whole point.

## Candidate generation and selection

`run()` already exposes `num_samples` and `seed`. Generating N candidates from one image is
a parameter change, not new architecture. Combined with the scorer, that gives:

```
image → N candidates (seed sweep) → QC scores → best-scoring mesh → Rhino
```

This is also the natural place a second generator (Hunyuan3D shape stage) plugs in: it becomes
another candidate producer feeding the same scorer, which is exactly the "run both and pick"
design the project charter calls for.

## What the scorer measures

`scripts/score_mesh.py`, geometry-only QC with no reference mesh required:

| Metric | Why it matters for jewelry |
|---|---|
| watertight / boundary loops | distinguishes genuine openwork from generation tears |
| non-manifold edges | QuadRemesh and NURBS conversion choke on these |
| connected components | detached prongs, floating shards |
| degenerate faces | zero-area triangles break downstream remeshing |
| self-intersection sampling | surfaces that fused where they should be separate |
| thin-feature probe | prongs collapsing below manufacturable thickness |
| mirror-symmetry error | the SymTRELLIS concern, measured on our own output |
| volume / surface area / bbox | sanity + scale checks |

Scores are advisory ranking signals, not pass/fail gates — a real openwork pendant *should*
be non-watertight, so a naive "watertight = good" rule would reject exactly the pieces we care
most about.

## On SymTRELLIS

[arXiv 2606.04108](https://arxiv.org/abs/2606.04108). Real, and aimed squarely at a problem we
have — it enforces finite point-group symmetry during flow sampling by averaging predicted
velocities across symmetry-equivalent transforms at each ODE step, without retraining the VAE
or flow model.

**But it is not a drop-in.** It needs a "spatial-transform latent mapper" — a learned linear
operator on voxel latents — that has to be trained, and no released implementation is
confirmed. Treat it as a direction, not a dependency.

The cheap approximation available now: measure mirror-symmetry error in the scorer (done), and
enforce symmetry in post — mirror the better half, or impose it in Rhino where a ring is
supposed to be exactly C_n symmetric anyway. For most jewelry the symmetry plane is known a
priori from the design, which is a significant advantage over the general case SymTRELLIS
solves.
