# -*- coding: utf-8 -*-
"""Educational MD5/SHA-256 tracing helpers.

The final digest is verified with hashlib. The trace exposes fixed IVs,
message padding, 512-bit blocks, message words and compression rounds.
"""
from __future__ import annotations

import hashlib
import math
import struct
from typing import Dict, List

MASK32 = 0xFFFFFFFF

SHA256_IV = [
    0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A,
    0x510E527F, 0x9B05688C, 0x1F83D9AB, 0x5BE0CD19,
]
SHA256_K = [
    0x428A2F98,0x71374491,0xB5C0FBCF,0xE9B5DBA5,0x3956C25B,0x59F111F1,0x923F82A4,0xAB1C5ED5,
    0xD807AA98,0x12835B01,0x243185BE,0x550C7DC3,0x72BE5D74,0x80DEB1FE,0x9BDC06A7,0xC19BF174,
    0xE49B69C1,0xEFBE4786,0x0FC19DC6,0x240CA1CC,0x2DE92C6F,0x4A7484AA,0x5CB0A9DC,0x76F988DA,
    0x983E5152,0xA831C66D,0xB00327C8,0xBF597FC7,0xC6E00BF3,0xD5A79147,0x06CA6351,0x14292967,
    0x27B70A85,0x2E1B2138,0x4D2C6DFC,0x53380D13,0x650A7354,0x766A0ABB,0x81C2C92E,0x92722C85,
    0xA2BFE8A1,0xA81A664B,0xC24B8B70,0xC76C51A3,0xD192E819,0xD6990624,0xF40E3585,0x106AA070,
    0x19A4C116,0x1E376C08,0x2748774C,0x34B0BCB5,0x391C0CB3,0x4ED8AA4A,0x5B9CCA4F,0x682E6FF3,
    0x748F82EE,0x78A5636F,0x84C87814,0x8CC70208,0x90BEFFFA,0xA4506CEB,0xBEF9A3F7,0xC67178F2,
]

MD5_IV = [0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476]
MD5_S = [
    7,12,17,22, 7,12,17,22, 7,12,17,22, 7,12,17,22,
    5,9,14,20, 5,9,14,20, 5,9,14,20, 5,9,14,20,
    4,11,16,23, 4,11,16,23, 4,11,16,23, 4,11,16,23,
    6,10,15,21, 6,10,15,21, 6,10,15,21, 6,10,15,21,
]
MD5_K = [int(abs(math.sin(i + 1)) * (2**32)) & MASK32 for i in range(64)]


def _rotr(x: int, n: int) -> int:
    return ((x >> n) | (x << (32 - n))) & MASK32


def _rotl(x: int, n: int) -> int:
    return ((x << n) | (x >> (32 - n))) & MASK32


def _bits(data: bytes) -> str:
    return ''.join(f'{b:08b}' for b in data)


def pad_message(data: bytes, algorithm: str) -> bytes:
    original_bits = len(data) * 8
    out = bytearray(data)
    out.append(0x80)
    while len(out) % 64 != 56:
        out.append(0)
    if algorithm == 'md5':
        out.extend(struct.pack('<Q', original_bits))
    else:
        out.extend(struct.pack('>Q', original_bits))
    return bytes(out)


