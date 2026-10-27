# -*- coding: utf-8 -*-
"""
app/crypto/container.py

Собственный контейнерный формат для хранения шифротекста ВМЕСТЕ со всеми
параметрами, необходимыми для последующего дешифрования - даже после
закрытия и повторного открытия приложения.

Формат: JSON-объект, закодированный в Base64 для удобства копирования как
одна строка текста.

Поля контейнера:
    format_version   - версия формата контейнера
    mode             - "AES" | "Experimental"
    cipher_mode      - "ECB" | "CBC"
    block_bits       - размер блока в битах
    key_bits         - размер ключа в битах
    rounds           - число раундов
    sbox             - таблица S-box (256 чисел) как использовалась при шифровании
    sbox_meta        - параметры генерации S-box (для документации/воспроизведения)
    linear_transform - используемое линейное преобразование (для Experimental)
    iv_hex           - IV в HEX, если используется CBC
    padding          - информация о дополнении (исходная длина и т.д.)
    original_length_bytes - точная исходная длина данных (байт) для снятия padding
    ciphertext_hex   - собственно зашифрованные данные, в HEX
"""
from __future__ import annotations
import json
import base64
from typing import Dict, Any


FORMAT_VERSION = 1


def build_container(*, mode: str, cipher_mode: str, block_bits: int, key_bits: int,
                     rounds: int, sbox: list, sbox_meta: dict, linear_transform: str,
                     iv_hex: str, original_length_bytes: int,
                     ciphertext_hex: str, extra: Dict[str, Any] = None) -> str:
    payload = {
        "format_version": FORMAT_VERSION,
        "mode": mode,                      # "AES" | "Experimental"
        "cipher_mode": cipher_mode,         # "ECB" | "CBC"
        "block_bits": block_bits,
        "key_bits": key_bits,
        "rounds": rounds,
        "sbox": sbox,
        "sbox_meta": sbox_meta,
        "linear_transform": linear_transform,
        "iv_hex": iv_hex,
        "original_length_bytes": original_length_bytes,
        "ciphertext_hex": ciphertext_hex,
    }
    if extra:
        payload["extra"] = extra
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def parse_container(container_str: str) -> Dict[str, Any]:
    try:
        raw = base64.b64decode(container_str.strip())
        payload = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise ValueError(f"Не удалось разобрать контейнер шифротекста: {e}")

    required = ["format_version", "mode", "cipher_mode", "block_bits", "key_bits",
                "rounds", "sbox", "original_length_bytes", "ciphertext_hex"]
    for field in required:
        if field not in payload:
            raise ValueError(f"В контейнере отсутствует обязательное поле: {field}")
    return payload
