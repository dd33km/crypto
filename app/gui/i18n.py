# -*- coding: utf-8 -*-
"""Lightweight runtime RU/EN translation for the desktop UI."""
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QGroupBox, QCheckBox, QRadioButton,
    QTabWidget, QLineEdit, QPlainTextEdit, QTextEdit, QComboBox,
    QTableWidget, QDialog
)

EXACT = {
    "HASH — хеширование": "HASH — hashing",
    "Два алгоритма, две отдельные учебные схемы. IV фиксирован стандартом, функция сжатия показана по раундам.": "Two algorithms, two separate educational diagrams. The IV is fixed by the standard and the compression function is shown round by round.",
    "Исходное сообщение": "Input message",
    "Введите слово или фразу": "Enter a word or phrase",
    "Вычислить хэш": "Calculate hash",
    "Скопировать хэш": "Copy hash",
    "Режим визуализации": "Visualization mode",
    "Учебный — первые 16 раундов": "Educational — first 16 rounds",
    "Стандартный — все 64 раунда": "Standard — all 64 rounds",
    "Детали текущего раунда": "Current round details",
    "← Предыдущий": "← Previous",
    "Следующий →": "Next →",
    "О программе": "About",
    "ⓘ  О программе": "ⓘ  About",
    "Справка": "Help",
    "Настройки": "Settings",
    "Тема оформления": "Theme",
    "Шифрование": "Encryption",
    "Шифровка": "Encryption",
    "Дешифрование": "Decryption",
    "Расшифровка": "Decryption",
    "Ключ": "Key",
    "Ключ:": "Key:",
    "S-box": "S-box",
    "Раунды": "Rounds",
    "Раунд": "Round",
    "Раунд:": "Round:",
    "Раунд —": "Round —",
    "Хэширование": "Hashing",
    "Диаграмма": "Diagram",
    "Сеть Фейстеля": "Feistel Network",
    "Ввод данных": "Input",
    "Параметры": "Parameters",
    "Результат": "Result",
    "Статус:": "Status:",
    "Раунды:": "Rounds:",
    "Режим": "Mode",
    "Режим:": "Mode:",
    "Формат:": "Format:",
    "Размер блока:": "Block size:",
    "Размер ключа:": "Key size:",
    "Количество раундов:": "Number of rounds:",
    "Формат ключа:": "Key format:",
    "Текст / фраза": "Text / phrase",
    "Бинарный ввод": "Binary input",
    "Шифровать": "Encrypt",
    "ЗАШИФРОВАТЬ": "ENCRYPT",
    "Расшифровать": "Decrypt",
    "РАСШИФРОВАТЬ": "DECRYPT",
    "Контейнер шифротекста": "Ciphertext container",
    "Параметры из контейнера": "Container parameters",
    "Вставьте контейнер": "Paste a container",
    "Вставить из буфера": "Paste from clipboard",
    "Загрузить последний": "Load latest",
    "Загрузить последний шифротекст": "Load latest ciphertext",
    "Открыть диаграмму расшифровки": "Open decryption diagram",
    "Открыть диаграмму": "Open diagram",
    "Скопировать контейнер": "Copy container",
    "Скопировано ✓": "Copied ✓",
    "Скопировать в буфер обмена": "Copy to clipboard",
    "Посмотреть раунды →": "View rounds →",
    "Посмотреть раунды дешифрования →": "View decryption rounds →",
    "Сгенерировать новый ключ": "Generate new key",
    "Генерация ключа": "Key generation",
    "Случайный ключ": "Random key",
    "Слово (SHA-256)": "Word (SHA-256)",
    "Фраза (SHA-256)": "Phrase (SHA-256)",
    "Введите слово": "Enter a word",
    "Введите фразу": "Enter a phrase",
    "Введите ключ": "Enter a key",
    "Бинарное значение:": "Binary value:",
    "Бинарное значение (ввод вручную)": "Binary value (manual input)",
    "Генерация S-box": "S-box generation",
    "Способ генерации": "Generation method",
    "Сгенерировать S-box": "Generate S-box",
    "Вернуть стандартную S-box AES": "Restore standard AES S-box",
    "Визуализация S-box": "S-box visualization",
    "Таблица S-box (16x16)": "S-box table (16x16)",
    "Протокол раундов": "Round log",
    "Визуализация раундов": "Round visualization",
    "Схема раунда": "Round diagram",
    "Детали шага": "Step details",
    "Шаг": "Step",
    "После раунда": "After round",
    "Исходное состояние": "Initial state",
    "Исходное состояние (шифротекст)": "Initial state (ciphertext)",
    "Итоговый шифротекст": "Final ciphertext",
    "Восстановленный открытый блок": "Recovered plaintext block",
    "Исходный текст": "Plaintext",
    "Восстановленный текст:": "Recovered text:",
    "Восстановленный Binary:": "Recovered binary:",
    "Шифротекст (Binary):": "Ciphertext (binary):",
    "Преобразование входа": "Input conversion",
    "Словарь терминов": "Glossary",
    "Q&A / Словарь терминов": "Q&A / Glossary",
    "Методы шифрования": "Encryption methods",
    "Почему это нужно?": "Why is this needed?",
    "Запустить самопроверку": "Run self-test",
    "Самопроверка AES (официальные тестовые векторы FIPS-197)": "AES self-test (official FIPS-197 test vectors)",
    "Исходный текст (поддерживается любой Unicode)": "Plaintext (any Unicode is supported)",
    "Режим сцепления блоков:": "Block chaining mode:",
    "Линейное преобразование (эксперим.):": "Linear transform (experimental):",
    "128 бит (фиксировано стандартом AES)": "128 bits (fixed by AES standard)",
    "Зашифрованные данные (контейнер JSON+Base64)": "Encrypted data (JSON+Base64 container)",
    "Параметры, извлечённые из контейнера": "Parameters extracted from container",
    "Контейнер шифротекста (JSON+Base64) - скопируйте для дешифрования:": "Ciphertext container (JSON+Base64) - copy it for decryption:",
    "Учебная демонстрация классической сети Фейстеля.": "Educational demonstration of a classic Feistel network.",
    "Учебная визуализация: функция F работает с левым блоком L": "Educational visualization: function F operates on the left block L",
    "L → F(L,K) → XOR с R": "L → F(L,K) → XOR with R",
    "Дважды нажмите на строку раунда, чтобы открыть его блок-схему.": "Double-click a round row to open its diagram.",
    "S-box генерируется локально. Никаких сайтов, WebView или сетевых запросов.": "S-box is generated locally. No websites, WebView, or network requests.",
    "После расчёта раунда здесь будут показаны использованные ячейки S-box.": "S-box cells used by the round will be shown here.",
    "Вставьте сюда контейнер Feistel — расшифровка запустится автоматически": "Paste the Feistel container here — decryption will start automatically",
    "Контейнер Feistel — скопируйте его целиком во вкладку «Расшифровка»:": "Feistel container — copy it in full to the Decryption tab:",
    "Например: учебный ключ": "Example: training key",
    "Например: Привет, это сеть Фейстеля": "Example: Hello, this is a Feistel network",
    "Например: Привет, Фейстель!": "Example: Hello, Feistel!",
    "Например: криптография": "Example: cryptography",
    "Например: Мой секретный ключ 2026": "Example: My secret key 2026",
    "Вставьте сюда контейнер шифротекста, полученный на вкладке 'Шифрование'": "Paste the ciphertext container obtained on the Encryption tab",
    "Ключ: (см. вкладку 'Ключ')": "Key: (see the Key tab)",
    "Ключ: не сгенерирован (перейдите на вкладку 'Ключ')": "Key: not generated (open the Key tab)",
    "Сначала выполните операцию.": "Run an operation first.",
    "Сначала выполните шифрование.": "Encrypt something first.",
    "Нет данных": "No data",
    "Ошибка": "Error",
    "Ошибка шифрования": "Encryption error",
    "Ошибка расшифровки": "Decryption error",
    "Ошибка дешифрования": "Decryption error",
    "Ошибка разбора": "Parse error",
    "Пусто": "Empty",
    "Пустой текст": "Empty text",
    "Готово": "Done",
    "Внимание": "Warning",
}

