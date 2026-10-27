# -*- coding: utf-8 -*-
"""
app/gui/decryption_view.py

Вкладка "Дешифрование": вставка ранее сохранённого контейнера
шифротекста (JSON+Base64, см. crypto/container.py) и его дешифрование с
восстановлением исходного Unicode-текста, используя ВСЕ параметры,
сохранённые внутри контейнера (это позволяет расшифровать данные даже
после закрытия и повторного открытия приложения).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPlainTextEdit,
    QPushButton, QMessageBox, QTextEdit, QFormLayout
)
from PySide6.QtCore import Signal

from app.crypto.container import parse_container
from app.crypto.aes import AESCipher
from app.crypto.experimental_cipher import ExperimentalCipher
from app.crypto.padding import unpad_zero_bytes, split_into_blocks
from app.crypto.encoding import bytes_to_text, bytes_to_hex


class DecryptionView(QWidget):
    decryption_done = Signal()
    request_switch_to_round_tab = Signal()

    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Дешифрование")
        title.setObjectName("heading")
        layout.addWidget(title)

        input_box = QGroupBox("Зашифрованные данные (контейнер JSON+Base64)")
        input_layout = QVBoxLayout(input_box)
        self.ct_input = QPlainTextEdit()
        self.ct_input.setPlaceholderText(
            "Вставьте сюда контейнер шифротекста, полученный на вкладке 'Шифрование'"
        )
        input_layout.addWidget(self.ct_input)

        btn_row = QHBoxLayout()
        self.load_last_btn = QPushButton("Загрузить последний шифротекст")
        self.load_last_btn.setObjectName("secondary")
        self.load_last_btn.clicked.connect(self._on_load_last)
        self.decrypt_btn = QPushButton("Расшифровать")
        self.decrypt_btn.clicked.connect(self._on_decrypt)
        btn_row.addWidget(self.load_last_btn)
        btn_row.addWidget(self.decrypt_btn)
        btn_row.addStretch()
        input_layout.addLayout(btn_row)

        layout.addWidget(input_box)

        params_box = QGroupBox("Параметры, извлечённые из контейнера")
        self.params_form = QFormLayout(params_box)
        self.p_mode = QLabel("-")
        self.p_block = QLabel("-")
        self.p_key = QLabel("-")
        self.p_rounds = QLabel("-")
        self.p_sbox = QLabel("-")
        self.params_form.addRow("Режим:", self.p_mode)
        self.params_form.addRow("Размер блока:", self.p_block)
        self.params_form.addRow("Размер ключа:", self.p_key)
        self.params_form.addRow("Раунды:", self.p_rounds)
        self.params_form.addRow("S-box:", self.p_sbox)
        layout.addWidget(params_box)

        result_box = QGroupBox("Результат")
        result_layout = QVBoxLayout(result_box)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(QLabel("Восстановленный текст:"))
        result_layout.addWidget(self.result_text)

        self.view_rounds_btn = QPushButton("Посмотреть раунды дешифрования →")
        self.view_rounds_btn.setObjectName("secondary")
        self.view_rounds_btn.clicked.connect(self.request_switch_to_round_tab.emit)
        result_layout.addWidget(self.view_rounds_btn)

        layout.addWidget(result_box)
        layout.addStretch()

    def _on_load_last(self):
        if self.app_state.last_container:
            self.ct_input.setPlainText(self.app_state.last_container)
        else:
            QMessageBox.information(self, "Нет данных",
                                     "Ещё не было выполнено ни одно шифрование в этом сеансе.")

    def _on_decrypt(self):
        container_str = self.ct_input.toPlainText().strip()
        if not container_str:
            QMessageBox.warning(self, "Пусто", "Вставьте контейнер шифротекста")
            return

        try:
            payload = parse_container(container_str)
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка разбора", str(e))
            return

        mode = payload["mode"]
        cipher_mode = payload["cipher_mode"]
        block_bits = payload["block_bits"]
        key_bits = payload["key_bits"]
        rounds = payload["rounds"]
        sbox = payload["sbox"]
        linear_transform = payload.get("linear_transform", "aes_like")
        iv_hex = payload.get("iv_hex", "")
        original_len = payload["original_length_bytes"]
        ciphertext = bytes.fromhex(payload["ciphertext_hex"])

        self.p_mode.setText(f"{mode} ({'стандарт' if mode == 'AES' else 'НЕ стандарт AES'})")
        self.p_block.setText(f"{block_bits} бит")
        self.p_key.setText(f"{key_bits} бит")
        self.p_rounds.setText(str(rounds))
        self.p_sbox.setText(payload.get("sbox_meta", {}).get("method", "?"))

        key_info = self.app_state.key_info
        if key_info is None or key_info.bits != key_bits:
            QMessageBox.warning(
                self, "Нужен ключ",
                f"Для дешифрования нужен ключ размером {key_bits} бит. "
                f"Перейдите на вкладку 'Ключ' и введите/сгенерируйте тот же "
                f"ключ, который использовался при шифровании (например, ту "
                f"же фразу), либо любой ключ такого размера для демонстрации."
            )
            return

        block_bytes = block_bits // 8
        blocks = split_into_blocks(ciphertext, block_bytes)
        iv = bytes.fromhex(iv_hex) if iv_hex else None

        try:
            if mode == "AES":
                cipher = AESCipher(key_info.key_bytes, key_bits, sbox=sbox)
                pt_blocks, traces = cipher.decrypt_blocks(blocks, mode=cipher_mode, iv=iv)
            else:
                cipher = ExperimentalCipher(key_info.key_bytes, block_bits, key_bits, rounds,
                                             sbox=sbox, linear_transform=linear_transform)
                pt_blocks = []
                traces = []
                prev = iv
                for block in blocks:
                    pt, tr = cipher.decrypt_block(block)
                    if cipher_mode == "CBC" and prev is not None:
                        pt = bytes(a ^ b for a, b in zip(pt, prev))
                    pt_blocks.append(pt)
                    traces.append(tr)
                    if cipher_mode == "CBC":
                        prev = block
        except Exception as e:
            QMessageBox.critical(self, "Ошибка дешифрования", str(e))
            return

        padded_plain = b"".join(pt_blocks)
        try:
            original = unpad_zero_bytes(padded_plain, original_len)
            text = bytes_to_text(original, errors="strict")
        except Exception:
            text = f"(не удалось декодировать как UTF-8 текст; HEX: {bytes_to_hex(padded_plain[:original_len])})"

        self.app_state.last_operation = "decrypt"
        self.app_state.last_block_traces = traces

        self.result_text.setPlainText(text)
        self.decryption_done.emit()
