---
name: codebase-design
description: Shared vocabulary for designing deep modules in scientific code. Use when designing or restructuring a module's interface, when one rule (a tolerance, a formula, a binning or normalization convention) is implemented in several places, when deciding where a seam goes, or when code is hard to test through its public interface.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/mattpocock/skills/blob/abeeaf9/skills/engineering/codebase-design/SKILL.md
  adapted-for: scientific libraries and analysis code
---

# Codebase design

Design **deep modules**: much behavior behind a small interface, placed at a
clean seam, testable through that interface. Callers get leverage, maintainers
get locality, and tests have one place to cross.

This skill gives the vocabulary and the questions. What a formula, selection or
normalization means stays with its scientific owner
([scientific-coding](../scientific-coding/SKILL.md)).

## Glossary

Use these terms exactly. Do not swap in "component", "service", "API" or
"boundary".

- **Module**: anything with an interface and an implementation, at any scale: a
  function, a class, a file, a package.
- **Interface**: everything a caller must know to use the module correctly. The
  signature, but also invariants, ordering constraints, error modes, required
  configuration, units, and cost. A histogram `ratio` that silently needs
  matching bin edges has that requirement in its interface whether or not the
  signature says so.
- **Implementation**: what is inside. Say **adapter** when the seam is the topic
  and **implementation** otherwise.
- **Depth**: behavior a caller or test can exercise per unit of interface they
  must learn. **Deep**: a lot behind a small interface. **Shallow**: an
  interface nearly as complex as the implementation.
- **Seam** (Michael Feathers): the place where behavior can change without
  editing there; the location where a module's interface lives.
- **Adapter**: a concrete thing that satisfies an interface at a seam, named by
  the role it fills (a file reader, an in-memory fake).
- **Leverage**: what callers get from depth. One implementation pays back across
  every call site and every test.
- **Locality**: what maintainers get from depth. A change, a bug, a convention
  and its verification sit in one place. Fix once, fixed everywhere.

## Deep and shallow, with an example

Shallow: three public helpers, `edges_match(a, b, tol)`, `safe_divide(n, d)`,
`propagate_error(n, d)`. Every caller chains them and chooses its own `tol`, so
four callers carry four tolerances and one of them is eventually wrong.

Deep: one `ratio(num, den) -> Ratio(value, error, valid)`. It owns the
grid-compatibility rule, the zero-denominator policy and the error propagation.
The caller learns one call and one result type; the rule exists once.

When designing an interface, ask whether you can drop entry points, simplify
parameters, or move more decisions inside.

## Principles

- **Depth is a property of the interface.** A deep module may be built from
  small parts; they are not part of its interface. Internal seams are private
  to the module and its own tests.
- **The deletion test.** Imagine deleting the module. If the complexity
  disappears, it was a pass-through. If it reappears in every caller, the module
  was earning its keep.
- **Locality is the rule "one implementation owner" applied to shape.**
  [scientific-coding](../scientific-coding/SKILL.md) says to give each formula,
  selection, weight, normalization, binning and response convention one
  implementation owner. A module is where that owner lives. Several copies of a
  rule that drift apart (an edge tolerance, a rebinning path, how squared
  weights are read) mean the rule has no module yet. Do not restate the rule
  here; find the owner it names, or create one.
- **The interface is the test surface.** Callers and tests cross the same seam.
  If you must test past the interface, the module is the wrong shape. See
  [test behavior, not implementation](../principle-test-behavior-not-implementation/SKILL.md).
- **One adapter is a hypothetical seam; two adapters make a real one.** Add a
  seam only when something varies across it, typically production and a test
  stand-in.
- **Fail where the rule is, not downstream.** A module that owns a rule also
  owns the loud error for violating it, so callers cannot silently lose entries.

## Designing for testability

1. **Accept dependencies, do not create them.** A function that takes a reader
   or an open file can be tested with a temporary file; one that builds its own
   path to a remote store cannot.
2. **Return results, do not mutate.** `rebinned = rebin(h, edges)` is testable;
   `h.rebin_inplace(edges)` forces the test to inspect hidden state.
3. **Keep the surface small.** Fewer entry points and parameters mean fewer
   tests and simpler setup.

## Relationships

- A module has one interface; depth is measured against it.
- A seam is where the interface lives; an adapter sits at a seam.
- Depth produces leverage for callers and locality for maintainers.

## Rejected framings

- **Depth as the ratio of implementation lines to interface lines.** It rewards
  padding. Depth here is leverage.
- **"Interface" as the language keyword or a class's public methods.** Too
  narrow: it leaves out invariants and error modes.
- **"Boundary".** Overloaded; say seam or interface.

## Going deeper

- [Deepening a cluster](references/deepening.md): dependency categories, seam
  discipline and replacing tests rather than layering them.
- [Design it twice](references/design-it-twice.md): parallel fresh-context
  designs of one interface, compared on depth, locality and seam placement.
- Looking for candidates across a codebase: [architecture-review](../architecture-review/SKILL.md).
