# -*- coding: utf-8 -*-
"""
app/visualization/matrix_view.py

Виджет для отображения состояния AES (или экспериментального шифра) в
виде матрицы 4xN байт, где N = число столбцов (4 для стандартного AES-128
блока). При наведении на ячейку показывается всплывающая подсказка с
дополнительной информацией (позиция, значение в HEX/DEC/BIN).
"""
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor


class MatrixWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionMode(QTableWidget.NoSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setFixedHeight(180)

    def set_state(self, state, highlight_changed_from=None, byte_labels=None):
        """
        state: список из 4 строк (list[list[int]]), как в crypto/aes.py
        highlight_changed_from: если задан (тот же формат), ячейки с иным
            значением подсвечиваются, чтобы визуально показать, что
            изменилось на этом шаге.
        """
        rows = len(state)
        cols = len(state[0]) if rows else 0
        self.setRowCount(rows)
        self.setColumnCount(cols)
        self.setHorizontalHeaderLabels([f"col {c}" for c in range(cols)])
        self.setVerticalHeaderLabels([f"row {r}" for r in range(rows)])

        for r in range(rows):
            for c in range(cols):
                value = state[r][c]
                item = QTableWidgetItem(f"{value:02X}")
                item.setTextAlignment(Qt.AlignCenter)
                tooltip = (f"Позиция: строка {r}, столбец {c}\n"
                           f"HEX: {value:02X}\n"
                           f"DEC: {value}\n"
                           f"BIN: {value:08b}")
                item.setToolTip(tooltip)
                if highlight_changed_from is not None:
                    old = highlight_changed_from[r][c]
                    if old != value:
                        item.setBackground(QColor(74, 102, 255, 90))
                self.setItem(r, c, item)
