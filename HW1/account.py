from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True) # immutable

class Account():
    """
    define a immutable object -> every operation returns a new account instead of mutating self.
    the original is never changed.
    """

    balance: int

    def withdraw(self, amount: int) -> bool:
        if not isinstance(amount,int) or amount <= 0:
            raise ValueError(f"invalid amount: {amount}")
        if self.balance < amount:
            raise ValueError(f"insufficient funds: need {amount}, have {self.balance}")
        return Account(self.balance - amount)

    def deposit(self, amount: int) -> Account:
        if not isinstance(amount, int) or amount <= 0:
            raise ValueError(f"Invalid amount: {amount}")
        return Account(self.balance + amount)            
    
    def __str__(self):
        return f"balance: {self.balance}"
    