# Generator choice — TRELLIS.2 vs Hunyuan3D 2.1

**Decision: TRELLIS.2 primary, Hunyuan3D 2.1 shape stage as fallback/benchmark.**
Recorded 2026-08-19. Reasoning is Howard's; provenance of each claim is marked below.

## The argument

The two models are optimized for different end states, and ours is unusual.

**TRELLIS.2** is built around O-Voxel, a field-free sparse voxel representation chosen
specifically to survive difficult topology — open surfaces, non-manifold geometry, internal
enclosed structures — without the lossy iso-surface conversion that field-based methods need.
*(Verified: stated in the upstream README's "Arbitrary Topology Handling" section.)*

That maps directly onto what jewelry stresses: thin prongs, through-holes, undercuts,
engraving, sharp ridges, closely spaced surfaces, internal galleries.

**Hunyuan3D 2.1** splits cleanly into Hunyuan3D-Shape (3.3B, image→geometry) and
Hunyuan3D-Paint (2B, mesh+image→PBR). Its most mature, most differentiated capability is
production-grade PBR texturing and a texture-any-mesh workflow.
*(User-supplied; not independently verified in this survey.)*

**We discard texture entirely** at `mesh → QuadRemesh → SubD/NURBS → STEP`. So Hunyuan's
strongest advantage is spent on output we delete, while TRELLIS.2's strongest advantage is
precisely the axis we're graded on.

## Benchmark evidence — and how much weight it carries

Microsoft's TRELLIS.2 paper benchmarks against Hunyuan3D 2.1 directly and reports higher image
alignment and 3D similarity across CLIP, ULIP-2 and Uni3D:

| Metric | TRELLIS.2 | Hunyuan3D 2.1 |
|---|---|---|
| ULIP-2 | 0.477 | 0.474 |
| Uni3D | 0.436 | 0.427 |
| Human preference, shape only | 69.0% | 7.5% |

*(User-supplied figures, not re-verified against the paper in this survey. Flagged because
they are load-bearing for the decision and should be checked before being quoted externally.)*

**Read these with the discount they deserve.** This is Microsoft evaluating Microsoft's model
against a competitor it selected as a baseline. The automatic metrics are near-identical —
0.477 vs 0.474 is not a meaningful gap. The 69.0% vs 7.5% human-preference spread is enormous
and comes from the interested party; the *direction* is credible, the magnitude is not
evidence we should lean on.

The architectural argument above is the real basis for the decision. The benchmarks are
consistent with it, not the reason for it.

## Where each genuinely wins

| | TRELLIS.2 | Hunyuan3D 2.1 |
|---|---|---|
| Fine geometry | Likely better | Very good |
| Sharp features | Better architectural fit | Good |
| Complex topology | Major strength | Good |
| Internal / enclosed geometry | Major strength | Less emphasized |
| PBR texturing | Excellent | Major strength |
| Texture-any-mesh workflow | Yes | Very mature |
| **Geometry for downstream CAD** | **Pick** | Second |
| Mac path | Maintained MLX fork | Community options |
| Licensing | MIT end to end | Tencent terms — check |

## The thing we are explicitly not assuming

**TRELLIS does not win every piece.** These models infer occluded geometry differently, and
which one is right for a given design is not predictable from the reference image. Running
both over the same input is cheap relative to the cost of a human discovering the failure in
Rhino.

So the pipeline treats generators as **interchangeable candidate producers** feeding one
scorer (`scripts/score_mesh.py`). Adding Hunyuan later is a new producer, not a rewrite. That
is a deliberate architectural concession to genuine uncertainty about which model is better,
and it is why selection is automated rather than left to taste.

## Sources

- https://github.com/microsoft/TRELLIS.2
- https://huggingface.co/microsoft/TRELLIS.2-4B
- https://arxiv.org/abs/2606.04108 (SymTRELLIS — benchmarks both models on symmetry error)
