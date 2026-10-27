# -*- coding: utf-8 -*-
"""
app/gui/key_view.py

Вкладка "Ключ": генерация ключа четырьмя способами (фраза, слово,
бинарное значение, случайный), с отображением ключа как TEXT / HEX / BIN
и количества бит.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit,
    QPushButton, QComboBox, QPlainTextEdit, QRadioButton, QButtonGroup,
    QMessageBox, QFormLayout
)
from PySide6.QtCore import Signal

from app.crypto import key_generator as kg


class KeyView(QWidget):
    key_generated = Signal()

    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build_ui()
        self._refresh_key_size_options()
        self._on_generate_random()  # ключ по умолчанию, чтобы приложение сразу работало

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Генерация ключа")
        title.setObjectName("heading")
        layout.addWidget(title)
        sub = QLabel("Ключ можно получить из фразы/слова (через SHA-256), "
                      "ввести напрямую в бинарном виде или сгенерировать случайно.")
        sub.setObjectName("subheading")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        # Выбор размера ключа
        size_box = QGroupBox("Размер ключа")
        size_layout = QHBoxLayout(size_box)
        self.key_size_combo = QComboBox()
        size_layout.addWidget(QLabel("Размер ключа:"))
        size_layout.addWidget(self.key_size_combo)
        size_layout.addStretch()
        layout.addWidget(size_box)

        # Методы генерации
        method_box = QGroupBox("Способ генерации")
        method_layout = QVBoxLayout(method_box)

        self.method_group = QButtonGroup(self)
        self.rb_phrase = QRadioButton("Фраза (SHA-256)")
        self.rb_word = QRadioButton("Слово (SHA-256)")
        self.rb_binary = QRadioButton("Бинарное значение (ввод вручную)")
        self.rb_random = QRadioButton("Случайный ключ")
        self.rb_random.setChecked(True)
        for i, rb in enumerate([self.rb_phrase, self.rb_word, self.rb_binary, self.rb_random]):
            self.method_group.addButton(rb, i)
            method_layout.addWidget(rb)

        form = QFormLayout()
        self.phrase_input = QLineEdit()
        self.phrase_input.setPlaceholderText("Например: Мой секретный ключ 2026")
        form.addRow("Фраза:", self.phrase_input)

        self.word_input = QLineEdit()
        self.word_input.setPlaceholderText("Например: криптография")
        form.addRow("Слово:", self.word_input)

        self.binary_input = QLineEdit()
        self.binary_input.setPlaceholderText("Например: 0101010101010101...")
        form.addRow("Бинарное значение:", self.binary_input)

        method_layout.addLayout(form)

        self.generate_btn = QPushButton("Сгенерировать новый ключ")
        self.generate_btn.clicked.connect(self._on_generate_clicked)
        method_layout.addWidget(self.generate_btn)

        layout.addWidget(method_box)

        # Результат
        result_box = QGroupBox("Текущий ключ")
        result_layout = QFormLayout(result_box)
        self.bits_label = QLabel("-")
        self.text_label = QLabel("-")
        self.text_label.setWordWrap(True)
        self.hex_display = QPlainTextEdit()
        self.hex_display.setReadOnly(True)
        self.hex_display.setMaximumHeight(60)
        self.bin_display = QPlainTextEdit()
        self.bin_display.setReadOnly(True)
        self.bin_display.setMaximumHeight(80)

        result_layout.addRow("Размер (бит):", self.bits_label)
        result_layout.addRow("Как текст (если применимо):", self.text_label)
        result_layout.addRow("HEX:", self.hex_display)
        result_layout.addRow("BIN:", self.bin_display)

        layout.addWidget(result_box)
        layout.addStretch()

    def _refresh_key_size_options(self):
        self.key_size_combo.clear()
        if self.app_state.is_standard_aes():
            sizes = [128, 192, 256]
        else:
            sizes = [64, 128, 192, 256]
        for s in sizes:
            self.key_size_combo.addItem(f"{s} бит", s)
        # выбрать текущий размер из состояния, если возможен
        idx = self.key_size_combo.findData(self.app_state.key_bits)
        self.key_size_combo.setCurrentIndex(idx if idx >= 0 else 0)

    def sync_with_mode(self):
        """Вызывается извне при смене режима AES/Experimental."""
        self._refresh_key_size_options()

    def _current_bits(self) -> int:
        return self.key_size_combo.currentData()

    def _on_generate_clicked(self):
        bits = self._current_bits()
        try:
            if self.rb_phrase.isChecked():
                text = self.phrase_input.text()
                if not text:
                    raise ValueError("Введите фразу")
                info = kg.key_from_phrase(text, bits)
            elif self.rb_word.isChecked():
                text = self.word_input.text()
                if not text:
                    raise ValueError("Введите слово")
                info = kg.key_from_word(text, bits)
            elif self.rb_binary.isChecked():
                info = kg.key_from_binary_string(self.binary_input.text(), bits)
            else:
                info = kg.key_random(bits)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка генерации ключа", str(e))
            return

        self.app_state.key_info = info
        self.app_state.key_bits = bits
        self._update_display(info)

        warn = kg.key_size_warning(bits)
        if warn:
            QMessageBox.information(self, "Внимание", warn)

        self.key_generated.emit()

    def _on_generate_random(self):
        self.rb_random.setChecked(True)
        self._on_generate_clicked()

    def _update_display(self, info: kg.KeyInfo):
        self.bits_label.setText(str(info.bits))
        text_repr = info.as_text_if_printable
        self.text_label.setText(text_repr if text_repr else "(не отображается как текст)")
        self.hex_display.setPlainText(info.hex)
        self.bin_display.setPlainText(info.bin)
