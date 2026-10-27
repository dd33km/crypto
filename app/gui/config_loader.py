# -*- coding: utf-8 -*-
"""
app/gui/config_loader.py

Загружает описание интерфейса приложения из config/ui.json (заголовок и
размер окна, подписи меню, названия вкладок, тексты полей/кнопок вкладки
"Сеть Фейстеля" и т.д.), чтобы эти тексты и параметры не были жёстко
"зашиты" в Python-коде.

Если файл конфигурации отсутствует или повреждён, приложение не
ломается - используются встроенные значения по умолчанию (идентичные
тем, что были в JSON изначально), поэтому GUI всегда запускается.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "window": {"title": "Crypto Visualizer", "width": 1200, "height": 820},
    "menu": {
        "methods_menu": "Методы шифрования",
        "settings_menu": "Настройки",
        "help_menu": "Справка",
        "aes_action": "AES Visualizer",
        "feistel_action": "Сеть Фейстеля",
        "theme_action": "Тема оформления...",
        "about_action": "О программе",
    },
    "tabs": [
        {"id": "aes", "title": "AES Visualizer"},
        {"id": "feistel", "title": "Сеть Фейстеля"},
    ],
    "feistel": {
        "heading": "Сеть Фейстеля",
        "subheading": "Учебная демонстрация классической сети Фейстеля.",
        "input_group_title": "Исходный текст",
        "input_placeholder": "Например: Привет, Фейстель!",
        "key_group_title": "Ключ",
        "key_placeholder": "Введите ключ",
        "rounds_label": "Количество раундов:",
        "block_size_label": "Размер блока (байт):",
        "encrypt_button": "ЗАШИФРОВАТЬ",
        "decrypt_button": "РАСШИФРОВАТЬ",
        "ciphertext_group_title": "Шифротекст (контейнер)",
        "ciphertext_placeholder": "Вставьте контейнер шифротекста",
        "load_last_button": "Загрузить последний шифротекст",
        "copy_button": "Скопировать в буфер обмена",
        "result_group_title": "Результат",
        "rounds_trace_group_title": "Протокол раундов",
        "diagram_group_title": "Схема раунда",
        "round_selector_label": "Раунд:",
    },
}


def _project_root() -> Path:
    # app/gui/config_loader.py -> parents[2] == папка проекта (рядом с main.py)
    return Path(__file__).resolve().parents[2]


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_ui_config(path: str = None) -> Dict[str, Any]:
    """Загружает config/ui.json, объединяя его со значениями по умолчанию,
    так что отсутствие отдельных полей в JSON не ломает приложение."""
    if path is None:
        path = os.path.join(_project_root(), "config", "ui.json")

    if not os.path.isfile(path):
        return DEFAULT_CONFIG

    try:
        with open(path, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        return _deep_merge(DEFAULT_CONFIG, user_config)
    except (json.JSONDecodeError, OSError):
        # Повреждённый/недоступный конфиг - работаем на встроенных значениях
        return DEFAULT_CONFIG
