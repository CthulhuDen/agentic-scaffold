# Testing

These rules apply to all tests in this repository. Mocks are defined at the consumption site as small interfaces with
the minimum surface a test exercises; remote services the code calls are stubbed through this pattern.

## Coverage bar

Spec coverage is not a target: the spec documents behaviour, tests insure it, and these are different jobs. A spec'd
behaviour deserves a dedicated test only when its plausible regression would be silent and costly — unintended external
writes, data or audit loss, security gaps, or user-facing breakage with no loud failure. Behaviour whose breakage is
loud (compile failure, immediate crash, obvious in any manual run) or low-cost (a missing log line) may go untested even
though the spec describes it.

## Brittleness limits

Every test must justify itself by the production defect it uniquely catches: if every defect a test would catch is
already caught by another test, merge it into that test or delete it. Specifically:

| Rule                      | Statement                                                                                                                                                                                  |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| One canonical render test | Exact user-facing wording (messages, banners, formatted output) is asserted in at most one test per message; every other test asserts the message key or a short discriminating substring. |
| One canonical struct test | The full field set of an event, payload, or struct mapping is asserted in at most one test per type; every other test asserts only the fields that distinguish its scenario.               |
| Table-drive same-branch   | Scenarios that exercise the same production branch with varied inputs are rows in one table-driven test, not separate functions.                                                           |
| No dependency re-testing  | A package's tests do not re-assert behaviour owned and tested by a dependency; they assert only the integration contract (the dependency was invoked with the right inputs).               |
| No trivial-plumbing tests | Pass-through delegation, getters, and constant wiring get no dedicated test; they are covered incidentally by behavioural tests.                                                           |
| One flow test per flow    | Tests that run the same production flow to assert different side effects merge into one canonical flow test carrying all the assertions, instead of each re-running the fixture.           |
| One surface per mechanism | A mechanism living in code shared between surfaces is tested through one surface; mirror tests on the other surfaces cover only surface-specific behaviour.                                |
| Own layer, not per intake | Logic shared by several intake paths (a filter chain, a dispatcher) is tested once at the layer that owns it, not repeated from each intake's tests.                                       |

## Mutation check

Every behavioural test fails under at least one plausible regression of the specific behaviour its name claims: removing
or inverting that behaviour, usually in one to a few lines. Failing only when the whole code path is deleted does not
count; such a test does not meet the [coverage bar](#coverage-bar).

## Producer → consumer contracts

When a change alters the data format or contract one function produces for another package to consume — library swap,
serialization change, parsed-shape adjustment — include a test that exercises producer → consumer in the same direction
production code does. Tests that hand-build the consumer's input from a synthetic literal bypass the boundary the change
touches and miss producer/consumer mismatches. When such a bug surfaces, pin the contract with a regression test that
runs the full chain.