REPLACEMENTS = [
    (" бит", " bits"), (" байт", " bytes"),
    ("Раунд ", "Round "), (" из ", " of "),
    ("Размер рабочего блока:", "Working block size:"),
    ("Половина:", "Half:"),
    ("Введённый текст:", "Entered text:"),
    ("Введённый Binary:", "Entered binary:"),
    ("Ключ-текст:", "Key text:"),
    ("Ключ Binary:", "Key binary:"),
    ("Текст → Binary:", "Text → binary:"),
    ("Ключ → Binary:", "Key → binary:"),
    ("Блок до padding:", "Block before padding:"),
    ("Блок после padding:", "Block after padding:"),
    ("Ключ до padding:", "Key before padding:"),
    ("Ключ после padding:", "Key after padding:"),
    ("Нули: слева ", "Zeros: left "),
    (", справа ", ", right "),
    (" (автоматически)", " (automatic)"),
    (" (из контейнера)", " (from container)"),
    ("Контейнер распознан. Расшифровка выполнена автоматически ✓", "Container recognized. Decryption completed automatically ✓"),
]

def tr(text: str, language: str) -> str:
    if language != "en" or not text:
        return text
    if text in EXACT:
        return EXACT[text]
    out = text
    for ru, en in REPLACEMENTS:
        out = out.replace(ru, en)
    return out

