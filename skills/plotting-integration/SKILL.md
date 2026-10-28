---
name: plotting-integration
description: Adapt an existing scientific plotting or report pipeline to emit evidence for numerical, inventory and visual review. Use when bringing a custom renderer into the scientific-agents workflow or connecting analyb-compatible review manifests without replacing the plotting library.
---

# Plotting integration

Read [plot evidence](../../workflows/plot-evidence.md). Inspect the actual plotting
entry point, scientific definition owners, saving/composition path and imported
library revision. Preserve the user's plotting library and conventions.

1. Identify existing figure checks, numerical evidence, figure/page inventories
   and provenance. Name missing capabilities before proposing adapters.
2. Establish the comparison's scientific contract: quantities, units, bin edges,
   normalization, ratios and uncertainties. Do not change these to fit an API.
3. Add evidence emission beside the code that saves figures, typesets numbers
   and places panels. Derive inventories from the composition loop, not a second
   guessed layout. Bind evidence to exact artifacts and input identities.
4. Reuse supported analyb formats or supply equivalent explicit evidence when a
   schema is unsuitable. Never call a missing check passed or irrelevant merely
   because the custom renderer cannot emit a manifest.
5. Test a small successful example and deliberate missing, changed and stale
   evidence. Verify rendered numbers against an independent calculation; checking
   printed text presence alone is not numerical validation.
6. Hand back the changed entry points, evidence files, checks performed and
   remaining reading tasks. Visual review judges readability of actual final
   pages; geometry checks and contact sheets do not replace it.

Keep reusable renderer capabilities in their library and analysis-specific
formulas in their analysis owner. Forking analyb is optional, not a prerequisite.
