# Homework 2 — Composite State Flattening

## Assignment

With reference to the state machine presented on slide 39:

1. flatten the composite `Preparing` state;
2. propose an equivalent version using fork and join pseudostates.

The original state machine models the preparation of a transaction. After the
`prepare` event, two activities run concurrently:

- `PreparingWth`, checked by `wthTest`;
- `PreparingDep`, checked by `depTest`.

The transaction is committed only when both activities succeed. If either one
fails, the transaction is rolled back.

## Part 1 — Flattened state machine

The parallel composite state is replaced with ordinary states representing all
possible combinations of the two regions. Each region can be either preparing
or prepared, so the Cartesian product produces four combined states.

| State | Withholding region | Deposit region |
| --- | --- | --- |
| `PreparingWth ∧ PreparingDep` | Preparing | Preparing |
| `WthPrepared ∧ PreparingDep` | Prepared | Preparing |
| `PreparingWth ∧ DepPrepared` | Preparing | Prepared |
| `WthPrepared ∧ DepPrepared` | Prepared | Prepared |

Both success orders are preserved: the withholding preparation may complete
before the deposit preparation, or the deposit preparation may complete first.
When both components are prepared, the machine enters `Committed`. Any failure
leads to `RolledBack`.

![Flattened transfer state machine](diagrams/transfer_flattened.png)

The editable source is available in
[`diagrams/transfer_flattened.drawio`](diagrams/transfer_flattened.drawio).

## Part 2 — Fork and join version

The second diagram expresses the same concurrency explicitly:

- a **fork** starts `PreparingWth` and `PreparingDep` in parallel;
- each branch performs its own test;
- successful branches reach a **join**;
- the join is crossed only after both branches have succeeded;
- a failure in either branch bypasses the join and leads to `RolledBack`.

![Fork and join transfer state machine](diagrams/transfer_fork_join.png)

The editable source is available in
[`diagrams/transfer_fork_join.drawio`](diagrams/transfer_fork_join.drawio).

## Behavioural equivalence

The two proposed diagrams describe the same relevant behaviour:

- `Committed` is reachable only after both preparation tasks succeed;
- the order of the two successful tests is not fixed;
- one failed preparation is sufficient to trigger rollback;
- successful and failed executions terminate through different final paths.

The flattened version makes every concurrent configuration explicit, while the
fork/join version represents parallelism directly and is more compact.

## Files

```text
Homework2/
├── README.md
└── diagrams/
    ├── transfer_flattened.drawio
    ├── transfer_flattened.png
    ├── transfer_fork_join.drawio
    └── transfer_fork_join.png
```

The `.drawio` files can be opened and edited with
[diagrams.net](https://app.diagrams.net/).

