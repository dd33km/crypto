# -*- coding: utf-8 -*-
"""
app/crypto/padding.py

Дополнение (padding) данных нулевыми битами/байтами до размера, кратного
размеру блока, как того требует учебный проект.

ВАЖНО: чтобы корректно восстановить исходную длину сообщения даже если
реальные данные сами заканчиваются нулевыми байтами, приложение ВСЕГДА
сохраняет исходную длину сообщения (в байтах) в метаданных контейнера
шифротекста (см. container.py) - паддинг никогда не пытается "угадать"
длину по содержимому.
"""
from __future__ import annotations
from typing import Tuple, Dict, Any


def pad_zero_bytes(data: bytes, block_size_bytes: int) -> Tuple[bytes, Dict[str, Any]]:
    """
    Дополняет data нулевыми байтами В КОНЦЕ до кратности block_size_bytes.
    Возвращает (padded_data, info), где info содержит все величины,
    которые требуется отобразить в GUI.
    """
    original_len = len(data)
    if block_size_bytes <= 0:
        raise ValueError("Размер блока должен быть положительным")

    remainder = original_len % block_size_bytes
    if remainder == 0 and original_len != 0:
        pad_len = 0
    else:
        pad_len = block_size_bytes - remainder
        if original_len == 0:
            pad_len = block_size_bytes  # хотя бы один блок

    padded = data + (b"\x00" * pad_len)

    info = {
        "original_length_bytes": original_len,
        "original_length_bits": original_len * 8,
        "block_size_bytes": block_size_bytes,
        "padding_bytes_added": pad_len,
        "padding_bits_added": pad_len * 8,
        "padded_length_bytes": len(padded),
        "original_hex": data.hex(),
        "padded_hex": padded.hex(),
        "original_bin": " ".join(f"{b:08b}" for b in data),
        "padded_bin": " ".join(f"{b:08b}" for b in padded),
    }
    return padded, info


def unpad_zero_bytes(padded_data: bytes, original_length_bytes: int) -> bytes:
    """
    Убирает добавленные нули, восстанавливая исходную длину по значению,
    сохранённому в метаданных шифротекста (а НЕ по эвристике поиска
    "хвостовых нулей", чтобы не повредить настоящие данные, которые сами
    заканчиваются нулевыми байтами).
    """
    if original_length_bytes > len(padded_data):
        raise ValueError("Сохранённая исходная длина больше, чем длина данных после дешифрования")
    return padded_data[:original_length_bytes]


def split_into_blocks(data: bytes, block_size_bytes: int):
    return [data[i:i + block_size_bytes] for i in range(0, len(data), block_size_bytes)]
