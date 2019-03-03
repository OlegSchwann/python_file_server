#!/usr/bin/env python3
import sys

from src import main

if __name__ == "__main__":
    is_debug = (False if "--release" in sys.argv else (True if "--debug" in sys.argv else None))
    main.main(is_debug)
