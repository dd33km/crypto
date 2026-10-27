# -*- coding: utf-8 -*-
"""
app/crypto/key_generator.py

Генерация ключа четырьмя способами:
  1. Фраза          -> SHA-256(фраза), взять нужное число бит
  2. Слово          -> тот же механизм (SHA-256)
  3. Бинарное значение -> пользователь вводит биты напрямую, с проверкой длины
  4. Случайный ключ -> os.urandom (криптографически стойкий ГПСЧ)
"""
from __future__ import annotations
import os
import hashlib
from dataclasses import dataclass


@dataclass
class KeyInfo:
    key_bytes: bytes
    bits: int
    source_method: str
    source_text: str | None = None

    @property
    def hex(self) -> str:
        return self.key_bytes.hex().upper()

    @property
    def bin(self) -> str:
        return " ".join(f"{b:08b}" for b in self.key_bytes)

    @property
    def as_text_if_printable(self) -> str | None:
        try:
            s = self.key_bytes.decode("utf-8")
            if all(32 <= ord(c) < 0x10000 for c in s):
                return s
        except UnicodeDecodeError:
            pass
        return None


def key_from_phrase(phrase: str, bits: int) -> KeyInfo:
    """
    Преобразует фразу/слово в ключ заданной длины с помощью SHA-256.
    Если требуется больше бит, чем даёт один SHA-256 (256 бит), используется
    расширение через HKDF-подобную цепочку хешей (SHA-256(phrase || counter)),
    что покрывает и учебные размеры ключа (например, 64 бита для
    экспериментального режима).
    """
    if bits <= 0 or bits % 8 != 0:
        raise ValueError("Размер ключа в битах должен быть положительным и кратным 8")
    needed_bytes = bits // 8

    material = b""
    counter = 0
    data = phrase.encode("utf-8")
    while len(material) < needed_bytes:
        material += hashlib.sha256(data + counter.to_bytes(4, "big")).digest()
        counter += 1
    key_bytes = material[:needed_bytes]
    return KeyInfo(key_bytes=key_bytes, bits=bits, source_method="phrase", source_text=phrase)


def key_from_word(word: str, bits: int) -> KeyInfo:
    info = key_from_phrase(word, bits)
    info.source_method = "word"
    return info


def key_from_binary_string(bin_str: str, bits: int) -> KeyInfo:
    """Пользователь вводит биты напрямую (например, 0101...). Строгая
    проверка длины: должна ровно совпадать с требуемым размером ключа."""
    cleaned = bin_str.strip().replace(" ", "")
    if not cleaned:
        raise ValueError("Пустое бинарное значение")
    if any(c not in "01" for c in cleaned):
        raise ValueError("Бинарное значение должно содержать только символы 0 и 1")
    if len(cleaned) != bits:
        raise ValueError(
            f"Длина бинарного ключа должна быть ровно {bits} бит, "
            f"введено {len(cleaned)} бит"
        )
    # дополняем до кратности 8 слева нулями на всякий случай (не должно
    # случиться, так как bits всегда кратно 8 в этом приложении)
    if len(cleaned) % 8 != 0:
        cleaned = cleaned.rjust((len(cleaned) // 8 + 1) * 8, "0")
    key_bytes = bytes(int(cleaned[i:i + 8], 2) for i in range(0, len(cleaned), 8))
    return KeyInfo(key_bytes=key_bytes, bits=bits, source_method="binary", source_text=bin_str)


def key_random(bits: int) -> KeyInfo:
    if bits <= 0 or bits % 8 != 0:
        raise ValueError("Размер ключа в битах должен быть положительным и кратным 8")
    key_bytes = os.urandom(bits // 8)
    return KeyInfo(key_bytes=key_bytes, bits=bits, source_method="random", source_text=None)


NON_STANDARD_AES_KEY_SIZES = {64}
STANDARD_AES_KEY_SIZES = {128, 192, 256}


def is_standard_aes_key_size(bits: int) -> bool:
    return bits in STANDARD_AES_KEY_SIZES


def key_size_warning(bits: int) -> str | None:
    if bits in NON_STANDARD_AES_KEY_SIZES:
        return ("64-битный ключ доступен только в учебном режиме и "
                "не является стандартным AES.")
    if bits not in STANDARD_AES_KEY_SIZES:
        return ("Это нестандартный размер ключа - доступен только в "
                "экспериментальном учебном режиме, не является AES.")
    return None
