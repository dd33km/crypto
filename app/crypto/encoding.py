# -*- coding: utf-8 -*-
"""
app/crypto/encoding.py

Утилиты для преобразования Unicode-текста <-> UTF-8 байты <-> HEX <-> BIN,
используемые повсюду в GUI для отображения "Text / Hex / Binary" одного и
того же состояния данных. Полностью поддерживает произвольный Unicode
(русский, английский, китайский, японский, арабский и т.д.), так как
кодирование выполняется через стандартный UTF-8, который может представить
любой символ Unicode.
"""
from __future__ import annotations


def text_to_bytes(text: str) -> bytes:
    """Unicode-текст -> UTF-8 байты."""
    return text.encode("utf-8")


def bytes_to_text(data: bytes, errors: str = "replace") -> str:
    """UTF-8 байты -> Unicode-текст. errors='replace' на случай, что байты
    не являются корректным UTF-8 (например, промежуточное шифрованное
    состояние - в этом случае используем HEX для отображения)."""
    return data.decode("utf-8", errors=errors)


def bytes_to_hex(data: bytes, spaced: bool = True) -> str:
    h = data.hex().upper()
    if not spaced:
        return h
    return " ".join(h[i:i + 2] for i in range(0, len(h), 2))


def hex_to_bytes(hex_str: str) -> bytes:
    cleaned = hex_str.replace(" ", "").replace("\n", "").replace(":", "")
    return bytes.fromhex(cleaned)


def bytes_to_bin(data: bytes, spaced: bool = True) -> str:
    bits = "".join(f"{b:08b}" for b in data)
    if not spaced:
        return bits
    return " ".join(f"{b:08b}" for b in data)


def bin_to_bytes(bin_str: str) -> bytes:
    cleaned = bin_str.replace(" ", "").replace("\n", "")
    if len(cleaned) % 8 != 0:
        raise ValueError("Длина бинарной строки должна быть кратна 8 битам")
    return bytes(int(cleaned[i:i + 8], 2) for i in range(0, len(cleaned), 8))


def is_probably_valid_utf8_text(data: bytes) -> bool:
    """Пытается понять, представляют ли байты осмысленный UTF-8 текст
    (используется, чтобы решить, показывать ли вкладку TEXT для
    промежуточных/зашифрованных состояний, которые обычно НЕ являются
    валидным текстом)."""
    try:
        data.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def bytes_to_matrix_4x4(data: bytes):
    """16 байт -> 4x4 матрица в порядке AES (столбцовый порядок)."""
    assert len(data) == 16
    m = [[0] * 4 for _ in range(4)]
    for i in range(16):
        m[i % 4][i // 4] = data[i]
    return m