def _remember(obj, key: str, value: str):
    prop = f"_i18n_{key}_ru"
    if obj.property(prop) is None:
        obj.setProperty(prop, value)
    return obj.property(prop)

def apply_language(root: QWidget, language: str):
    """Translate current widget tree. Russian originals are cached on widgets."""
    widgets = [root] + root.findChildren(QWidget)
    for w in widgets:
        if isinstance(w, QDialog):
            ru = _remember(w, "window_title", w.windowTitle())
            w.setWindowTitle(tr(ru, language) if language == "en" else ru)

        if isinstance(w, QGroupBox):
            ru = _remember(w, "title", w.title())
            w.setTitle(tr(ru, language) if language == "en" else ru)
        elif isinstance(w, (QLabel, QPushButton, QCheckBox, QRadioButton)):
            ru = _remember(w, "text", w.text())
            w.setText(tr(ru, language) if language == "en" else ru)

        if isinstance(w, (QLineEdit, QPlainTextEdit, QTextEdit)):
            ru = _remember(w, "placeholder", w.placeholderText())
            w.setPlaceholderText(tr(ru, language) if language == "en" else ru)

        if isinstance(w, QTabWidget):
            if w.property("_i18n_tab_ru") is None:
                w.setProperty("_i18n_tab_ru", [w.tabText(i) for i in range(w.count())])
            originals = w.property("_i18n_tab_ru") or []
            for i, ru in enumerate(originals[:w.count()]):
                w.setTabText(i, tr(ru, language) if language == "en" else ru)

        if isinstance(w, QComboBox):
            if w.property("_i18n_combo_ru") is None:
                w.setProperty("_i18n_combo_ru", [w.itemText(i) for i in range(w.count())])
            originals = w.property("_i18n_combo_ru") or []
            for i, ru in enumerate(originals[:w.count()]):
                w.setItemText(i, tr(ru, language) if language == "en" else ru)

        if isinstance(w, QTableWidget):
            if w.property("_i18n_headers_ru") is None:
                vals = []
                for i in range(w.columnCount()):
                    item = w.horizontalHeaderItem(i)
                    vals.append(item.text() if item else "")
                w.setProperty("_i18n_headers_ru", vals)
            originals = w.property("_i18n_headers_ru") or []
            for i, ru in enumerate(originals[:w.columnCount()]):
                item = w.horizontalHeaderItem(i)
                if item:
                    item.setText(tr(ru, language) if language == "en" else ru)
