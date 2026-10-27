# -*- coding: utf-8 -*-
"""
app/crypto/experimental_cipher.py

"Учебный / экспериментальный блочный шифр" - НЕ является стандартом AES.

Позволяет пользователю свободно менять параметры, которые в настоящем AES
зафиксированы стандартом:
    - размер блока: 64 / 128 / 192 / 256 бит (кратно 32 битам)
    - размер ключа: 64 / 128 / 192 / 256 бит
    - число раундов: 10 / 12 / 14 / 16 (или другое)
    - S-box: пользовательский (сгенерированный в разделе "S-box")
    - линейное преобразование: ShiftRows+MixColumns (как в AES) ИЛИ
      альтернативы: XOR соседних байт, циклический сдвиг, перестановка
      битов, умножение матрицы по модулю 2.

Приложение обязано визуально и текстово подчёркивать, что это НЕ AES -
это делается на уровне GUI (метки "Experimental AES-like Cipher"), а также
здесь, в docstring и в возвращаемых структурах (поле "standard": False).

Ничего из этого не является реализацией существующего "опасного" алгоритма -
это учебная конструкция для демонстрации того, как параметры влияют на
блочный шифр, стандартная тема для курсов по криптографии.
"""
from __future__ import annotations
from typing import List, Dict, Any, Tuple
from .aes_sbox import AES_SBOX, build_inverse_sbox, gf_mul
from .aes_key_expansion import sub_word, rot_word, xor_words

LINEAR_TRANSFORMS = [
    "aes_like",        # ShiftRows + MixColumns (обобщённые на N столбцов)
    "xor_neighbors",   # XOR каждого байта с соседним (циклически)
    "cyclic_shift",    # циклический сдвиг всего блока на 1 байт
    "bit_permutation", # фиксированная (но обратимая) перестановка битов
]


