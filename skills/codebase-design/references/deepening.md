# Deepening

How to deepen a cluster of shallow modules safely, given what it depends on.
Uses the vocabulary of [codebase-design](../SKILL.md).

## Dependency categories

Classify each dependency of the cluster. The category decides how the deepened
module is tested across its seam.

1. **In-process.** Pure computation and in-memory state: histogram arithmetic,
   error propagation, binning, selection masks. Always deepenable: merge the
   modules and test through the new interface. No adapter.
2. **Local-substitutable.** Dependencies with a cheap local stand-in. ROOT or
   HDF5 files are the usual case: the test writes a small file to a temporary
   directory (`tmp_path`, `uproot` or `h5py`) and the loader reads it back. A
   cache directory or a scratch filesystem is the same. The seam stays
   internal; no port at the external interface.
3. **Remote but owned.** Your own services or hosts across a network: a Slurm
   cluster, an internal database, a shared-storage mount. Define a port at the
   seam. The module owns the logic; the transport is an injected adapter, a real
   one for production and an in-memory one for tests.
4. **True external.** Services you do not control: Rucio, PanDA, a web API. The
   module takes the dependency as an injected port and tests supply a mock
   adapter. Keep one check against the real service, run by hand, because a mock
   cannot show that the service still behaves as assumed
   ([prove it on the real artifact](../../principle-prove-it-on-the-real-artifact/SKILL.md)).

## Seam discipline

- **One adapter is a hypothetical seam; two adapters make a real one.** Do not
  add a port unless two adapters are justified. A seam with one adapter is
  indirection.
- **Internal and external seams.** A deep module may have internal seams used by
  its own tests. Do not lift them into the interface because a test uses them.

## Testing: replace, do not layer

- Tests of the old shallow helpers become waste once tests at the deepened
  interface exist. Delete them, and write down why in the commit or decision
  record. Delete a helper test only after an interface-level test covers the
  same behavior.
- Write the new tests at the deepened interface, asserting observable results,
  not internal state. Take expected values from an independent source
  ([test behavior, not implementation](../../principle-test-behavior-not-implementation/SKILL.md)).
- Before the refactor, save outputs of the old code on a reference input. After
  it, the numbers must match exactly, except for bugs the change is meant to
  fix, which you list in advance. This is what lets a deletion of old tests be
  safe.
- A test that must change when the implementation changes is testing past the
  interface.
