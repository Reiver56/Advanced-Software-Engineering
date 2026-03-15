## Description
The goal of the homework is to implement an atomic transaction system over a set of objects. Each transaction consists of a sequence of operations that must all succeed, otherwise no changes are applied.
 
The `Account` class represents a bank account and is defined as an immutable object. This means that calling `withdraw` or `deposit` does not modify the account the method is called on, but returns a new object with the updated balance.
 
```python
a = Account(balance=500)  # 'a' is still Account(500)
b = a.withdraw(100)  # 'b' is a new Account(400)
                      
```
 
When a transaction is executed, all operations are applied on a copy of the original object list. If every operation succeeds, the original list is replaced with the updated one. If any operation fails, the copy is discarded and the originals remain unchanged.
 
### Dir Structure
 
```
HW1/
├── account.py       # Account class definition
├── transaction.py   # Transaction execution logic
├── main.py          # Entry point
└── base.yaml        # Transaction configuration file
```
 
### Configuration format (YAML)
 
```yaml
transactions:
  - id: 1
    objects:
      - target: "account.Account"
        args: {balance: 500}
      - target: "account.Account"
        args: {balance: 300}
    methodsCalls:
      - this: 0        # index into the objects list
        name: withdraw
        args: {amount: 100}
      - this: 1
        name: deposit
        args: {amount: 100}
```
 
### How to run
 
```bash
pip install pyyaml
python main.py ./base.yaml
```
 
### Expected output
 
```
Transaction 1 COMPLETE. Balances:
  balance: 400
  balance: 400
Error during the transaction 2: insufficient funds: need 200, have 50
Transaction 2 FAILED. Rollback executed. Balances:
  balance: 50
  balance: 200
```