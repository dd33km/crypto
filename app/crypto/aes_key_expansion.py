# -*- coding: utf-8 -*-
"""
app/crypto/aes_key_expansion.py

Реализация расширения ключа (Key Expansion / Key Schedule) AES по FIPS-197,
с подробным пошаговым протоколом каждого вычисленного Word - для учебной
визуализации в GUI.

Поддерживает произвольные Nk (слов в ключе) и Nr (число раундов), что
позволяет использовать один и тот же код и для стандартного AES
(Nk=4/6/8, Nr=10/12/14), и для экспериментального режима с иным числом
раундов или размером ключа.
"""
from __future__ import annotations
from typing import List, Dict, Any
from .aes_sbox import AES_SBOX


Word = List[int]  # 4 байта


def sub_word(word: Word, sbox: List[int]) -> Word:
    return [sbox[b] for b in word]


def rot_word(word: Word) -> Word:
    return word[1:] + word[:1]


def xor_words(a: Word, b: Word) -> Word:
    return [x ^ y for x, y in zip(a, b)]


def key_expansion(key: bytes, nk: int, nr: int, sbox: List[int] = None,
                   rcon: List[int] = None) -> Dict[str, Any]:
    """
    Выполняет полное расширение ключа AES.

    Параметры:
        key  - исходный ключ (nk*4 байт)
        nk   - число 32-битных слов в ключе (4/6/8 для AES-128/192/256)
        nr   - число раундов (10/12/14 для стандартного AES,
               либо иное значение в экспериментальном режиме)
        sbox - таблица замен, используемая в SubWord (по умолчанию
               стандартная AES S-box)
        rcon - таблица Rcon (по умолчанию стандартная AES)

    Возвращает словарь:
        {
          "words": [Word, ...]            - все 4*(nr+1) слов расширенного ключа
          "round_keys": [bytes, ...]      - nr+1 раундовых ключей по 16 байт
          "trace": [ {...step info...} ]  - подробный протокол вычисления
                                             каждого нового слова (для i>=nk)
        }
    """
    if sbox is None:
        sbox = AES_SBOX
    if rcon is None:
        from .aes_sbox import AES_RCON
        rcon = AES_RCON

    if len(key) != nk * 4:
        raise ValueError(f"Длина ключа должна быть {nk*4} байт, получено {len(key)}")

    total_words = 4 * (nr + 1)
    words: List[Word] = []
    trace: List[Dict[str, Any]] = []

    # Первые Nk слов - это сам исходный ключ
    for i in range(nk):
        words.append(list(key[4 * i: 4 * i + 4]))

    rcon_index = 1
    for i in range(nk, total_words):
        temp = list(words[i - 1])
        step: Dict[str, Any] = {
            "word_index": i,
            "prev_word": list(temp),
        }
        if i % nk == 0:
            after_rot = rot_word(temp)
            after_sub = sub_word(after_rot, sbox)
            rc = rcon[rcon_index - 1] if rcon_index - 1 < len(rcon) else rcon[-1]
            rcon_word = [rc, 0x00, 0x00, 0x00]
            temp = xor_words(after_sub, rcon_word)
            step.update({
                "rot_word": after_rot,
                "sub_word": after_sub,
                "rcon": rc,
                "rcon_word": rcon_word,
                "used_rot_sub_rcon": True,
            })
            rcon_index += 1
        elif nk > 6 and i % nk == 4:
            # Дополнительный SubWord для AES-256 (Nk=8), см. FIPS-197 §5.2
            after_sub = sub_word(temp, sbox)
            temp = after_sub
            step.update({
                "sub_word": after_sub,
                "used_extra_subword": True,
            })
        new_word = xor_words(words[i - nk], temp)
        step.update({
            "word_minus_nk": list(words[i - nk]),
            "transformed_prev": list(temp),
            "new_word": list(new_word),
        })
        trace.append(step)
        words.append(new_word)

    round_keys = []
    for r in range(nr + 1):
        rk = bytes(words[4 * r]) + bytes(words[4 * r + 1]) + bytes(words[4 * r + 2]) + bytes(words[4 * r + 3])
        round_keys.append(rk)

    return {
        "words": words,
        "round_keys": round_keys,
        "trace": trace,
        "nk": nk,
        "nr": nr,
    }
