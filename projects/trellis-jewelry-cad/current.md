# trellis-jewelry-cad — Current Status

**Last updated:** 2026-08-19

**Next:**
- **Hardware decision is the open gate.** Everything below assumes an Apple Silicon Mac with
  ≥24GB unified memory. The tier we can actually run (`512` / `1024_cascade` / `1536_cascade`)
  is unknown until measured — no published Mac memory figure exists above the `512` tier.
  Run the memory ladder in `SETUP.md` first; it decides the shape of the rest.
- Stand up the stock MLX fork and generate one asset with `app_mlx.py` **before** introducing
  `scripts/trellis_geom.py`, so a failure is attributable.
- `scripts/trellis_geom.py` has never been executed — it needs Apple Silicon. Expect debugging
  on first contact.
- Resolve the DINOv3 licensing question before the pipeline produces anything sold.

**Key decisions:**

- **TRELLIS.2 is the generator, single-model** (2026-08-19). Chosen on the architectural
  argument: O-Voxel targets exactly the topology cases jewelry stresses, and it is MIT
  end to end. Models whose main strength is PBR texturing are not a fit, since texture is
  discarded before Rhino. Explicitly **not** a comparative bake-off — this project is the
  TRELLIS workflow.

- **The MLX fork (`pedronaugusto/trellis2-apple`) is the right base, and the search results
  about it are wrong.** Web sources describe it as "postprocessing only" and last-updated in
  March 2026. Reading the source: it was last pushed **2026-08-06**, and `mlx_backend/`
  contains a full reimplementation of the generation path (flow models, VAE decoders, sparse
  ops, DINOv3, attention), backed by four custom Metal packages pinned to exact commits.
  There is a second, unrelated Mac port (`shivampkumar/trellis-mac`) that is **MPS, not MLX**,
  4 months staler, and has hole-filling disabled. Sources conflate the two constantly.
  Details: `reference/mac-ports.md`.

- **Geometry-only is a clean architectural cut, and it is worth taking** (2026-08-19).
  `run()` is: sparse structure → shape SLat → **texture SLat** → decode. Texture SLat feeds
  only the decode step, nothing in the shape path, so omitting it costs nothing downstream and
  saves ~40% of generation wall-clock at the top tier plus the UV/bake pass in `to_glb()`.
  Upstream has no flag for this, so it is a ~30-line reimplementation of `run()`:
  `scripts/trellis_geom.py`. See `reference/pipeline-architecture.md`.

- **`fill_holes()` defaults to OFF, against upstream** (2026-08-19). `decode_latent()` calls it
  unconditionally. For generic assets that is desirable; for jewelry it is a hazard — pierced
  galleries, filigree and prong gaps are holes by design, and sealing them yields geometry that
  renders fine and is wrong to manufacture. Which default is actually correct is an empirical
  question to settle on the first real openwork test piece.

- **"1536³" is decode resolution, not model capacity.** There is no 1536 flow model.
  `1536_cascade` runs the same 512→1024 shape cascade and cascades the decode to 1536. Worth
  having — it is where fine detail survives — but expectations should be set accordingly.

- **Selection is automated and measured.** `scripts/score_mesh.py` scores candidates
  reference-free on topology, degeneracy, self-intersection, wall thickness and mirror
  symmetry. Scores rank candidates; they are **not** pass/fail gates, because a genuine
  openwork pendant is correctly non-watertight and a naive "watertight = good" rule would
  reject exactly the pieces that matter most.

- **SymTRELLIS is a direction, not a dependency.** [arXiv 2606.04108](https://arxiv.org/abs/2606.04108)
  is real and targets a problem we have, but it needs a trained spatial-transform latent mapper
  and no released implementation is confirmed. Near-term substitute: measure mirror-symmetry
  error in the scorer (done) and enforce symmetry in post/Rhino, where the symmetry plane is
  usually known a priori from the design.

**Built so far:**

| File | Status |
|---|---|
| `scripts/score_mesh.py` | **Working and tested** on synthetic failure meshes |
| `scripts/test_score_mesh.py` | **Passing** — 12 assertions, runs anywhere, no Mac needed |
| `scripts/trellis_geom.py` | **Untested** — written against source, needs Apple Silicon |
| `SETUP.md` | Checklist with known traps marked; not itself verified |

Two real bugs were found and fixed while testing the scorer, both worth not reintroducing
(they are covered by `test_score_mesh.py`):
- The classic 11-axis triangle-triangle SAT degenerates on **coplanar** triangles, reporting
  disjoint coplanar pairs as intersecting. Fixed by adding in-plane edge normals (17 axes).
- Symmetry scoring with `axis='auto'` took the **minimum** error across axes — exactly
  backwards, since a piece asymmetric about x is still symmetric about y and z. `auto` now
  reports all three axes and refuses to score. A sampling noise floor (~0.006 on a smooth
  torus) is now measured and subtracted; without that the real signal sits under the noise.

**Not started:** the Rhino side (QuadRemesh settings, SubD/NURBS strategy, STEP export). That
is deliberate — it should be designed against real generated meshes, not in advance.
