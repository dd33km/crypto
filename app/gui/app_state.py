# -*- coding: utf-8 -*-
"""
app/gui/app_state.py

Общее состояние приложения, разделяемое между вкладками (ключ, S-box,
параметры шифрования, результаты последнего шифрования/дешифрования для
вкладки "Раунды" и т.д.)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

from app.crypto.aes_sbox import AES_SBOX
from app.crypto.key_generator import KeyInfo


@dataclass
class AppState:
    # Параметры шифра
    mode: str = "AES"                 # "AES" | "Experimental"
    cipher_submode: str = "ECB"       # "ECB" | "CBC"
    block_bits: int = 128
    key_bits: int = 128
    rounds: int = 10
    linear_transform: str = "aes_like"

    # Ключ
    key_info: Optional[KeyInfo] = None

    # S-box
    sbox: List[int] = field(default_factory=lambda: list(AES_SBOX))
    sbox_meta: Dict[str, Any] = field(default_factory=lambda: {"method": "standard_aes"})
    sbox_id: str = "STANDARD-AES"

    # Результаты последней операции (для вкладки "Раунды")
    last_operation: Optional[str] = None       # "encrypt" | "decrypt"
    last_block_traces: List[List[Dict[str, Any]]] = field(default_factory=list)
    last_container: Optional[str] = None
    last_plaintext: Optional[str] = None

    # Состояние вкладки "Сеть Фейстеля" (независимо от вкладки AES)
    feistel_last_container: Optional[str] = None

    # тема и язык интерфейса
    theme: str = "light"
    language: str = "ru"

    def is_standard_aes(self) -> bool:
        return self.mode == "AES"
