# -*- coding: utf-8 -*-
"""
app/gui/round_view.py

Вкладка "Раунды": интерактивная временная шкала всех шагов последнего
шифрования/дешифрования. Каждый шаг кликабелен - при выборе показываются
подробности (матрица состояния, HEX, BIN, использованный раундовый ключ,
визуализация XOR).
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QTreeWidget,
    QTreeWidgetItem, QComboBox, QPlainTextEdit, QSplitter
)
from PySide6.QtCore import Qt

from app.visualization.matrix_view import MatrixWidget
from app.visualization.binary_view import format_xor_visualization
from app.crypto.encoding import bytes_to_hex, bytes_to_bin


STAGE_LABELS_RU = {
    "InitialState": "Исходное состояние",
    "AddRoundKey": "AddRoundKey (XOR с раундовым ключом)",
    "SubBytes": "SubBytes (замена через S-box)",
    "ShiftRows": "ShiftRows (сдвиг строк)",
    "MixColumns": "MixColumns (перемешивание столбцов)",
    "Ciphertext": "Итоговый шифротекст",
    "InitialState(Ciphertext)": "Исходное состояние (шифротекст)",
    "InvAddRoundKey": "Inverse AddRoundKey",
    "InvSubBytes": "Inverse SubBytes",
    "InvShiftRows": "Inverse ShiftRows",
    "InvMixColumns": "Inverse MixColumns",
    "PlaintextBlock": "Восстановленный открытый блок",
}


class RoundView(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Визуализация раундов")
        title.setObjectName("heading")
        layout.addWidget(title)
        sub = QLabel("Временная шкала всех шагов последнего шифрования/дешифрования. "
                      "Нажмите на шаг, чтобы увидеть подробности.")
        sub.setObjectName("subheading")
        sub.setWordWrap(True)
        layout.addWidget(sub)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Блок:"))
        self.block_combo = QComboBox()
        self.block_combo.currentIndexChanged.connect(self._on_block_changed)
        selector_row.addWidget(self.block_combo)
        selector_row.addStretch()
        layout.addLayout(selector_row)

        splitter = QSplitter(Qt.Horizontal)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Шаг"])
        self.tree.itemClicked.connect(self._on_item_clicked)
        splitter.addWidget(self.tree)

        detail_box = QGroupBox("Детали шага")
        detail_layout = QVBoxLayout(detail_box)

        self.matrix_widget = MatrixWidget()
        detail_layout.addWidget(self.matrix_widget)

        self.hex_view = QPlainTextEdit()
        self.hex_view.setReadOnly(True)
        self.hex_view.setMaximumHeight(60)
        detail_layout.addWidget(QLabel("HEX:"))
        detail_layout.addWidget(self.hex_view)

        self.xor_view = QPlainTextEdit()
        self.xor_view.setReadOnly(True)
        self.xor_view.setMaximumHeight(110)
        self.xor_view.setStyleSheet("font-family: Consolas, monospace;")
        detail_layout.addWidget(QLabel("Побитовая визуализация (если применимо):"))
        detail_layout.addWidget(self.xor_view)

        self.note_label = QLabel("")
        self.note_label.setObjectName("warning")
        self.note_label.setWordWrap(True)
        self.note_label.hide()
        detail_layout.addWidget(self.note_label)

        detail_layout.addStretch()
        splitter.addWidget(detail_box)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

    def refresh_from_state(self):
        """Пересобирает дерево на основе app_state.last_block_traces."""
        self.block_combo.blockSignals(True)
        self.block_combo.clear()
        n_blocks = len(self.app_state.last_block_traces)
        for i in range(n_blocks):
            self.block_combo.addItem(f"Блок {i + 1}", i)
        self.block_combo.blockSignals(False)
        if n_blocks:
            self.block_combo.setCurrentIndex(0)
            self._populate_tree(0)

    def _on_block_changed(self, idx):
        if idx >= 0:
            self._populate_tree(idx)

    def _populate_tree(self, block_index: int):
        self.tree.clear()
        if block_index >= len(self.app_state.last_block_traces):
            return
        trace = self.app_state.last_block_traces[block_index]

        current_round = None
        round_item = None
        for i, step in enumerate(trace):
            rnd = step.get("round")
            stage = step.get("stage", "")
            if rnd != current_round:
                current_round = rnd
                label = "Round 0 (начальный)" if rnd == 0 else f"Round {rnd}"
                round_item = QTreeWidgetItem([label])
                self.tree.addTopLevelItem(round_item)
                round_item.setExpanded(True)

            stage_label = STAGE_LABELS_RU.get(stage.split("(")[0], stage)
            child = QTreeWidgetItem([stage_label])
            child.setData(0, Qt.UserRole, i)
            round_item.addChild(child)

        if trace:
            first_child = self.tree.topLevelItem(0).child(0) if self.tree.topLevelItemCount() else None
            if first_child:
                self.tree.setCurrentItem(first_child)
                self._show_step_details(block_index, 0)

    def _on_item_clicked(self, item, column):
        step_index = item.data(0, Qt.UserRole)
        if step_index is None:
            return
        block_index = self.block_combo.currentData()
        self._show_step_details(block_index, step_index)

    def _show_step_details(self, block_index: int, step_index: int):
        trace = self.app_state.last_block_traces[block_index]
        step = trace[step_index]

        self.note_label.hide()
        if "note" in step:
            self.note_label.setText(step["note"])
            self.note_label.show()

        if "state" in step:
            state = step["state"]
            prev_state = trace[step_index - 1]["state"] if step_index > 0 and "state" in trace[step_index - 1] else None
            self.matrix_widget.set_state(state, highlight_changed_from=prev_state)
            flat = bytes(state[r][c] for c in range(len(state[0])) for r in range(4))
            self.hex_view.setPlainText(bytes_to_hex(flat))

            if step.get("stage") == "AddRoundKey" or step.get("stage") == "InvAddRoundKey":
                rk = step.get("round_key")
                if rk and step_index > 0:
                    prev = trace[step_index - 1].get("state")
                    if prev:
                        prev_flat = bytes(prev[r][c] for c in range(len(prev[0])) for r in range(4))
                        self.xor_view.setPlainText(format_xor_visualization(prev_flat, rk))
                    else:
                        self.xor_view.clear()
                else:
                    self.xor_view.clear()
            else:
                self.xor_view.clear()

        elif "data" in step:
            # Экспериментальный шифр - данные хранятся плоским байтовым массивом
            data = step["data"]
            cols = max(1, len(data) // 4)
            state = [[data[r + 4 * c] if r + 4 * c < len(data) else 0 for c in range(cols)] for r in range(4)]
            self.matrix_widget.set_state(state)
            self.hex_view.setPlainText(bytes_to_hex(data))

            if "round_key" in step:
                rk = step["round_key"]
                prev_data = trace[step_index - 1].get("data") if step_index > 0 else None
                if prev_data:
                    self.xor_view.setPlainText(format_xor_visualization(prev_data, rk))
                else:
                    self.xor_view.clear()
            else:
                self.xor_view.clear()
