# Two renderers, one evidence contract

This example counts six synthetic entries into three fixed bins. The hand-counted
result is `[2, 3, 1]`; there are no measured data, physics selections or inferred
uncertainties. The same recipe can draw with plain Matplotlib or analyb.

From the repository root, using a project Python environment with NumPy and
Matplotlib:

```bash
python examples/custom-plotting/render.py --renderer matplotlib --out build/custom
python skills/render-review/scripts/render_gate.py numbers build/custom/example-counts.pdf build/custom/values.json
python skills/render-review/scripts/render_gate.py gate --session build/custom --pdf build/custom/example-counts.pdf --values build/custom/values.json --contract build/custom/applicability.json --out build/custom/gate
```

For analyb, [requirements-analyb.txt](requirements-analyb.txt) pins the reviewed
public snapshot. Once that commit is available on GitHub, install it into your
own project virtual environment, then use `--renderer analyb --out build/analyb`.
The recipe uses
its histogram/drawing/save APIs and writes its figure-check sidecar. It does not
replace your plotting style with the example's style. An output directory must
be new: use a distinct directory for a new run so old evidence cannot be mixed.

The script records source samples, an independent hand-count check, formatted
values, renderer identity and an artifact-bound one-page inventory check. The
gate's `numbers` command checks text presence and context; arithmetic was checked
separately before rendering. This custom example uses explicit external inventory
evidence rather than pretending to implement a multi-page analyb page map.

To test stale evidence, edit a copy of `counts.json` after rendering and rerun
`numbers`: its recorded source hash must fail. To test a missing printed value,
change a copy of `values.json` so a record expects `999` and rerun `numbers`.
Keep these deliberately broken copies separate from accepted outputs.

A ready gate is preparation for visual review, not its completion. Ask a reviewer
to read each bin height and the total at final size, verify units/labels and
distinguish the synthetic example from measured results. The example declares no
bibliography because it uses only explicitly authored synthetic inputs; reports
making sourced claims should follow the [citation example](../citations/README.md).
