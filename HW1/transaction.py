from __future__ import annotations
import yaml
from dataclasses import dataclass, field
from typing import Any
import importlib
import time

@dataclass
class ObjectConfig:
    target: str
    args: dict[str, Any]

@dataclass
class MethodCall:
    this: str
    name: str
    args: dict[str, Any]

@dataclass
class SingleTransaction:
    id: int
    objects: list[ObjectConfig]
    methodsCalls: list[MethodCall]

@dataclass
class TransactionConfig:
    transactions: list[SingleTransaction] = field(default_factory=list)

def _instantiate(cfg: ObjectConfig):
    module_name, class_name = cfg.target.rsplit(".",1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)(**cfg.args)

def load_config(path: str) -> TransactionConfig:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    transactions = []
    for t in raw.get("transactions", []):
        objects = [ObjectConfig(**o) for o in t["objects"]]
        calls = [MethodCall(**c) for c in t["methodsCalls"]]
        transactions.append(SingleTransaction(t["id"], objects, calls))
    return TransactionConfig(transactions)

def execute_transaction(t: SingleTransaction, originals: list) -> bool:
    """
    works on a working copy -> original are never touched - on success return new copy else discard them
    """
    try:
        working = list(originals)
        for calls in t.methodsCalls:
            obj = working[calls.this]
            method = getattr(obj, calls.name)
            # each call returns a new object -> and store it back the working list
            working[calls.this] = method(**calls.args)
        
        # if succeeded = true -> replace the original with new version
        originals[:] = working
        return True
    except Exception as e:
        print(f"Error during the transaction {t.id}: {e}")
        # originals is unchande
        return False

def execute_transactions(cfg: TransactionConfig):
    for t in cfg.transactions:
        instances = [_instantiate(o) for o in t.objects]

        print(f"\n--- Transaction {t.id} ---", flush=True)
        time.sleep(0.5)

        if execute_transaction(t, instances):
            print(f"Transaction {t.id} COMPLETE. Balances:", flush=True)
        else:
            print(f"Transaction {t.id} FAILED. Rollback executed. Balances:", flush=True)

        for obj in instances:
            time.sleep(0.3)
            print(f"  {obj}", flush=True)