# ---------------------------------------------------------------------------
# Обобщённое представление состояния: block_size_bytes байт, 4 строки x
# (block_size_bytes/4) столбцов - естественное обобщение AES-состояния на
# другие размеры блока (block_size_bytes должен быть кратен 4).
# ---------------------------------------------------------------------------
def bytes_to_gen_state(data: bytes, cols: int):
    state = [[0] * cols for _ in range(4)]
    for i in range(len(data)):
        state[i % 4][i // 4] = data[i]
    return state


def gen_state_to_bytes(state, cols: int) -> bytes:
    out = bytearray(4 * cols)
    for i in range(4 * cols):
        out[i] = state[i % 4][i // 4]
    return bytes(out)


def gen_shift_rows(state, cols: int):
    new_state = [row[:] for row in state]
    for r in range(1, 4):
        shift = r % cols if cols > 0 else 0
        new_state[r] = state[r][shift:] + state[r][:shift]
    return new_state


def gen_inv_shift_rows(state, cols: int):
    new_state = [row[:] for row in state]
    for r in range(1, 4):
        shift = r % cols if cols > 0 else 0
        new_state[r] = state[r][-shift:] + state[r][:-shift] if shift else state[r][:]
    return new_state


def _mix_col(col):
    a0, a1, a2, a3 = col
    return [
        gf_mul(a0, 2) ^ gf_mul(a1, 3) ^ a2 ^ a3,
        a0 ^ gf_mul(a1, 2) ^ gf_mul(a2, 3) ^ a3,
        a0 ^ a1 ^ gf_mul(a2, 2) ^ gf_mul(a3, 3),
        gf_mul(a0, 3) ^ a1 ^ a2 ^ gf_mul(a3, 2),
    ]


def _inv_mix_col(col):
    a0, a1, a2, a3 = col
    return [
        gf_mul(a0, 0x0e) ^ gf_mul(a1, 0x0b) ^ gf_mul(a2, 0x0d) ^ gf_mul(a3, 0x09),
        gf_mul(a0, 0x09) ^ gf_mul(a1, 0x0e) ^ gf_mul(a2, 0x0b) ^ gf_mul(a3, 0x0d),
        gf_mul(a0, 0x0d) ^ gf_mul(a1, 0x09) ^ gf_mul(a2, 0x0e) ^ gf_mul(a3, 0x0b),
        gf_mul(a0, 0x0b) ^ gf_mul(a1, 0x0d) ^ gf_mul(a2, 0x09) ^ gf_mul(a3, 0x0e),
    ]


def gen_mix_columns(state, cols: int):
    new_state = [[0] * cols for _ in range(4)]
    for c in range(cols):
        col = [state[r][c] for r in range(4)]
        mixed = _mix_col(col)
        for r in range(4):
            new_state[r][c] = mixed[r]
    return new_state


def gen_inv_mix_columns(state, cols: int):
    new_state = [[0] * cols for _ in range(4)]
    for c in range(cols):
        col = [state[r][c] for r in range(4)]
        mixed = _inv_mix_col(col)
        for r in range(4):
            new_state[r][c] = mixed[r]
    return new_state


def xor_neighbors_forward(data: bytes) -> bytes:
    n = len(data)
    out = bytearray(n)
    for i in range(n):
        out[i] = data[i] ^ data[(i + 1) % n]
    return bytes(out)


def xor_neighbors_inverse(data: bytes) -> bytes:
    # Обратная операция к xor_neighbors_forward: решается последовательно
    # с конца, так как out[i] = data[i] xor data[i+1 mod n].
    n = len(data)
    orig = bytearray(n)
    # data[n-1] = orig[n-1] xor orig[0]; неизвестна orig[0] напрямую без
    # доп. информации, поэтому для гарантированной обратимости используем
    # альтернативную, действительно обратимую конструкцию: каждый выходной
    # байт = XOR с ПРЕДЫДУЩИМ байтом ИСХОДНОГО состояния (цепочка), что
    # эквивалентно потоковому XOR и легко обращается.
    orig[0] = data[0]
    for i in range(1, n):
        orig[i] = data[i] ^ orig[i - 1]
    return bytes(orig)


def xor_chain_forward(data: bytes) -> bytes:
    """Действительно обратимая версия: out[0]=in[0]; out[i]=in[i] xor in[i-1]."""
    n = len(data)
    out = bytearray(n)
    out[0] = data[0]
    for i in range(1, n):
        out[i] = data[i] ^ data[i - 1]
    return bytes(out)


def xor_chain_inverse(data: bytes) -> bytes:
    n = len(data)
    orig = bytearray(n)
    orig[0] = data[0]
    for i in range(1, n):
        orig[i] = data[i] ^ orig[i - 1]
    return bytes(orig)


def cyclic_shift_forward(data: bytes) -> bytes:
    if not data:
        return data
    return data[1:] + data[:1]


def cyclic_shift_inverse(data: bytes) -> bytes:
    if not data:
        return data
    return data[-1:] + data[:-1]


def _fixed_bit_permutation(n_bits: int) -> List[int]:
    """Детерминированная, зависящая только от длины блока перестановка
    битов (обратимая, т.к. это перестановка индексов)."""
    # простая, воспроизводимая схема: reverse + interleave
    perm = list(range(n_bits))
    half = n_bits // 2
    new_perm = []
    for i in range(half):
        new_perm.append(perm[i])
        new_perm.append(perm[half + i])
    if n_bits % 2:
        new_perm.append(perm[-1])
    return new_perm


def bit_permutation_forward(data: bytes) -> bytes:
    n_bits = len(data) * 8
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    perm = _fixed_bit_permutation(n_bits)
    new_bits = [0] * n_bits
    for i, p in enumerate(perm):
        new_bits[i] = bits[p]
    out = bytearray(len(data))
    for i in range(len(data)):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | new_bits[i * 8 + j]
        out[i] = byte
    return bytes(out)


def bit_permutation_inverse(data: bytes) -> bytes:
    n_bits = len(data) * 8
    bits = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    perm = _fixed_bit_permutation(n_bits)
    orig_bits = [0] * n_bits
    for i, p in enumerate(perm):
        orig_bits[p] = bits[i]
    out = bytearray(len(data))
    for i in range(len(data)):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | orig_bits[i * 8 + j]
        out[i] = byte
    return bytes(out)


def apply_linear_transform(data: bytes, cols: int, transform: str, forward: bool = True) -> bytes:
    if transform == "aes_like":
        state = bytes_to_gen_state(data, cols)
        if forward:
            state = gen_shift_rows(state, cols)
            state = gen_mix_columns(state, cols)
        else:
            state = gen_inv_mix_columns(state, cols)
            state = gen_inv_shift_rows(state, cols)
        return gen_state_to_bytes(state, cols)
    elif transform == "xor_neighbors":
        return xor_chain_forward(data) if forward else xor_chain_inverse(data)
    elif transform == "cyclic_shift":
        return cyclic_shift_forward(data) if forward else cyclic_shift_inverse(data)
    elif transform == "bit_permutation":
        return bit_permutation_forward(data) if forward else bit_permutation_inverse(data)
    else:
        raise ValueError(f"Неизвестное линейное преобразование: {transform}")


# ---------------------------------------------------------------------------
# Обобщённое (не строго по FIPS-197, но по той же идее) расширение ключа
# ---------------------------------------------------------------------------
def generalized_key_expansion(key: bytes, nk: int, nr: int, words_per_round_key: int,
                               sbox: List[int], rcon: List[int]) -> Dict[str, Any]:
    total_words = words_per_round_key * (nr + 1)
    words = []
    trace = []
    for i in range(nk):
        words.append(list(key[4 * i:4 * i + 4]))

    rcon_index = 1
    for i in range(nk, total_words):
        temp = list(words[i - 1])
        step = {"word_index": i, "prev_word": list(temp)}
        if i % nk == 0:
            after_rot = rot_word(temp)
            after_sub = sub_word(after_rot, sbox)
            rc = rcon[(rcon_index - 1) % len(rcon)]
            rcon_word = [rc, 0, 0, 0]
            temp = xor_words(after_sub, rcon_word)
            step.update({"rot_word": after_rot, "sub_word": after_sub,
                         "rcon": rc, "rcon_word": rcon_word})
            rcon_index += 1
        elif nk > 6 and i % nk == 4:
            temp = sub_word(temp, sbox)
            step.update({"sub_word": temp})
        new_word = xor_words(words[i - nk], temp)
        step.update({"word_minus_nk": list(words[i - nk]), "new_word": list(new_word)})
        trace.append(step)
        words.append(new_word)

    round_keys = []
    for r in range(nr + 1):
        rk = b""
        for w in range(words_per_round_key):
            rk += bytes(words[r * words_per_round_key + w])
        round_keys.append(rk)

    return {"words": words, "round_keys": round_keys, "trace": trace}


class ExperimentalCipher:
    """
    Экспериментальный SPN-шифр с настраиваемыми параметрами. НЕ является
    AES и явно помечен как таковой (см. self.standard == False).
    """

    def __init__(self, key: bytes, block_bits: int, key_bits: int, num_rounds: int,
                 sbox: List[int], linear_transform: str = "aes_like"):
        if block_bits % 32 != 0:
            raise ValueError("Размер блока должен быть кратен 32 битам")
        if key_bits % 32 != 0:
            raise ValueError("Размер ключа должен быть кратен 32 битам")
        if len(key) * 8 != key_bits:
            raise ValueError(f"Ключ должен быть {key_bits} бит")
        if linear_transform not in LINEAR_TRANSFORMS:
            raise ValueError(f"Неизвестное линейное преобразование: {linear_transform}")

        self.standard = False  # Явно НЕ AES
        self.block_bits = block_bits
        self.block_bytes = block_bits // 8
        self.key_bits = key_bits
        self.nk = key_bits // 32
        self.nr = num_rounds
        self.cols = self.block_bytes // 4
        self.sbox = sbox
        self.inv_sbox = build_inverse_sbox(sbox)
        self.linear_transform = linear_transform

        from .aes_sbox import AES_RCON
        self.key_schedule = generalized_key_expansion(
            key, self.nk, self.nr, self.cols, self.sbox, AES_RCON)
        self.round_keys = self.key_schedule["round_keys"]

    def encrypt_block(self, block: bytes) -> Tuple[bytes, List[Dict[str, Any]]]:
        assert len(block) == self.block_bytes
        trace = []
        state = bytes(block)
        trace.append({"round": 0, "stage": "InitialState", "data": state})

        state = bytes(a ^ b for a, b in zip(state, self.round_keys[0]))
        trace.append({"round": 0, "stage": "AddRoundKey", "data": state,
                       "round_key": self.round_keys[0]})

        for rnd in range(1, self.nr + 1):
            state = bytes(self.sbox[b] for b in state)
            trace.append({"round": rnd, "stage": "SubBytes", "data": state})

            state = apply_linear_transform(state, self.cols, self.linear_transform, forward=True)
            trace.append({"round": rnd, "stage": f"LinearTransform({self.linear_transform})",
                           "data": state})

            state = bytes(a ^ b for a, b in zip(state, self.round_keys[rnd]))
            trace.append({"round": rnd, "stage": "AddRoundKey", "data": state,
                           "round_key": self.round_keys[rnd]})

        trace.append({"round": self.nr, "stage": "Ciphertext", "data": state})
        return state, trace

    def decrypt_block(self, block: bytes) -> Tuple[bytes, List[Dict[str, Any]]]:
        assert len(block) == self.block_bytes
        trace = []
        state = bytes(block)
        trace.append({"round": self.nr, "stage": "InitialState(Ciphertext)", "data": state})

        for rnd in range(self.nr, 0, -1):
            state = bytes(a ^ b for a, b in zip(state, self.round_keys[rnd]))
            trace.append({"round": rnd, "stage": "InvAddRoundKey", "data": state,
                           "round_key": self.round_keys[rnd]})

            state = apply_linear_transform(state, self.cols, self.linear_transform, forward=False)
            trace.append({"round": rnd, "stage": f"InvLinearTransform({self.linear_transform})",
                           "data": state})

            state = bytes(self.inv_sbox[b] for b in state)
            trace.append({"round": rnd, "stage": "InvSubBytes", "data": state})

        state = bytes(a ^ b for a, b in zip(state, self.round_keys[0]))
        trace.append({"round": 0, "stage": "InvAddRoundKey", "data": state,
                       "round_key": self.round_keys[0]})

        trace.append({"round": 0, "stage": "PlaintextBlock", "data": state})
        return state, trace
