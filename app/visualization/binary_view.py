# -*- coding: utf-8 -*-
"""
app/visualization/binary_view.py

Текстовая визуализация побитового XOR двух байтовых строк - используется
в шаге AddRoundKey, чтобы наглядно показать XOR каждого бита:

Block:     01010011 ...
RoundKey:  11000010 ...
XOR:       10010001 ...
"""
from __future__ import annotations


def format_xor_visualization(a: bytes, b: bytes, max_bytes: int = 16) -> str:
    a = a[:max_bytes]
    b = b[:max_bytes]
    result = bytes(x ^ y for x, y in zip(a, b))

    lines = []
    a_bits = " ".join(f"{x:08b}" for x in a)
    b_bits = " ".join(f"{x:08b}" for x in b)
    r_bits = " ".join(f"{x:08b}" for x in result)

    lines.append(f"Block:      {a_bits}")
    lines.append(f"Round Key:  {b_bits}")
    lines.append(f"{'-' * max(len(a_bits), 12)}")
    lines.append(f"XOR:        {r_bits}")
    return "\n".join(lines)


def format_hex_triplet(a: bytes, b: bytes, result: bytes) -> str:
    return (f"Block:      {a.hex().upper()}\n"
            f"Round Key:  {b.hex().upper()}\n"
            f"XOR result: {result.hex().upper()}")
