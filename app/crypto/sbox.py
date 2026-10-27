# -*- coding: utf-8 -*-
"""Local, algorithmic AES-style S-box construction.

No table is downloaded and no network access is used.  The S-box is built
from the standard Rijndael construction: multiplicative inverse in GF(2^8)
followed by the affine transform.  Keeping it algorithmic makes the individual
row/column lookup easy to demonstrate in both AES and Feistel views.
"""
from __future__ import annotations
from typing import List


def gf_mul(a: int, b: int) -> int:
    a &= 0xFF
    b &= 0xFF
    out = 0
    for _ in range(8):
        if b & 1:
            out ^= a
        high = a & 0x80
        a = (a << 1) & 0xFF
        if high:
            a ^= 0x1B
        b >>= 1
    return out & 0xFF


def gf_pow(a: int, power: int) -> int:
    result = 1
    base = a & 0xFF
    while power:
        if power & 1:
            result = gf_mul(result, base)
        base = gf_mul(base, base)
        power >>= 1
    return result


def gf_inverse(a: int) -> int:
    # In GF(2^8), a^-1 = a^254 for non-zero a.
    return 0 if a == 0 else gf_pow(a, 254)


def _rotl8(value: int, shift: int) -> int:
    shift %= 8
    return ((value << shift) | (value >> (8 - shift))) & 0xFF


def generate_sbox() -> List[int]:
    """Generate the Rijndael/AES S-box algorithmically (256 values)."""
    result: List[int] = []
    for x in range(256):
        inv = gf_inverse(x)
        y = inv ^ _rotl8(inv, 1) ^ _rotl8(inv, 2) ^ _rotl8(inv, 3) ^ _rotl8(inv, 4) ^ 0x63
        result.append(y & 0xFF)
    return result


def substitute_bytes(bit_string: str, sbox: List[int] | None = None):
    """Substitute every 8-bit chunk, returning output bits and lookup details."""
    if sbox is None:
        sbox = generate_sbox()
    if len(bit_string) % 8:
        raise ValueError("S-box input length must be a multiple of 8 bits")
    outputs = []
    details = []
    for offset in range(0, len(bit_string), 8):
        chunk = bit_string[offset:offset + 8]
        value = int(chunk, 2)
        row, col = value >> 4, value & 0x0F
        substituted = sbox[value]
        out_bits = f"{substituted:08b}"
        outputs.append(out_bits)
        details.append({
            "index": offset // 8,
            "input_bits": chunk,
            "input_hex": f"{value:02X}",
            "row": row,
            "column": col,
            "value": substituted,
            "value_hex": f"{substituted:02X}",
            "output_bits": out_bits,
        })
    return "".join(outputs), details
