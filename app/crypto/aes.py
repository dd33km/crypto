# -*- coding: utf-8 -*-
"""
app/crypto/aes.py

Реализация СТАНДАРТНОГО блочного шифра AES (Rijndael, FIPS-197) со строгим
соблюдением спецификации:
  - размер блока ровно 128 бит (16 байт) - это фиксированное требование
    стандарта AES и не может быть изменено в этом модуле;
  - размер ключа 128 / 192 / 256 бит;
  - число раундов 10 / 12 / 14 соответственно;
  - в последнем раунде MixColumns не выполняется (особенность AES).

Модуль возвращает не только результат, но и полный протокол (trace) каждого
шага каждого раунда - именно это использует GUI для пошаговой визуализации.

AES является открытым, общедоступным государственным стандартом
шифрования (NIST FIPS-197), его реализация в учебных целях - стандартная
практика в курсах криптографии по всему миру.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple
from .aes_sbox import AES_SBOX, AES_INV_SBOX, gf_mul, build_inverse_sbox
from .aes_key_expansion import key_expansion

BLOCK_SIZE_BYTES = 16  # 128 бит - фиксировано стандартом AES

NK_BY_KEYBITS = {128: 4, 192: 6, 256: 8}
NR_BY_KEYBITS = {128: 10, 192: 12, 256: 14}


# ---------------------------------------------------------------------------
# Представление состояния (state) - матрица 4x4 байта, столбцовый порядок,
# как определено в FIPS-197 §3.4.
# ---------------------------------------------------------------------------
def bytes_to_state(data: bytes) -> List[List[int]]:
    assert len(data) == 16
    state = [[0] * 4 for _ in range(4)]
    for i in range(16):
        state[i % 4][i // 4] = data[i]
    return state


def state_to_bytes(state: List[List[int]]) -> bytes:
    out = bytearray(16)
    for i in range(16):
        out[i] = state[i % 4][i // 4]
    return bytes(out)


def state_copy(state: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in state]


# ---------------------------------------------------------------------------
# Базовые преобразования AES
# ---------------------------------------------------------------------------
def sub_bytes(state, sbox=AES_SBOX):
    return [[sbox[b] for b in row] for row in state]


def inv_sub_bytes(state, inv_sbox=AES_INV_SBOX):
    return [[inv_sbox[b] for b in row] for row in state]


def shift_rows(state):
    new_state = state_copy(state)
    for r in range(1, 4):
        new_state[r] = state[r][r:] + state[r][:r]
    return new_state


def inv_shift_rows(state):
    new_state = state_copy(state)
    for r in range(1, 4):
        new_state[r] = state[r][-r:] + state[r][:-r]
    return new_state


def _mix_single_column(col: List[int]) -> List[int]:
    a0, a1, a2, a3 = col
    return [
        gf_mul(a0, 2) ^ gf_mul(a1, 3) ^ a2 ^ a3,
        a0 ^ gf_mul(a1, 2) ^ gf_mul(a2, 3) ^ a3,
        a0 ^ a1 ^ gf_mul(a2, 2) ^ gf_mul(a3, 3),
        gf_mul(a0, 3) ^ a1 ^ a2 ^ gf_mul(a3, 2),
    ]


def _inv_mix_single_column(col: List[int]) -> List[int]:
    a0, a1, a2, a3 = col
    return [
        gf_mul(a0, 0x0e) ^ gf_mul(a1, 0x0b) ^ gf_mul(a2, 0x0d) ^ gf_mul(a3, 0x09),
        gf_mul(a0, 0x09) ^ gf_mul(a1, 0x0e) ^ gf_mul(a2, 0x0b) ^ gf_mul(a3, 0x0d),
        gf_mul(a0, 0x0d) ^ gf_mul(a1, 0x09) ^ gf_mul(a2, 0x0e) ^ gf_mul(a3, 0x0b),
        gf_mul(a0, 0x0b) ^ gf_mul(a1, 0x0d) ^ gf_mul(a2, 0x09) ^ gf_mul(a3, 0x0e),
    ]


def mix_columns(state):
    new_state = [[0] * 4 for _ in range(4)]
    for c in range(4):
        col = [state[r][c] for r in range(4)]
        mixed = _mix_single_column(col)
        for r in range(4):
            new_state[r][c] = mixed[r]
    return new_state


def inv_mix_columns(state):
    new_state = [[0] * 4 for _ in range(4)]
    for c in range(4):
        col = [state[r][c] for r in range(4)]
        mixed = _inv_mix_single_column(col)
        for r in range(4):
            new_state[r][c] = mixed[r]
    return new_state


def add_round_key(state, round_key: bytes):
    rk_state = bytes_to_state(round_key)
    return [[state[r][c] ^ rk_state[r][c] for c in range(4)] for r in range(4)]


# ---------------------------------------------------------------------------
# Шифрование / дешифрование одного 128-битного блока, с полным протоколом
# ---------------------------------------------------------------------------
def encrypt_block(plaintext_block: bytes, round_keys: List[bytes], nr: int,
                   sbox: List[int] = AES_SBOX) -> Tuple[bytes, List[Dict[str, Any]]]:
    assert len(plaintext_block) == 16
    trace: List[Dict[str, Any]] = []

    state = bytes_to_state(plaintext_block)
    trace.append({"round": 0, "stage": "InitialState", "state": state_copy(state)})

    state = add_round_key(state, round_keys[0])
    trace.append({"round": 0, "stage": "AddRoundKey", "state": state_copy(state),
                   "round_key": round_keys[0]})

    for rnd in range(1, nr):
        state = sub_bytes(state, sbox)
        trace.append({"round": rnd, "stage": "SubBytes", "state": state_copy(state)})

        state = shift_rows(state)
        trace.append({"round": rnd, "stage": "ShiftRows", "state": state_copy(state)})

        state = mix_columns(state)
        trace.append({"round": rnd, "stage": "MixColumns", "state": state_copy(state)})

        state = add_round_key(state, round_keys[rnd])
        trace.append({"round": rnd, "stage": "AddRoundKey", "state": state_copy(state),
                       "round_key": round_keys[rnd]})

    # Финальный раунд: SubBytes -> ShiftRows -> AddRoundKey (БЕЗ MixColumns)
    state = sub_bytes(state, sbox)
    trace.append({"round": nr, "stage": "SubBytes", "state": state_copy(state)})

    state = shift_rows(state)
    trace.append({"round": nr, "stage": "ShiftRows", "state": state_copy(state),
                   "note": "В последнем раунде MixColumns НЕ выполняется (особенность AES)"})

    state = add_round_key(state, round_keys[nr])
    trace.append({"round": nr, "stage": "AddRoundKey", "state": state_copy(state),
                   "round_key": round_keys[nr]})

    ciphertext = state_to_bytes(state)
    trace.append({"round": nr, "stage": "Ciphertext", "state": state_copy(state)})
    return ciphertext, trace


def decrypt_block(ciphertext_block: bytes, round_keys: List[bytes], nr: int,
                   inv_sbox: List[int] = AES_INV_SBOX) -> Tuple[bytes, List[Dict[str, Any]]]:
    assert len(ciphertext_block) == 16
    trace: List[Dict[str, Any]] = []

    state = bytes_to_state(ciphertext_block)
    trace.append({"round": nr, "stage": "InitialState(Ciphertext)", "state": state_copy(state)})

    state = add_round_key(state, round_keys[nr])
    trace.append({"round": nr, "stage": "InvAddRoundKey", "state": state_copy(state),
                   "round_key": round_keys[nr]})

    for rnd in range(nr - 1, 0, -1):
        state = inv_shift_rows(state)
        trace.append({"round": rnd, "stage": "InvShiftRows", "state": state_copy(state)})

        state = inv_sub_bytes(state, inv_sbox)
        trace.append({"round": rnd, "stage": "InvSubBytes", "state": state_copy(state)})

        state = add_round_key(state, round_keys[rnd])
        trace.append({"round": rnd, "stage": "InvAddRoundKey", "state": state_copy(state),
                       "round_key": round_keys[rnd]})

        state = inv_mix_columns(state)
        trace.append({"round": rnd, "stage": "InvMixColumns", "state": state_copy(state)})

    state = inv_shift_rows(state)
    trace.append({"round": 0, "stage": "InvShiftRows", "state": state_copy(state)})

    state = inv_sub_bytes(state, inv_sbox)
    trace.append({"round": 0, "stage": "InvSubBytes", "state": state_copy(state)})

    state = add_round_key(state, round_keys[0])
    trace.append({"round": 0, "stage": "InvAddRoundKey", "state": state_copy(state),
                   "round_key": round_keys[0]})

    plaintext = state_to_bytes(state)
    trace.append({"round": 0, "stage": "PlaintextBlock", "state": state_copy(state)})
    return plaintext, trace


# ---------------------------------------------------------------------------
# Высокоуровневый класс AESCipher: работает с многоблочными сообщениями,
# использует padding.py, поддерживает ECB и CBC.
# ---------------------------------------------------------------------------
class AESCipher:
    """
    Стандартный AES-128/192/256 (строго 128-битный блок).
    keybits должен быть одним из {128, 192, 256}.
    """

    def __init__(self, key: bytes, keybits: int, sbox: List[int] = None):
        if keybits not in NK_BY_KEYBITS:
            raise ValueError("keybits должен быть 128, 192 или 256 для стандартного AES")
        if len(key) * 8 != keybits:
            raise ValueError(f"Ключ должен быть {keybits} бит, получено {len(key) * 8} бит")

        self.keybits = keybits
        self.nk = NK_BY_KEYBITS[keybits]
        self.nr = NR_BY_KEYBITS[keybits]
        self.sbox = sbox if sbox is not None else AES_SBOX
        self.inv_sbox = build_inverse_sbox(self.sbox)

        self.key_schedule = key_expansion(key, self.nk, self.nr, sbox=self.sbox)
        self.round_keys = self.key_schedule["round_keys"]

    def encrypt_blocks(self, blocks: List[bytes], mode: str = "ECB",
                        iv: bytes = None) -> Tuple[List[bytes], List[List[Dict[str, Any]]]]:
        ciphertext_blocks = []
        traces = []
        prev = iv if (mode == "CBC" and iv is not None) else None
        for block in blocks:
            if mode == "CBC" and prev is not None:
                block = bytes(a ^ b for a, b in zip(block, prev))
            ct, trace = encrypt_block(block, self.round_keys, self.nr, self.sbox)
            ciphertext_blocks.append(ct)
            traces.append(trace)
            if mode == "CBC":
                prev = ct
        return ciphertext_blocks, traces

    def decrypt_blocks(self, blocks: List[bytes], mode: str = "ECB",
                        iv: bytes = None) -> Tuple[List[bytes], List[List[Dict[str, Any]]]]:
        plaintext_blocks = []
        traces = []
        prev = iv if (mode == "CBC" and iv is not None) else None
        for block in blocks:
            pt, trace = decrypt_block(block, self.round_keys, self.nr, self.inv_sbox)
            if mode == "CBC" and prev is not None:
                pt = bytes(a ^ b for a, b in zip(pt, prev))
            plaintext_blocks.append(pt)
            traces.append(trace)
            if mode == "CBC":
                prev = block
        return plaintext_blocks, traces
