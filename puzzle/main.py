#!/usr/bin/env python3
"""Block Clash — Puzzle Versus (mirip Tetris) dengan pilihan tokoh & ending berbeda.

Jalankan dengan:
    pip install -r requirements.txt
    python main.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
