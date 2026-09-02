# Homework 1 — Generic Transaction Engine

This project implements a generic, configuration-driven transaction engine in
Python.

A composite transaction is represented as an ordered sequence of primitive
operations. The engine prepares every operation before making any permanent
change. If all preparation steps succeed, the operations are committed. If one
step fails, all previously prepared operations are rolled back in reverse
order.

## Main objective

The transaction engine is independent of the banking example used to
demonstrate it.

Transaction structures and argument mappings are defined in external files, so
the engine does not contain hardcoded transfer logic.

## Example configuration

`descriptions.txt` defines the primitive operations:

```text
transfer ["deposit", "withdraw"]
```

`data.txt` maps transaction arguments to each operation:

```text
transfer [0, 1] [0, 2]
```

Given:

```python
engine.execute(
    "transfer",
    [amount, destination_account, source_account],
)
```

the configuration produces:

```text
deposit(amount, destination_account)
withdraw(amount, source_account)
```

## Transaction protocol

The engine uses three phases:

1. **Prepare** — validate the operation and reserve the required resources.
2. **Commit** — permanently apply all prepared operations.
3. **Rollback** — cancel prepared operations if one step fails.

This guarantees that a composite transaction either completes entirely or
leaves the accounts unchanged.

## Project structure

```text
Homework1_Matteo_Carrese/
├── account.py
├── operation.py
├── operations.py
├── transaction_config.py
├── transaction_engine.py
├── main.py
├── descriptions.txt
├── data.txt
├── tests/
│   └── test_transaction_engine.py
└── README.md
```

## Design

### Account

`Account` stores:

- the confirmed balance;
- the amount temporarily reserved by prepared withdrawals;
- the balance still available for new operations.

Monetary values use Python's `Decimal` type to avoid floating-point rounding
errors.

### Operations

Every primitive operation follows the same contract:

```text
prepare
commit
rollback
```

Deposit and withdrawal operations implement this contract without exposing
banking rules to the transaction engine.

### Transaction engine

The engine:

1. loads a transaction definition;
2. extracts the required arguments using configured indexes;
3. resolves operations through a registry;
4. prepares the operations in configuration order;
5. commits all operations after complete preparation;
6. rolls prepared operations back in reverse order after a failure.

## Expected scenarios

The demonstration includes:

- a successful transfer that updates both accounts;
- a failed transfer caused by insufficient funds;
- verification that failed transactions leave all balances unchanged.

## Requirements

- Python 3.10 or newer;
- pytest for the automated tests.

Install the test dependency:

```bash
python -m pip install pytest
```

## Run

From the homework directory:

```bash
python main.py
```

Run the test suite with:

```bash
python -m pytest -v
```