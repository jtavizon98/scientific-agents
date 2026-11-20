---
name: principle-test-behavior-not-implementation
description: Apply when you write, change or keep a test. Assert what the code's users can observe, so the test fails when that behavior breaks and keeps passing when only the internals change.
license: MIT; complete terms in LICENSE.txt
metadata:
  source: https://github.com/cursor/plugins/blob/aaeb0ea/pstack/skills/principle-test-behavior-not-implementation/SKILL.md
  adapted-for: scientific work
---

# Test behavior, not implementation

A test is a claim about what users of the code can observe through its interface: return values, errors, state they can read back, files written. Private helpers, internal call order and intermediate arrays are implementation.

Judge each test against two imagined edits:

- **Break the behavior** (a wrong value, a dropped overflow bin, a doubled weight). If the test still passes, it proves nothing. The usual causes are a loose tolerance, an expected value computed by the code under test, and an assertion on data the test built itself.
- **Change the internals** and keep every observable result. If the test fails, it is pinned to the implementation.

Keep a test that catches the first edit and survives the second. Rewrite or delete the rest.

- **Drive the public interface** with a concrete input. Do not call the private helper the bug happened to live in.
- **Take the expected value from outside the code:** a hand-worked example small enough to check on paper, a published number, a conservation law, or a result from an independent implementation. A test that repeats the formula under test is a tautology and does not count ([Numerical evidence](../scientific-coding/references/implementation.md#numerical-evidence)).
- **Prefer invariants through the interface.** Rebinning keeps the total weight and the total squared weight; filling in two batches equals filling once; the ratio of a histogram to a rescaled copy of itself is that constant in every bin with a nonzero denominator. A property test over random inputs states what must hold without copying the algorithm.
- **Pair "this never happens" with a case where it does.** A test that no entries are lost needs a fill with entries in the flow bins.
- **Assert the error type** callers branch on, not its message.
- **A bug that review or a plot found, and no test did, gets a test at the interface that fails on the old code,** before the fix is accepted.

You skipped this when a test only mirrors the implementation, passes after you break the code, or fails after a refactor that changed no number.

Related: [codebase-design](../codebase-design/SKILL.md) (the interface is the test surface).
