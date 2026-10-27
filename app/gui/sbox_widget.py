# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush
from app.crypto.sbox import generate_sbox


class SBoxWidget(QWidget):
    sbox_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sbox = generate_sbox()
        self.highlight_values = []
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.generate_btn = QPushButton("Сгенерировать S-box")
        self.generate_btn.clicked.connect(self.regenerate)
        row.addWidget(self.generate_btn)
        self.note = QLabel("Локальная алгоритмическая генерация: GF(2^8) → мультипликативная инверсия → аффинное преобразование")
        self.note.setWordWrap(True)
        row.addWidget(self.note, 1)
        layout.addLayout(row)
        self.table = QTableWidget(16, 16)
        self.table.setHorizontalHeaderLabels([f"{i:X}" for i in range(16)])
        self.table.setVerticalHeaderLabels([f"{i:X}" for i in range(16)])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        self.render()

    def regenerate(self):
        self.sbox = generate_sbox()
        self.render()
        self.sbox_changed.emit(list(self.sbox))

    def set_highlights(self, input_values):
        self.highlight_values = list(input_values or [])
        self.render()

    def render(self):
        for r in range(16):
            for c in range(16):
                idx = r * 16 + c
                item = QTableWidgetItem(f"{self.sbox[idx]:02X}")
                item.setTextAlignment(Qt.AlignCenter)
                if idx in self.highlight_values:
                    item.setBackground(QBrush(QColor("#FFD54F")))
                    item.setForeground(QBrush(QColor("#111111")))
                self.table.setItem(r, c, item)
