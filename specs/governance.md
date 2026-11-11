# Governance

The governance layer documents the rules every author of code, documentation, or change must follow. Rule
documents live under [`policy/`](../policy); [`policy/README.md`](../policy/README.md) indexes them.

## Application

Agents load the relevant policy file before performing the corresponding work.

| Policy file                                                                                                              | Load before                                                      |
| ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| [`code-quality.md`](../policy/code-quality.md)                                                                           | Writing or reviewing code                                        |
| [`testing.md`](../policy/testing.md)                                                                                     | Writing or reviewing tests                                       |
| [`doc-quality.md`](../policy/doc-quality.md), [`markdown.md`](../policy/markdown.md), [`charts.md`](../policy/charts.md) | Writing or reviewing documentation                               |
| [`verification-gates.md`](../policy/verification-gates.md)                                                               | Committing a code change, to determine which checks it must pass |

## Ownership

[`manifest.yaml`](../manifest.yaml) marks each `policy/` file as managed or stub (see [`sync.md`](sync.md#manifest)).

| Owner    | Files                                                                                                                                      | Sync                                                                                                                                                                       |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Scaffold | Every cross-project rule document under `policy/`: each file the manifest does not list as a stub                                          | Push overwrites it on every sync                                                                                                                                           |
| Client   | [`policy/README.md`](../policy/README.md), the index; the client may add policy documents the scaffold does not ship                       | Seeded once on first install, never overwritten                                                                                                                            |
| Client   | [`policy/verification-gates.md`](../policy/verification-gates.md), the verification commands and pass criteria for the client's tech stack | Seeded once from [`templates/verification-gates.md`](../templates/verification-gates.md), which lists the gates that hold in a freshly installed client; never overwritten |
