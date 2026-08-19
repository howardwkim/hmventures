# Setup — TRELLIS.2 MLX on Apple Silicon

Target: `pedronaugusto/trellis2-apple` (MLX backend). Rationale in
`reference/mac-ports.md`.

**None of this has been executed.** It was assembled by reading the fork's source and
`requirements_macos.txt` on a Linux container with no Apple Silicon available. Treat it as a
checklist with the known traps marked, not a verified recipe.

## Prerequisites — the ones that actually bite

| Requirement | Why it is non-negotiable |
|---|---|
| **PyTorch ≥ 2.11.0** | `mtlgemm` links `at::mps::dispatch_sync_with_rethrow`, which only moved into that namespace in torch 2.11 (PR #167445). Torch 2.6–2.10 fail to link — not degrade, fail. |
| **Python 3.13** | The fork's verified configuration. |
| **macOS 26.2 / M3 Max** | The author's verified configuration. Other M-series should work; this is what is actually tested. |
| **Xcode Metal Toolchain** | Needed to build the four Metal packages. `xcodebuild -downloadComponent MetalToolchain` |
| **HuggingFace auth** | DINOv3 is a **gated** model — access must be requested and granted before first run. |
| **≥ 24GB unified memory** | Documented floor. See the memory note below. |

## Steps

```bash
git clone https://github.com/pedronaugusto/trellis2-apple.git
cd trellis2-apple

# Gated model — request access first, then authenticate:
#   https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m
hf auth login

python3.13 -m venv .venv && source .venv/bin/activate

# The four Metal packages are pinned to exact commits ON PURPOSE. Do not float them to
# main — the pins encode fixes for a BVH stack overflow that silently dropped subtrees on
# deep meshes, and a depth-test bug. Deep meshes is exactly our case.
pip install --no-build-isolation -r requirements_macos.txt

# Sanity check before touching our own scripts:
python app_mlx.py     # Gradio UI, generate one asset end to end
```

Get the stock fork working on its own terms **before** introducing
`scripts/trellis_geom.py`. If the geometry-only path fails, we need to know whether it is
our patch or the install.

## Memory: measure, do not assume

There is **no published Mac figure for `1024_cascade` or `1536_cascade`.** The only Mac
number that exists is ~18GB peak at the `512` tier, and that is from the *other* (MPS) port.

So the first real task is a memory ladder, not a jewelry test:

```bash
# Watch peak unified memory per tier. Stop at the first tier that swaps.
python trellis_geom.py assets/example_image/T.png --resolution 512   --outdir out/
python trellis_geom.py assets/example_image/T.png --resolution 1024  --outdir out/
python trellis_geom.py assets/example_image/T.png --resolution 1536  --outdir out/
```

If a tier will not fit, lower `--max-num-tokens` (default 49152) before giving up on the
tier. That is the knob bounding cascade memory.

Note the fork's own Gradio app exposes only `512` and `1024` in its resolution radio even
though `1536_cascade` is wired up. Read that as 1536 being unproven on Mac rather than
unavailable.

## Our scripts

```bash
pip install trimesh numpy scipy rtree      # scorer dependencies

# Geometry-only generation, three candidate seeds
python scripts/trellis_geom.py ring.png --resolution 1024 --seeds 0,1,2 --outdir out/

# Rank the candidates. Name the symmetry plane the design should actually be symmetric
# about -- without it, symmetry is reported but NOT scored, deliberately.
python scripts/score_mesh.py out/*.ply --symmetry-axis x --json out/scores.json

# Scorer self-test (no Apple hardware needed -- this runs anywhere)
python scripts/test_score_mesh.py
```

## Licensing gate before anything is sold

TRELLIS.2 itself is MIT, code and weights. Two dependencies are not:

- **DINOv3** (`facebook/dinov3-vitl16-pretrain-lvd1689m`) — gated, Meta's own licence.
  **Confirm commercial terms before this pipeline produces anything sold.** This is the
  one genuinely open licensing question and MIT on TRELLIS.2 does not resolve it.
- **BiRefNet** — background removal in this fork. Verify terms, but note this fork's choice
  is already the safer one: the MPS port uses RMBG-2.0, which is CC BY-NC (non-commercial).
