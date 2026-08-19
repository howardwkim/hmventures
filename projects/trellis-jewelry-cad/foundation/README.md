# trellis-jewelry-cad — Charter

## What this is

A pipeline that turns a **reference image of a piece of jewelry** into **manufacturable CAD
geometry**:

```
reference image
  ↓  TRELLIS.2 (MLX, Apple Silicon)      ← generation
mesh (untextured, high-res)
  ↓  QC + scoring + candidate selection  ← automated gate
best mesh
  ↓  QuadRemesh → SubD/NURBS → STEP      ← Rhino
CAD solid
```

## What we optimize for

**Naked geometry.** Everything downstream of the mesh — QuadRemesh, SubD/NURBS conversion,
STEP export — throws texture away. So PBR quality, material realism, and render fidelity are
worth zero here, and any stage that spends time or memory on them is pure overhead.

The geometry features that actually decide whether a generated ring is usable:

- thin prongs that must not fuse to the stone or each other
- **through-holes and openwork galleries that must stay open**
- undercuts
- engraving and sharp ridges
- closely spaced parallel surfaces
- symmetry, where the design is supposed to be symmetric

## Scope boundaries

**In scope:** image → mesh generation, mesh QC/scoring, candidate selection, and the export
handoff into Rhino.

**Out of scope (for now):**
- The Rhino side itself (QuadRemesh settings, NURBS strategy) — that's a separate workstream,
  and it should be designed against real generated meshes rather than in advance.
- Texture, materials, rendering, and product photography.
- Training or fine-tuning. This is an inference pipeline.

## Model choice

Primary: **TRELLIS.2** (MIT, 4B, Microsoft) via the MLX Apple Silicon fork.
Fallback/benchmark: **Hunyuan3D 2.1** shape stage.

Rationale and the evidence behind it: `../reference/model-survey.md`.
The short version: TRELLIS.2's O-Voxel representation is architecturally aimed at exactly the
topology cases jewelry stresses (open surfaces, enclosed structures, non-manifold), and it is
MIT-licensed end to end. Hunyuan's strongest differentiator is its texture stage, which we
discard.

**We do not assume TRELLIS wins every piece.** The pipeline is built to run more than one
generator over the same input and pick by score, because these models hallucinate unseen
geometry differently and neither is reliably better per-design.

## Design principles

1. **Skip work we throw away.** Fork the pipeline before texture sampling, not after.
2. **Every run is reproducible.** Seed, resolution tier, and model revision are recorded with
   every mesh.
3. **Selection is automated and measured, not eyeballed.** A mesh that fails QC should be
   rejected before a human ever opens Rhino.
4. **The generator is swappable.** TRELLIS today, a second generator alongside it tomorrow.
