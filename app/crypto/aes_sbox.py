# -*- coding: utf-8 -*-
"""
app/crypto/aes_sbox.py

Стандартная (официальная, FIPS-197) S-box AES и обратная (inverse) S-box,
а также арифметика в конечном поле GF(2^8), необходимая для:
  - вычисления мультипликативного обратного элемента (используется и для
    построения S-box, и для MixColumns/InvMixColumns);
  - генерации альтернативных ("экспериментальных") S-box для учебного режима.

Всё, что здесь описано, является хорошо известной, официально
опубликованной спецификацией (NIST FIPS-197) и не содержит какой-либо
"секретной" или потенциально опасной информации - это открытый,
общеизвестный государственный стандарт шифрования, используемый повсеместно
(HTTPS, Wi-Fi, банковские системы и т.д.), и его реализация в учебных целях
абсолютно стандартна для курсов по криптографии.
"""

from __future__ import annotations
import random
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Официальная (стандартная) AES S-box, 16x16, значения даны построчно.
# Источник: NIST FIPS-197, Figure 7.
# ---------------------------------------------------------------------------
AES_SBOX: List[int] = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16,
]

AES_RCON: List[int] = [
    0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80,
    0x1B, 0x36, 0x6C, 0xD8, 0xAB, 0x4D, 0x9A,
]


def build_inverse_sbox(sbox: List[int]) -> List[int]:
    """Строит inverse S-box: inv[sbox[i]] = i."""
    inv = [0] * 256
    for i, v in enumerate(sbox):
        inv[v] = i
    return inv


AES_INV_SBOX: List[int] = build_inverse_sbox(AES_SBOX)


# ---------------------------------------------------------------------------
# Арифметика GF(2^8) с несводимым многочленом x^8+x^4+x^3+x+1 (0x11B) -
# именно этот многочлен использует стандарт AES.
# ---------------------------------------------------------------------------
def gf_xtime(a: int) -> int:
    """Умножение на x (0x02) в GF(2^8)."""
    a <<= 1
    if a & 0x100:
        a ^= 0x11B
    return a & 0xFF


def gf_mul(a: int, b: int) -> int:
    """Полное умножение двух байт в GF(2^8) по модулю 0x11B."""
    result = 0
    a &= 0xFF
    b &= 0xFF
    for _ in range(8):
        if b & 1:
            result ^= a
        hi = a & 0x80
        a = (a << 1) & 0xFF
        if hi:
            a ^= 0x1B
        b >>= 1
    return result & 0xFF


def gf_inverse(a: int) -> int:
    """Мультипликативное обратное a в GF(2^8) (0 -> 0, как определено в AES)."""
    if a == 0:
        return 0
    for candidate in range(1, 256):
        if gf_mul(a, candidate) == 1:
            return candidate
    return 0  # недостижимо


def affine_transform(byte: int, matrix_rows: List[int], constant: int) -> int:
    """
    Применяет аффинное GF(2)-преобразование к байту:
        y_i = XOR(matrix_rows[i] & byte бит-битно) XOR constant_i

    matrix_rows - список из 8 байт, где matrix_rows[i] задаёт, какие биты
    входного байта участвуют в вычислении бита i выходного байта (как в
    классическом определении AES S-box: строка матрицы, циклически
    сдвинутая).
    """
    out = 0
    for i in range(8):
        row = matrix_rows[i]
        bit = 0
        for j in range(8):
            if (row >> j) & 1:
                bit ^= (byte >> j) & 1
        bit ^= (constant >> i) & 1
        out |= (bit << i)
    return out & 0xFF


STANDARD_AFFINE_ROWS = [0b10001111, 0b11000111, 0b11100011, 0b11110001,
                         0b11111000, 0b01111100, 0b00111110, 0b00011111]
STANDARD_AFFINE_CONST = 0x63


def generate_sbox_standard_construction(seed: int | None = None,
                                         randomize_constant: bool = True) -> Tuple[List[int], dict]:
    """
    Генерирует S-box по той же математической схеме, что и стандартный
    AES S-box (инверсия в GF(2^8) + аффинное GF(2)-преобразование), но со
    случайной аффинной константой (и, опционально, случайно
    циклически сдвинутой матрицей), так что при каждом вызове получается
    новый, отличный от стандартного, но всё ещё биективный (обратимый) S-box.

    Это отражает идею, лежащую в основе построения S-box AES, при этом
    давая новый вариант таблицы при каждом нажатии кнопки
    "Сгенерировать S-box", как того требует учебный режим приложения.

    Возвращает (sbox, meta), где meta содержит параметры, необходимые для
    воспроизведения и последующего дешифрования (обязательно сохраняются
    вместе с шифротекстом).
    """
    rng = random.Random(seed)
    constant = rng.randint(0, 255) if randomize_constant else STANDARD_AFFINE_CONST
    shift = rng.randint(0, 7)
    rows = STANDARD_AFFINE_ROWS[shift:] + STANDARD_AFFINE_ROWS[:shift]

    sbox = [0] * 256
    for x in range(256):
        inv = gf_inverse(x)
        sbox[x] = affine_transform(inv, rows, constant)

    meta = {
        "method": "gf_inverse_affine",
        "constant": constant,
        "row_shift": shift,
        "seed": seed,
    }
    return sbox, meta


def generate_sbox_from_meta(meta: dict) -> List[int]:
    """Восстанавливает S-box из сохранённых метаданных (для дешифрования)."""
    if meta.get("method") == "random_permutation":
        rng = random.Random(meta["seed"])
        sbox = list(range(256))
        rng.shuffle(sbox)
        return sbox
    # По умолчанию - стандартная конструкция инверсия+аффинное преобразование
    shift = meta.get("row_shift", 0)
    constant = meta.get("constant", STANDARD_AFFINE_CONST)
    rows = STANDARD_AFFINE_ROWS[shift:] + STANDARD_AFFINE_ROWS[:shift]
    sbox = [0] * 256
    for x in range(256):
        inv = gf_inverse(x)
        sbox[x] = affine_transform(inv, rows, constant)
    return sbox


def generate_sbox_random_permutation(seed: int | None = None) -> Tuple[List[int], dict]:
    """
    Альтернативный (упрощённый) резервный способ генерации S-box: случайная
    биективная перестановка 0..255. Гарантированно обратима (это просто
    перестановка), но НЕ обладает криптографическими свойствами настоящего
    AES S-box (нелинейность, устойчивость к дифференциальному
    криптоанализу и т.п.) - используется исключительно как запасной вариант
    и явно помечается в интерфейсе как учебный/экспериментальный.
    """
    rng = random.Random(seed)
    sbox = list(range(256))
    rng.shuffle(sbox)
    meta = {"method": "random_permutation", "seed": seed}
    return sbox, meta


def sbox_fingerprint(sbox: List[int]) -> str:
    """Короткий идентификатор S-box (для отображения пользователю)."""
    import hashlib
    h = hashlib.sha256(bytes(sbox)).hexdigest()
    return h[:12].upper()
