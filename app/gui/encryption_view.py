# -*- coding: utf-8 -*-
"""
app/gui/encryption_view.py

Вкладка "Шифрование": ввод текста -> выбор режима (AES / экспериментальный)
-> выбор параметров -> шифрование с подробным протоколом.
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPlainTextEdit,
    QPushButton, QComboBox, QRadioButton, QButtonGroup, QMessageBox,
    QFormLayout, QCheckBox, QTextEdit
)
from PySide6.QtCore import Signal

from app.crypto.encoding import text_to_bytes, bytes_to_hex, bytes_to_bin
from app.crypto.padding import pad_zero_bytes, split_into_blocks
from app.crypto.aes import AESCipher
from app.crypto.experimental_cipher import ExperimentalCipher, LINEAR_TRANSFORMS
from app.crypto.container import build_container
from app.crypto import key_generator as kg


class EncryptionView(QWidget):
    encryption_done = Signal()
    request_switch_to_round_tab = Signal()

    def __init__(self, app_state, key_view, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.key_view = key_view
        self._build_ui()
        self._on_mode_changed()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Шифрование")
        title.setObjectName("heading")
        layout.addWidget(title)

        input_box = QGroupBox("Исходный текст (поддерживается любой Unicode)")
        input_layout = QVBoxLayout(input_box)
        self.text_input = QPlainTextEdit()
        self.text_input.setPlaceholderText("Например: Привет, мир! 你好世界 こんにちは مرحبا")
        self.text_input.setPlainText("Привет, мир! 你好世界")
        input_layout.addWidget(self.text_input)
        layout.addWidget(input_box)

        mode_box = QGroupBox("Режим")
        mode_layout = QHBoxLayout(mode_box)
        self.mode_group = QButtonGroup(self)
        self.rb_aes = QRadioButton("AES Standard")
        self.rb_exp = QRadioButton("Experimental AES-like Cipher")
        self.rb_aes.setChecked(True)
        self.mode_group.addButton(self.rb_aes, 0)
        self.mode_group.addButton(self.rb_exp, 1)
        self.rb_aes.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.rb_aes)
        mode_layout.addWidget(self.rb_exp)
        self.mode_badge = QLabel("AES Standard")
        self.mode_badge.setObjectName("badgeAES")
        mode_layout.addWidget(self.mode_badge)
        mode_layout.addStretch()
        layout.addWidget(mode_box)

        params_box = QGroupBox("Параметры")
        params_layout = QFormLayout(params_box)

        self.block_combo = QComboBox()
        params_layout.addRow("Размер блока:", self.block_combo)

        self.key_size_combo = QComboBox()
        params_layout.addRow("Размер ключа:", self.key_size_combo)

        self.rounds_combo = QComboBox()
        params_layout.addRow("Раунды:", self.rounds_combo)

        self.cipher_mode_combo = QComboBox()
        self.cipher_mode_combo.addItems(["ECB", "CBC"])
        params_layout.addRow("Режим сцепления блоков:", self.cipher_mode_combo)

        self.transform_combo = QComboBox()
        for t in LINEAR_TRANSFORMS:
            self.transform_combo.addItem(t)
        params_layout.addRow("Линейное преобразование (эксперим.):", self.transform_combo)

        layout.addWidget(params_box)

        self.warning_label = QLabel("")
        self.warning_label.setObjectName("warning")
        self.warning_label.setWordWrap(True)
        self.warning_label.hide()
        layout.addWidget(self.warning_label)

        key_row = QHBoxLayout()
        self.key_display = QLabel("Ключ: (см. вкладку 'Ключ')")
        self.key_display.setWordWrap(True)
        key_row.addWidget(self.key_display)
        layout.addLayout(key_row)

        self.encrypt_btn = QPushButton("ЗАШИФРОВАТЬ")
        self.encrypt_btn.clicked.connect(self._on_encrypt)
        layout.addWidget(self.encrypt_btn)

        result_box = QGroupBox("Результат")
        result_layout = QVBoxLayout(result_box)

        self.pipeline_label = QLabel("")
        self.pipeline_label.setWordWrap(True)
        self.pipeline_label.setObjectName("subheading")
        result_layout.addWidget(self.pipeline_label)

        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setMaximumHeight(150)
        result_layout.addWidget(QLabel("Контейнер шифротекста (JSON+Base64) - скопируйте для дешифрования:"))
        result_layout.addWidget(self.result_text)

        btn_row = QHBoxLayout()
        self.copy_btn = QPushButton("Скопировать в буфер обмена")
        self.copy_btn.setObjectName("secondary")
        self.copy_btn.clicked.connect(self._on_copy)
        self.view_rounds_btn = QPushButton("Посмотреть раунды →")
        self.view_rounds_btn.setObjectName("secondary")
        self.view_rounds_btn.clicked.connect(self.request_switch_to_round_tab.emit)
        btn_row.addWidget(self.copy_btn)
        btn_row.addWidget(self.view_rounds_btn)
        btn_row.addStretch()
        result_layout.addLayout(btn_row)

        layout.addWidget(result_box)
        layout.addStretch()

    # ------------------------------------------------------------------
    def _on_mode_changed(self):
        is_aes = self.rb_aes.isChecked()
        self.app_state.mode = "AES" if is_aes else "Experimental"
        self.mode_badge.setText("AES Standard" if is_aes else "Experimental AES-like Cipher")
        self.mode_badge.setObjectName("badgeAES" if is_aes else "badgeExp")
        self.mode_badge.style().unpolish(self.mode_badge)
        self.mode_badge.style().polish(self.mode_badge)

        self.block_combo.clear()
        self.key_size_combo.clear()
        self.rounds_combo.clear()

        if is_aes:
            self.block_combo.addItem("128 бит (фиксировано стандартом AES)", 128)
            self.block_combo.setEnabled(False)
            for s in (128, 192, 256):
                self.key_size_combo.addItem(f"{s} бит", s)
            self.key_size_combo.currentIndexChanged.connect(self._update_rounds_for_aes)
            self._update_rounds_for_aes()
            self.rounds_combo.setEnabled(False)
            self.transform_combo.setEnabled(False)
            self.warning_label.hide()
        else:
            for s in (64, 128, 192, 256):
                self.block_combo.addItem(f"{s} бит", s)
            self.block_combo.setEnabled(True)
            for s in (64, 128, 192, 256):
                self.key_size_combo.addItem(f"{s} бит", s)
            for r in (10, 12, 14, 16):
                self.rounds_combo.addItem(str(r), r)
            self.rounds_combo.setEnabled(True)
            self.transform_combo.setEnabled(True)
            self.warning_label.setText(
                "Это экспериментальный режим - НЕ стандарт AES. Изменённые "
                "параметры (размер блока/ключа, число раундов, S-box, "
                "линейное преобразование) сделаны для демонстрации, а не "
                "для реального применения."
            )
            self.warning_label.show()

        if hasattr(self.key_view, "sync_with_mode"):
            self.key_view.sync_with_mode()
        self._update_key_display()

    def _update_rounds_for_aes(self):
        self.rounds_combo.clear()
        keybits = self.key_size_combo.currentData()
        nr = {128: 10, 192: 12, 256: 14}.get(keybits, 10)
        self.rounds_combo.addItem(str(nr), nr)

    def _update_key_display(self):
        info = self.app_state.key_info
        if info is None:
            self.key_display.setText("Ключ: не сгенерирован (перейдите на вкладку 'Ключ')")
        else:
            self.key_display.setText(
                f"Ключ ({info.bits} бит): HEX={info.hex}"
            )

    def showEvent(self, event):
        super().showEvent(event)
        self._update_key_display()

    # ------------------------------------------------------------------
    def _on_encrypt(self):
        text = self.text_input.toPlainText()
        if not text:
            QMessageBox.warning(self, "Пустой текст", "Введите текст для шифрования")
            return

        key_info = self.app_state.key_info
        required_bits = self.key_size_combo.currentData()
        if key_info is None or key_info.bits != required_bits:
            QMessageBox.warning(
                self, "Несоответствие ключа",
                f"Текущий ключ имеет размер {key_info.bits if key_info else 0} бит, "
                f"а выбранный размер ключа - {required_bits} бит. "
                f"Перейдите на вкладку 'Ключ' и сгенерируйте ключ нужного размера."
            )
            return

        is_aes = self.rb_aes.isChecked()
        block_bits = self.block_combo.currentData()
        key_bits = required_bits
        cipher_mode = self.cipher_mode_combo.currentText()

        data = text_to_bytes(text)
        block_bytes = block_bits // 8
        padded, pad_info = pad_zero_bytes(data, block_bytes)
        blocks = split_into_blocks(padded, block_bytes)

        iv = os.urandom(block_bytes) if cipher_mode == "CBC" else None

        try:
            if is_aes:
                cipher = AESCipher(key_info.key_bytes, key_bits, sbox=self.app_state.sbox)
                ct_blocks, traces = cipher.encrypt_blocks(blocks, mode=cipher_mode, iv=iv)
                rounds_used = cipher.nr
            else:
                rounds = self.rounds_combo.currentData()
                transform = self.transform_combo.currentText()
                cipher = ExperimentalCipher(key_info.key_bytes, block_bits, key_bits, rounds,
                                             sbox=self.app_state.sbox, linear_transform=transform)
                ct_blocks = []
                traces = []
                prev = iv
                for block in blocks:
                    if cipher_mode == "CBC" and prev is not None:
                        block = bytes(a ^ b for a, b in zip(block, prev))
                    ct, tr = cipher.encrypt_block(block)
                    ct_blocks.append(ct)
                    traces.append(tr)
                    if cipher_mode == "CBC":
                        prev = ct
                rounds_used = rounds
        except Exception as e:
            QMessageBox.critical(self, "Ошибка шифрования", str(e))
            return

        ciphertext = b"".join(ct_blocks)
        container = build_container(
            mode="AES" if is_aes else "Experimental",
            cipher_mode=cipher_mode,
            block_bits=block_bits,
            key_bits=key_bits,
            rounds=rounds_used,
            sbox=self.app_state.sbox,
            sbox_meta=self.app_state.sbox_meta,
            linear_transform=self.transform_combo.currentText() if not is_aes else "",
            iv_hex=iv.hex() if iv else "",
            original_length_bytes=pad_info["original_length_bytes"],
            ciphertext_hex=ciphertext.hex(),
        )

        self.app_state.last_operation = "encrypt"
        self.app_state.last_block_traces = traces
        self.app_state.last_container = container

        pipeline = (
            f"Исходные данные: {pad_info['original_length_bytes']} байт "
            f"({pad_info['original_length_bits']} бит)\n"
            f"↓ Padding: добавлено {pad_info['padding_bytes_added']} нулевых байт\n"
            f"↓ Разбито на {len(blocks)} блок(ов) по {block_bytes} байт\n"
            f"↓ {'AES-' + str(key_bits) if is_aes else 'Experimental'}, "
            f"{rounds_used} раунд(ов), режим {cipher_mode}\n"
            f"↓ Ciphertext: {len(ciphertext)} байт"
        )
        self.pipeline_label.setText(pipeline)
        self.result_text.setPlainText(container)

        self.encryption_done.emit()
        QMessageBox.information(self, "Готово",
                                 "Шифрование завершено. Перейдите на вкладку 'Раунды', "
                                 "чтобы увидеть подробный протокол.")

    def _on_copy(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.result_text.toPlainText())