def _sha256_trace(data: bytes) -> Dict:
    padded = pad_message(data, 'sha256')
    h = list(SHA256_IV)
    blocks = []
    for block_index in range(0, len(padded), 64):
        block = padded[block_index:block_index+64]
        w = list(struct.unpack('>16I', block)) + [0] * 48
        for t in range(16, 64):
            s0 = _rotr(w[t-15], 7) ^ _rotr(w[t-15], 18) ^ (w[t-15] >> 3)
            s1 = _rotr(w[t-2], 17) ^ _rotr(w[t-2], 19) ^ (w[t-2] >> 10)
            w[t] = (w[t-16] + s0 + w[t-7] + s1) & MASK32
        before = list(h)
        a,b,c,d,e,f,g,hh = h
        rounds = []
        for t in range(64):
            S1 = _rotr(e,6) ^ _rotr(e,11) ^ _rotr(e,25)
            ch = (e & f) ^ ((~e) & g)
            temp1 = (hh + S1 + ch + SHA256_K[t] + w[t]) & MASK32
            S0 = _rotr(a,2) ^ _rotr(a,13) ^ _rotr(a,22)
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & MASK32
            rounds.append({
                'round': t, 'word': w[t], 'k': SHA256_K[t],
                'a': a,'b': b,'c': c,'d': d,'e': e,'f': f,'g': g,'h': hh,
                'ch': ch & MASK32, 'maj': maj & MASK32,
                'sigma0': S0, 'sigma1': S1, 'temp1': temp1, 'temp2': temp2,
            })
            hh,g,f,e,d,c,b,a = g,f,e,(d+temp1)&MASK32,c,b,a,(temp1+temp2)&MASK32
        h = [(x+y)&MASK32 for x,y in zip(h,[a,b,c,d,e,f,g,hh])]
        blocks.append({'index': block_index//64, 'bytes': block, 'words': w, 'state_in': before, 'state_out': list(h), 'rounds': rounds})
    digest = ''.join(f'{x:08x}' for x in h)
    return {'algorithm':'sha256','iv':SHA256_IV,'padded':padded,'blocks':blocks,'digest':digest}


def _md5_trace(data: bytes) -> Dict:
    padded = pad_message(data, 'md5')
    h = list(MD5_IV)
    blocks = []
    for block_index in range(0, len(padded), 64):
        block = padded[block_index:block_index+64]
        m = list(struct.unpack('<16I', block))
        before = list(h)
        a,b,c,d = h
        rounds = []
        for i in range(64):
            if i < 16:
                f = (b & c) | ((~b) & d); g = i; fname = 'F'
            elif i < 32:
                f = (d & b) | ((~d) & c); g = (5*i + 1) % 16; fname = 'G'
            elif i < 48:
                f = b ^ c ^ d; g = (3*i + 5) % 16; fname = 'H'
            else:
                f = c ^ (b | (~d)); g = (7*i) % 16; fname = 'I'
            f &= MASK32
            total = (a + f + MD5_K[i] + m[g]) & MASK32
            rotated = _rotl(total, MD5_S[i])
            new_b = (b + rotated) & MASK32
            rounds.append({
                'round': i, 'word_index': g, 'word': m[g], 'k': MD5_K[i], 'shift': MD5_S[i],
                'a':a,'b':b,'c':c,'d':d,'func':fname,'func_value':f,
                'sum':total,'rotated':rotated,'new_b':new_b,
            })
            a,d,c,b = d,c,b,new_b
        h = [(x+y)&MASK32 for x,y in zip(h,[a,b,c,d])]
        blocks.append({'index':block_index//64,'bytes':block,'words':m,'state_in':before,'state_out':list(h),'rounds':rounds})
    digest = struct.pack('<4I', *h).hex()
    return {'algorithm':'md5','iv':MD5_IV,'padded':padded,'blocks':blocks,'digest':digest}


def trace_hash(text: str, algorithm: str) -> Dict:
    data = text.encode('utf-8')
    algorithm = algorithm.lower()
    if algorithm not in ('md5', 'sha256'):
        raise ValueError('Unsupported hash algorithm')
    result = _md5_trace(data) if algorithm == 'md5' else _sha256_trace(data)
    expected = hashlib.md5(data).hexdigest() if algorithm == 'md5' else hashlib.sha256(data).hexdigest()
    if result['digest'] != expected:
        raise AssertionError(f'{algorithm} trace mismatch: {result["digest"]} != {expected}')
    result.update({
        'text': text,
        'input_bytes': data,
        'input_bits': _bits(data),
        'padded_bits': _bits(result['padded']),
        'expected': expected,
    })
    return result
