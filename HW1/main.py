import sys
from transaction import load_config, execute_transactions

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "./HW1/base.yaml"
    cfg = load_config(path)
    execute_transactions(cfg)

if __name__ == "__main__":
    main()