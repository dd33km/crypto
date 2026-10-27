# -*- coding: utf-8 -*-
"""
app/gui/sbox_view.py

Вкладка "S-box": генерация новой таблицы замен, отображение таблицы,
визуального изображения и идентификатора S-box.

Источник генерации, указанный в задании:
    http://www.waysidehealth.com/Projects/crypto/Sbox.html
Приложение пытается обратиться к этому источнику как к дополнительному
источнику случайности (сид для локальной, математически корректной
конструкции S-box). Если сайт недоступен (что вполне вероятно - это
старый учебный ресурс), используется полностью локальный резервный
механизм генерации, и приложение не ломается.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt

from app.crypto.aes_sbox import (
    AES_SBOX, generate_sbox_standard_construction, generate_sbox_random_permutation,
    sbox_fingerprint, build_inverse_sbox,
)
from app.visualization.sbox_image import render_sbox_image

SOURCE_URL = "http://www.waysidehealth.com/Projects/crypto/Sbox.html"


class SboxView(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build_ui()
        self._render_current(is_standard=True)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Генерация S-box")
        title.setObjectName("heading")
        layout.addWidget(title)

        sub = QLabel(
            "По умолчанию используется стандартная S-box AES (FIPS-197). "
            "Кнопка генерирует S-box полностью локально: без браузера, WebView, HTTP-запросов "
            "и онлайн-зависимостей."
        )
        sub.setWordWrap(True)
        sub.setObjectName("subheading")
        layout.addWidget(sub)

        warn = QLabel(
            "⚠ Важно: как только вы сгенерировали собственную S-box, "
            "шифрование в режиме AES перестаёт быть стандартным AES - "
            "это уже 'AES-подобный' экспериментальный алгоритм. Стандартный "
            "AES определяет S-box строго фиксированной."
        )
        warn.setObjectName("warning")
        warn.setWordWrap(True)
        layout.addWidget(warn)

        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("Сгенерировать S-box")
        self.generate_btn.clicked.connect(self._on_generate)
        self.reset_btn = QPushButton("Вернуть стандартную S-box AES")
        self.reset_btn.setObjectName("secondary")
        self.reset_btn.clicked.connect(self._on_reset_standard)
        btn_row.addWidget(self.generate_btn)
        btn_row.addWidget(self.reset_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        info_row = QHBoxLayout()
        self.id_label = QLabel("ID текущей S-box: STANDARD-AES")
        self.id_label.setObjectName("subheading")
        info_row.addWidget(self.id_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        content_row = QHBoxLayout()

        table_box = QGroupBox("Таблица S-box (16x16)")
        table_layout = QVBoxLayout(table_box)
        self.table = QTableWidget(16, 16)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self.table)
        content_row.addWidget(table_box, 3)

        image_box = QGroupBox("Визуализация S-box")
        image_layout = QVBoxLayout(image_box)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        image_layout.addWidget(self.image_label)
        content_row.addWidget(image_box, 2)

        layout.addLayout(content_row)
        layout.addStretch()

    def _fill_table(self, sbox):
        for row in range(16):
            for col in range(16):
                value = sbox[row * 16 + col]
                item = QTableWidgetItem(f"{value:02X}")
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def _render_current(self, is_standard: bool):
        sbox = self.app_state.sbox
        self._fill_table(sbox)
        pix = render_sbox_image(sbox, dark=(self.app_state.theme == "dark"))
        self.image_label.setPixmap(pix)
        fp = sbox_fingerprint(sbox)
        label = "STANDARD-AES" if is_standard else fp
        self.app_state.sbox_id = label
        self.id_label.setText(f"ID текущей S-box: {label}")

    def _on_reset_standard(self):
        self.app_state.sbox = list(AES_SBOX)
        self.app_state.sbox_meta = {"method": "standard_aes"}
        self._render_current(is_standard=True)

    def _on_generate(self):
        # Полностью локально: никаких HTTP-запросов/WebView/браузера.
        import os
        seed = int.from_bytes(os.urandom(8), "big")
        self._finish_generation(seed, "Локальная алгоритмическая генерация (без сети)")

    def _finish_generation(self, seed: int, source_note: str):
        sbox, meta = generate_sbox_standard_construction(seed=seed)
        meta["source_note"] = source_note
        self.app_state.sbox = sbox
        self.app_state.sbox_meta = meta
        self._render_current(is_standard=False)
        self.generate_btn.setEnabled(True)
        self.generate_btn.setText("Сгенерировать S-box")
