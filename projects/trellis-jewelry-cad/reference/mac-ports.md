# TRELLIS.2 on Apple Silicon — port survey

**Surveyed 2026-08-19.** Findings below come from reading the cloned source, not from READMEs
or search summaries, both of which were misleading on several points.

## There are two Mac ports and they are not the same thing

| | `pedronaugusto/trellis2-apple` | `shivampkumar/trellis-mac` |
|---|---|---|
| Backend | **MLX** (+ custom Metal kernels) | PyTorch **MPS** |
| Last commit | **2026-08-06** | 2026-04-28 |
| Scope | Full inference stack reimplemented | Patch set over upstream |
| Background removal | BiRefNet (`ZhengPeng7/BiRefNet`) | RMBG-2.0 (**CC BY-NC 4.0**) |
| Hole filling | Present (upstream path) | **Disabled** — needs `cumesh` |
| Verdict | **Primary** | Reference only |

Search results conflate these two constantly, and describe the MLX fork as "postprocessing
only" and as last-updated in March. Both claims are wrong.

## Why the MLX fork is the right base

`mlx_backend/` is not a thin shim. It contains a reimplementation of the whole generation
path:

```
attention.py  flow_models.py  vae_decoders.py  structure_decoder.py
sparse_conv.py  sparse_ops.py  sparse_tensor.py  transformer_block.py
dinov3.py  rope.py  norm.py  vae_blocks.py  pipeline.py  adapters.py  convert.py
```

It is backed by four custom Metal packages written by the same author and pinned to exact
commits in `requirements_macos.txt` — `mtldiffrast`, `mtlbvh`, `mtlmesh` (installed as
`cumesh`), `mtlgemm` (installed as `flex_gemm`). The pins are deliberate; the file documents
two real bugs (a BVH traversal stack overflow that silently dropped subtrees on deep meshes,
and a depth-test error) that a floating `main` had masked.

Stated verified configuration: **M3 Max / macOS 26.2 / torch 2.11.0 / Python 3.13**.

`torch>=2.11.0` is a hard floor, not a preference — `mtlgemm` links against
`at::mps::dispatch_sync_with_rethrow`, which only moved into that namespace in PyTorch 2.11.
Torch 2.6–2.10 will fail to link.

## Licensing — matters, because this is commercial work

- **TRELLIS.2 code + weights: MIT.** Clean.
- **The MLX fork uses BiRefNet** for background removal. The MPS port uses **RMBG-2.0, which
  is CC BY-NC 4.0** — non-commercial. Choosing the MLX fork sidesteps that problem rather
  than inheriting it. This is an underrated reason to prefer it.
- **DINOv3** (`facebook/dinov3-vitl16-pretrain-lvd1689m`) is the image encoder and is a
  **gated** HF model under Meta's own license, not MIT. **Confirm its commercial terms before
  this pipeline produces anything sold.** This is the one open licensing question in the stack
  and it is not resolved by TRELLIS.2 being MIT.
- `nvdiffrast` / `nvdiffrec` carry their own non-MIT terms upstream. The Mac path replaces
  these with `mtldiffrast`, so they likely drop out — worth confirming once installed.

## Resolution tiers — the "1536³" label is misleading

From `trellis2/pipelines/trellis2_image_to_3d.py`, `pipeline_type` selects:

| Tier | Shape flow models | Texture flow model | Sparse structure res |
|---|---|---|---|
| `512` | 512 | 512 | 32 |
| `1024` | 1024 | 1024 | 64 |
| `1024_cascade` | 512 → 1024 | 1024 | 32 |
| `1536_cascade` | 512 → 1024 (target 1536) | 1024 | 32 |

There is **no 1536 flow model**. `1536_cascade` runs the same 512→1024 shape cascade and
cascades the *decode* to 1536. So "1536³" is O-Voxel decode resolution, not model capacity.
Useful — it's where fine detail survives — but it is not a bigger model, and expectations
should be set accordingly.

Microsoft's published timings (H100, full pipeline including texture):

| Res | Total | Shape | Texture |
|---|---|---|---|
| 512³ | ~3s | 2s | 1s |
| 1024³ | ~17s | 10s | 7s |
| 1536³ | ~60s | 35s | **25s** |

Texture is ~40% of generation time at the top tier — all of it wasted for our use case. See
`pipeline-architecture.md`.

Note: the fork's Gradio app (`app_mlx.py`) maps a `"1536"` UI option to `1536_cascade`, but
the radio button only exposes `["512", "1024"]`. Read that as 1536 being plumbed but not
routinely exercised on Mac. Treat it as unproven until we measure it.

## Memory

Upstream states 24GB VRAM minimum on NVIDIA. The MPS port states 24GB unified memory and
reports ~18GB peak on an M4 Pro at the `512` tier.

**No published Mac figure exists for `1024_cascade` or `1536_cascade`.** Measuring that is a
step-one task, not an assumption. `max_num_tokens` (default 49152) in `run()` is the knob that
bounds cascade memory, and is the first thing to turn down if a tier won't fit.

## Sources

- https://github.com/microsoft/TRELLIS.2
- https://huggingface.co/microsoft/TRELLIS.2-4B
- https://github.com/pedronaugusto/trellis2-apple
- https://github.com/shivampkumar/trellis-mac
