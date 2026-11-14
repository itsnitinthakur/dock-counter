"""Shortcut kept for earlier instructions: counts paper rolls.

Same as: python item_counter.py --item roll --prompt "paper roll" ...
"""
import sys

from item_counter import main

if __name__ == "__main__":
    if "--item" not in sys.argv:
        sys.argv += ["--item", "roll"]
    main()
