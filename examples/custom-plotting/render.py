"""A synthetic counting example with two renderer choices and bound evidence."""

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer", choices=("matplotlib", "analyb"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)

    # Literal samples and an independent hand count make the oracle inspectable.
    samples = [0.25, 0.75, 1.25, 1.50, 1.75, 2.25]
    edges = [0.0, 1.0, 2.0, 3.0]
    counts, _ = np.histogram(samples, bins=edges)
    if counts.tolist() != [2, 3, 1] or int(counts.sum()) != len(samples):
        raise RuntimeError("Synthetic counts disagree with the hand-counted oracle")
    source = out / "counts.json"
    write_json(source, {"samples": samples, "edges": edges, "counts": counts.tolist(),
                        "expected": [2, 3, 1], "total": len(samples)})

    # Use the checker's exact format contract without requiring analyb to draw.
    gate_path = Path(__file__).resolve().parents[2] / "skills" / "render-review" / "scripts" / "render_gate.py"
    spec = importlib.util.spec_from_file_location("example_render_gate", gate_path)
    gate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = gate
    spec.loader.exec_module(gate)
    records = []
    for index, count in enumerate(counts, start=1):
        records.append({"key": f"bin-{index}", "value": int(count), "text": str(count),
                        "context": f"Bin {index}", "source": "counts", "page": 1})
    records.append({"key": "total", "value": len(samples), "text": str(len(samples)),
                    "context": "Total entries", "source": "counts", "page": 1})

    if args.renderer == "analyb":
        import analyb as ab
        hist = ab.Hist1D(counts, edges, errors=np.zeros(3), label="Synthetic entries")
        fig, ax = ab.hist1d_plot(hist, xlabel="Synthetic coordinate", style="stairs",
                               atlas=False, figsize=(6.4, 4.8))
        renderer_identity = {"name": "analyb", "version": ab.__version__,
                             "module_sha256": digest(Path(ab.__file__))}
    else:
        fig, ax = plt.subplots(figsize=(6.4, 4.8), layout="constrained")
        ax.stairs(counts, edges, color="black", linewidth=2)
        ax.set_xlabel("Synthetic coordinate")
        renderer_identity = {"name": "matplotlib", "version": matplotlib.__version__}
    ax.set_ylabel("Entries $N_i$")
    ax.tick_params(axis="x", pad=6)
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 4.2)
    ax.set_xticks(edges)
    ax.set_yticks(range(5))
    for index, count in enumerate(counts, start=1):
        ax.text(index - 0.5, float(count) + 0.18, f"Bin {index}: {count}",
                ha="center", va="bottom", fontsize=10)
    ax.text(0.98, 0.96, f"Total entries: {len(samples)}", transform=ax.transAxes,
            ha="right", va="top", fontsize=10)
    pdf = out / "example-counts.pdf"
    if args.renderer == "analyb":
        ab.save_figure(fig, "counts", script_id="example", save_path=str(out),
                       figure_check="raise", final_width_cm=16.0)
    else:
        fig.savefig(pdf)
        plt.close(fig)

    # The one-panel inventory is checked against the final artifact, not assumed.
    text = subprocess.check_output(["pdftotext", "-layout", str(pdf), "-"], text=True)
    info = subprocess.check_output(["pdfinfo", str(pdf)], text=True)
    pages = next(int(line.split(":", 1)[1]) for line in info.splitlines()
                 if line.startswith("Pages:"))
    labels = ["Synthetic coordinate", "Entries", "Total entries", "Bin 1", "Bin 2", "Bin 3"]
    if pages != 1 or any(label not in text for label in labels):
        raise RuntimeError("Rendered one-page inventory or labels do not match")
    inventory = out / "inventory.json"
    write_json(inventory, {"pdf_sha256": digest(pdf), "pages": pages,
                            "labels_checked": labels, "renderer": renderer_identity,
                            "recipe_sha256": digest(Path(__file__)),
                            "scope": "one final page and expected labels; not visual acceptance"})
    write_json(out / "values.json", {"schema": gate.VALUES_SCHEMA,
        "schema_version": gate.VALUES_VERSION, "match_rule": gate.MATCH_RULE,
        "producer": "synthetic-counting-example", "sources": {
            "counts": {"path": str(source), "sha256": digest(source)}}, "values": records})
    write_json(out / "applicability.json", {"checks": {
        "build": {"status": "not_applicable", "reason": "Direct Matplotlib PDF, no TeX build"},
        "bibliography": {"status": "not_applicable", "reason": "Authored synthetic inputs only"},
        "inventory": {"status": "external", "reason": "Single-page custom composer checked labels/page count",
                      "path": str(inventory), "sha256": digest(inventory), "pdf_sha256": digest(pdf)},
        "plan": {"status": "not_applicable", "reason": "One declared three-bin synthetic comparison"},
        "reuse": {"status": "not_applicable", "reason": "New independent example artifact"}}})
    print(pdf)


if __name__ == "__main__":
    main()
