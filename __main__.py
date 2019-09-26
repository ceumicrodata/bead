import sys
assert sys.version_info >= (3, 6), "Python version 3.6 or newer is required"

if __name__ == "__main__":
    import bead_cli.main
    bead_cli.main.main()
