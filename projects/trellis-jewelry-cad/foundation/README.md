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

**TRELLIS.2** (MIT, 4B, Microsoft) via the MLX Apple Silicon fork. Single generator — this
project is the TRELLIS workflow, not a model bake-off.

Why it fits: O-Voxel is architecturally aimed at exactly the topology cases jewelry stresses
(open surfaces, enclosed structures, non-manifold geometry), and it is MIT-licensed end to end.
Alternatives that lead with PBR texturing have little to offer here — we discard texture before
Rhino ever sees the mesh.

**We still do not assume any single generation is good.** These models hallucinate occluded
geometry, and the same image with a different seed can produce a materially better or worse
ring. So the pipeline generates N candidates per image and picks by score rather than trusting
one run. See `../reference/pipeline-architecture.md`.

## Design principles

1. **Skip work we throw away.** Fork the pipeline before texture sampling, not after.
2. **Every run is reproducible.** Seed, resolution tier, and model revision are recorded with
   every mesh.
3. **Selection is automated and measured, not eyeballed.** A mesh that fails QC should be
   rejected before a human ever opens Rhino.
4. **The generator is swappable.** TRELLIS today, a second generator alongside it tomorrow.
