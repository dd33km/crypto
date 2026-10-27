# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QLineEdit, QComboBox, QPushButton, QTabWidget, QPlainTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QSplitter,
    QScrollArea, QApplication
)

from app.crypto.feistel import (
    encrypt, decrypt,
    build_teaching_container, parse_teaching_container, remove_original_padding,
)
from app.crypto.encoding import text_to_bytes, bytes_to_bin
from app.crypto.sbox import generate_sbox
from app.gui.sbox_widget import SBoxWidget
from app.visualization.feistel_diagram import FeistelDiagramWidget


class FeistelTab(QWidget):
    """Учебная сеть Фейстеля. AES-файлы этим виджетом не изменяются."""

    def __init__(self, app_state, ui_config, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self.cfg = ui_config.get("feistel", {})
        self.sbox = generate_sbox()

        self.encrypt_result = None
        self.decrypt_result = None
        self.diagram_source = None
        self.diagram_round_index = 0
        self._auto_decrypt_busy = False

        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 6, 8, 8)
        root.setSpacing(8)

        head = QHBoxLayout()
        title_col = QVBoxLayout()
        title = QLabel("Сеть Фейстеля")
        title.setObjectName("heading")
        subtitle = QLabel("Учебная визуализация: функция F работает с левым блоком L")
        subtitle.setObjectName("subheading")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        head.addLayout(title_col)
        head.addStretch(1)
        badge = QLabel("L → F(L,K) → XOR с R")
        badge.setObjectName("feistelBadge")
        head.addWidget(badge)
        root.addLayout(head)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("feistelInnerTabs")
        root.addWidget(self.tabs, 1)

        self.encrypt_page = QWidget()
        self.decrypt_page = QWidget()
        self.sbox_page = QWidget()
        self.diagram_page = QWidget()

        self.tabs.addTab(self.encrypt_page, "Шифровка")
        self.tabs.addTab(self.decrypt_page, "Расшифровка")
        self.tabs.addTab(self.sbox_page, "S-box")
        self.tabs.addTab(self.diagram_page, "Диаграмма")

        self._build_encrypt_page()
        self._build_decrypt_page()
        self._build_sbox()
        self._build_diagram()

    # ------------------------------------------------------------------
    # ШИФРОВКА
    # ------------------------------------------------------------------
    def _build_encrypt_page(self):
        outer = QVBoxLayout(self.encrypt_page)
        outer.setContentsMargins(8, 10, 8, 8)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        outer.addWidget(scroll)

        body = QWidget()
        scroll.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(4, 2, 4, 8)
        layout.setSpacing(10)

        input_box = QGroupBox("Ввод данных")
        form = QFormLayout(input_box)

        self.enc_mode = QComboBox()
        self.enc_mode.addItem("Текст / фраза", "text")
        self.enc_mode.addItem("Бинарный ввод", "binary")

        self.enc_source = QPlainTextEdit()
        self.enc_source.setMaximumHeight(90)
        self.enc_source.setPlaceholderText("Например: Привет, это сеть Фейстеля")

        self.enc_key_mode = QComboBox()
        self.enc_key_mode.addItem("Текст / фраза", "text")
        self.enc_key_mode.addItem("Бинарный ввод", "binary")
        self.enc_key = QLineEdit()
        self.enc_key.setPlaceholderText("Например: учебный ключ")

        self.enc_rounds = QComboBox()
        for n in range(1, 11):
            self.enc_rounds.addItem(str(n), n)
        self.enc_rounds.setCurrentIndex(3)

        form.addRow("Формат:", self.enc_mode)
        form.addRow("Исходная фраза / блок:", self.enc_source)
        form.addRow("Формат ключа:", self.enc_key_mode)
        form.addRow("Ключ:", self.enc_key)
        form.addRow("Количество раундов:", self.enc_rounds)
        layout.addWidget(input_box)

        buttons = QHBoxLayout()
        run = QPushButton("Шифровать")
        run.clicked.connect(self._run_encrypt)
        to_diagram = QPushButton("Открыть диаграмму")
        to_diagram.setObjectName("secondary")
        to_diagram.clicked.connect(lambda: self._open_diagram_for(False))
        buttons.addWidget(run)
        buttons.addWidget(to_diagram)
        buttons.addStretch(1)
        layout.addLayout(buttons)

        splitter = QSplitter(Qt.Horizontal)

        source_box = QGroupBox("Преобразование входа")
        sl = QVBoxLayout(source_box)
        self.enc_details = QPlainTextEdit()
        self.enc_details.setReadOnly(True)
        self.enc_details.setMinimumHeight(170)
        self.enc_details.setStyleSheet("font-family: Consolas, monospace;")
        sl.addWidget(self.enc_details)
        splitter.addWidget(source_box)

        result_box = QGroupBox("Результат шифрования")
        rl = QVBoxLayout(result_box)
        rl.addWidget(QLabel("Шифротекст (Binary):"))
        self.enc_result = QPlainTextEdit()
        self.enc_result.setReadOnly(True)
        self.enc_result.setMaximumHeight(105)
        self.enc_result.setStyleSheet("font-family: Consolas, monospace;")
        rl.addWidget(self.enc_result)

        rl.addWidget(QLabel("Контейнер Feistel — скопируйте его целиком во вкладку «Расшифровка»:"))
        self.enc_container = QPlainTextEdit()
        self.enc_container.setReadOnly(True)
        self.enc_container.setMaximumHeight(100)
        self.enc_container.setStyleSheet("font-family: Consolas, monospace;")
        rl.addWidget(self.enc_container)

        copy_row = QHBoxLayout()
        self.enc_copy_btn = QPushButton("Скопировать контейнер")
        self.enc_copy_btn.setObjectName("secondary")
        self.enc_copy_btn.clicked.connect(self._copy_feistel_container)
        copy_row.addWidget(self.enc_copy_btn)
        copy_row.addStretch(1)
        rl.addLayout(copy_row)

        splitter.addWidget(result_box)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)

        self.enc_table = self._create_round_table()
        layout.addWidget(self._rounds_box(self.enc_table, decrypting=False))

        self.enc_mode.currentIndexChanged.connect(self._update_encrypt_placeholders)
        self.enc_key_mode.currentIndexChanged.connect(self._update_encrypt_placeholders)

    def _update_encrypt_placeholders(self):
        self.enc_source.setPlaceholderText(
            "Например: 010011110101..." if self.enc_mode.currentData() == "binary"
            else "Например: Привет, это сеть Фейстеля"
        )
        self.enc_key.setPlaceholderText(
            "Например: 011010010101..." if self.enc_key_mode.currentData() == "binary"
            else "Например: учебный ключ"
        )

    # ------------------------------------------------------------------
    # РАСШИФРОВКА: один контейнер, без повторного ввода ключа/раундов
    # ------------------------------------------------------------------
    def _build_decrypt_page(self):
        outer = QVBoxLayout(self.decrypt_page)
        outer.setContentsMargins(8, 10, 8, 8)
        outer.setSpacing(10)

        input_box = QGroupBox("Контейнер шифротекста")
        il = QVBoxLayout(input_box)
        hint = QLabel(
            "Вставьте контейнер, скопированный после шифрования. "
            "Ключ, число раундов, S-box и padding будут извлечены автоматически."
        )
        hint.setWordWrap(True)
        hint.setObjectName("subheading")
        il.addWidget(hint)

        self.dec_container = QPlainTextEdit()
        self.dec_container.setPlaceholderText("Вставьте сюда контейнер Feistel — расшифровка запустится автоматически")
        self.dec_container.setMinimumHeight(115)
        self.dec_container.setStyleSheet("font-family: Consolas, monospace;")
        il.addWidget(self.dec_container)

        btns = QHBoxLayout()
        paste = QPushButton("Вставить из буфера")
        paste.setObjectName("secondary")
        paste.clicked.connect(self._paste_feistel_container)
        load_last = QPushButton("Загрузить последний")
        load_last.setObjectName("secondary")
        load_last.clicked.connect(self._load_last_feistel_container)
        run = QPushButton("Расшифровать")
        run.clicked.connect(lambda: self._decrypt_from_container(show_errors=True))
        btns.addWidget(paste)
        btns.addWidget(load_last)
        btns.addWidget(run)
        btns.addStretch(1)
        il.addLayout(btns)
        outer.addWidget(input_box)

        status_box = QGroupBox("Параметры из контейнера")
        sf = QFormLayout(status_box)
        self.dec_status = QLabel("Вставьте контейнер")
        self.dec_status.setWordWrap(True)
        self.dec_rounds_info = QLabel("—")
        self.dec_key_info = QLabel("—")
        sf.addRow("Статус:", self.dec_status)
        sf.addRow("Раунды:", self.dec_rounds_info)
        sf.addRow("Ключ:", self.dec_key_info)
        outer.addWidget(status_box)

        result_box = QGroupBox("Результат")
        rl = QVBoxLayout(result_box)
        self.dec_result = QPlainTextEdit()
        self.dec_result.setReadOnly(True)
        self.dec_result.setMinimumHeight(150)
        rl.addWidget(self.dec_result)
        to_diagram = QPushButton("Открыть диаграмму расшифровки")
        to_diagram.setObjectName("secondary")
        to_diagram.clicked.connect(lambda: self._open_diagram_for(True))
        rl.addWidget(to_diagram)
        outer.addWidget(result_box)

        self.dec_table = self._create_round_table()
        outer.addWidget(self._rounds_box(self.dec_table, decrypting=True), 1)

        # Обычная вставка Ctrl+V вызывает textChanged один раз уже с готовым
        # содержимым. Некорректный/недописанный текст молча игнорируется.
        self.dec_container.textChanged.connect(self._try_auto_decrypt)

    # ------------------------------------------------------------------
    @staticmethod
    def _input_to_bits(value: str, mode: str, field_name: str):
        if mode == "text":
            if not value:
                raise ValueError(f"Введите {field_name}")
            raw = text_to_bytes(value)
            return bytes_to_bin(raw, spaced=False), value
        cleaned = "".join(value.split())
        if not cleaned:
            raise ValueError(f"Введите {field_name}")
        if any(ch not in "01" for ch in cleaned):
            raise ValueError(f"{field_name}: в бинарном режиме разрешены только 0 и 1")
        return cleaned, None

    def _run_encrypt(self):
        try:
            source_value = self.enc_source.toPlainText()
            block_bits, block_text = self._input_to_bits(
                source_value, self.enc_mode.currentData(), "исходные данные"
            )
            key_bits, key_text = self._input_to_bits(
                self.enc_key.text(), self.enc_key_mode.currentData(), "ключ"
            )
            data = encrypt(block_bits, key_bits, self.enc_rounds.currentData(), self.sbox)
            data["input_text"] = block_text
            data["key_text"] = key_text
            data["input_binary"] = block_bits
            data["key_binary"] = key_bits

            bp = data["block_padding"]
            container = build_teaching_container(
                ciphertext_binary=data["result"],
                key_binary=key_bits,
                rounds=self.enc_rounds.currentData(),
                input_mode=self.enc_mode.currentData(),
                original_bit_length=len(block_bits),
                padding_left=bp["left"],
                padding_right=bp["right"],
                sbox=self.sbox,
            )
            data["container"] = container
        except Exception as exc:
            QMessageBox.warning(self, "Ошибка", str(exc))
            return

        self.encrypt_result = data
        self.app_state.feistel_last_container = container
        self.diagram_source = data
        self.diagram_round_index = 0
        self._render_encrypt(data)
        self._refresh_diagram()

    def _render_encrypt(self, data: dict):
        bp = data["block_padding"]
        kp = data["key_padding"]
        lines = []
        if data.get("input_text") is not None:
            lines += ["Введённый текст:", data["input_text"], "", "Текст → Binary:", data["input_binary"], ""]
        else:
            lines += ["Введённый Binary:", data["input_binary"], ""]
        if data.get("key_text") is not None:
            lines += ["Ключ-текст:", data["key_text"], "", "Ключ → Binary:", data["key_binary"], ""]
        else:
            lines += ["Ключ Binary:", data["key_binary"], ""]
        lines += [
            f"Размер рабочего блока: {data['block_size']} бит (автоматически)",
            f"Половина: {data['half_size']} бит", "",
            "Блок до padding:", bp["before"],
            "Блок после padding:", bp["after"],
            f"Нули: слева {bp['left']}, справа {bp['right']}", "",
            "Ключ до padding:", kp["before"],
            "Ключ после padding:", kp["after"],
            f"Нули: слева {kp['left']}, справа {kp['right']}",
        ]
        self.enc_details.setPlainText("\n".join(lines))
        self.enc_result.setPlainText(data["result"])
        self.enc_container.setPlainText(data["container"])
        self._fill_round_table(self.enc_table, data)

    def _copy_feistel_container(self):
        value = self.enc_container.toPlainText().strip()
        if not value:
            QMessageBox.information(self, "Нет данных", "Сначала выполните шифрование.")
            return
        QApplication.clipboard().setText(value)
        self.enc_copy_btn.setText("Скопировано ✓")

    def _paste_feistel_container(self):
        self.dec_container.setPlainText(QApplication.clipboard().text().strip())

    def _load_last_feistel_container(self):
        value = self.app_state.feistel_last_container
        if not value:
            QMessageBox.information(self, "Нет данных", "В этом сеансе ещё не было шифрования Feistel.")
            return
        self.dec_container.setPlainText(value)

    def _try_auto_decrypt(self):
        if self._auto_decrypt_busy:
            return
        text = self.dec_container.toPlainText().strip()
        if not text:
            self.dec_status.setText("Вставьте контейнер")
            return
        try:
            parse_teaching_container(text)
        except Exception:
            # При наборе текста руками не засыпаем пользователя окнами ошибок.
            return
        self._decrypt_from_container(show_errors=False)

    def _decrypt_from_container(self, show_errors: bool = True):
        if self._auto_decrypt_busy:
            return
        self._auto_decrypt_busy = True
        try:
            payload = parse_teaching_container(self.dec_container.toPlainText())
            sbox = payload["sbox"]
            data = decrypt(
                payload["ciphertext_binary"],
                payload["key_binary"],
                payload["rounds"],
                sbox,
            )
            restored_bits = remove_original_padding(
                data["result"],
                original_bit_length=payload["original_bit_length"],
                padding_left=payload["padding_left"],
            )
            restored_text = None
            if payload.get("input_mode") == "text" and len(restored_bits) % 8 == 0:
                try:
                    raw = bytes(int(restored_bits[i:i+8], 2) for i in range(0, len(restored_bits), 8))
                    restored_text = raw.decode("utf-8")
                except Exception:
                    restored_text = None

            data["restored_bits"] = restored_bits
            data["restored_text"] = restored_text
            data["container_payload"] = payload
            self.decrypt_result = data
            self.diagram_source = data
            self.diagram_round_index = 0

            # Использованная при шифровании S-box также восстанавливается из контейнера.
            self.sbox = list(sbox)
            self.sbox_widget.sbox = list(sbox)
            self.sbox_widget.render()

            self.dec_status.setText("Контейнер распознан. Расшифровка выполнена автоматически ✓")
            self.dec_rounds_info.setText(str(payload["rounds"]))
            key_preview = payload["key_binary"]
            if len(key_preview) > 64:
                key_preview = key_preview[:64] + "…"
            self.dec_key_info.setText(key_preview + " (из контейнера)")

            result_lines = []
            if restored_text is not None:
                result_lines += ["Восстановленный текст:", restored_text, ""]
            result_lines += ["Восстановленный Binary:", restored_bits]
            self.dec_result.setPlainText("\n".join(result_lines))
            self._fill_round_table(self.dec_table, data)
            self._refresh_diagram()
        except Exception as exc:
            if show_errors:
                QMessageBox.warning(self, "Ошибка расшифровки", str(exc))
        finally:
            self._auto_decrypt_busy = False

    # ------------------------------------------------------------------
    def _create_round_table(self):
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels(["Раунд", "L", "R", "K", "F(L,K)", "После раунда"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setMinimumHeight(250)
        return table

    def _rounds_box(self, table, decrypting: bool):
        box = QGroupBox("Раунды")
        layout = QVBoxLayout(box)
        table.cellDoubleClicked.connect(lambda row, _col: self._open_table_round(decrypting, row))
        layout.addWidget(table)
        hint = QLabel("Дважды нажмите на строку раунда, чтобы открыть его блок-схему.")
        hint.setObjectName("subheading")
        layout.addWidget(hint)
        return box

    @staticmethod
    def _fill_round_table(table: QTableWidget, data: dict):
        table.setRowCount(0)
        for row, step in enumerate(data["rounds"]):
            table.insertRow(row)
            values = [
                str(step["round"]), step["L_in"], step["R_in"], step["K"],
                step["F_out"], f"L={step['L_out']}\nR={step['R_out']}",
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

    # ------------------------------------------------------------------
    def _build_sbox(self):
        layout = QVBoxLayout(self.sbox_page)
        layout.setContentsMargins(8, 10, 8, 8)
        note = QLabel("S-box генерируется локально. Никаких сайтов, WebView или сетевых запросов.")
        note.setObjectName("subheading")
        layout.addWidget(note)
        self.sbox_widget = SBoxWidget()
        self.sbox_widget.sbox = list(self.sbox)
        self.sbox_widget.render()
        self.sbox_widget.sbox_changed.connect(self._sbox_changed)
        layout.addWidget(self.sbox_widget, 1)
        self.sbox_detail = QPlainTextEdit()
        self.sbox_detail.setReadOnly(True)
        self.sbox_detail.setMaximumHeight(130)
        self.sbox_detail.setPlaceholderText("После расчёта раунда здесь будут показаны использованные ячейки S-box.")
        self.sbox_detail.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.sbox_detail)

    def _sbox_changed(self, values):
        self.sbox = list(values)
        # Пересчитываем только Feistel. AES не затрагивается.
        if self.encrypt_result:
            self._run_encrypt()

    # ------------------------------------------------------------------
    def _build_diagram(self):
        layout = QVBoxLayout(self.diagram_page)
        layout.setContentsMargins(8, 10, 8, 8)
        layout.setSpacing(8)

        self.diagram = FeistelDiagramWidget()
        self.diagram.set_theme(self.app_state.theme == "dark")
        layout.addWidget(self.diagram, 1)

        nav = QHBoxLayout()
        self.prev_round_btn = QPushButton("←")
        self.prev_round_btn.setObjectName("secondary")
        self.prev_round_btn.setFixedWidth(58)
        self.prev_round_btn.clicked.connect(lambda: self._change_round(-1))
        nav.addWidget(self.prev_round_btn)

        nav.addStretch(1)
        self.round_label = QLabel("Раунд —")
        self.round_label.setObjectName("roundNavigator")
        self.round_label.setAlignment(Qt.AlignCenter)
        nav.addWidget(self.round_label)
        nav.addStretch(1)

        self.next_round_btn = QPushButton("→")
        self.next_round_btn.setFixedWidth(58)
        self.next_round_btn.clicked.connect(lambda: self._change_round(1))
        nav.addWidget(self.next_round_btn)
        layout.addLayout(nav)

        self.diagram_detail = QPlainTextEdit()
        self.diagram_detail.setReadOnly(True)
        self.diagram_detail.setMaximumHeight(150)
        self.diagram_detail.setStyleSheet("font-family: Consolas, monospace;")
        layout.addWidget(self.diagram_detail)

    def _open_diagram_for(self, decrypting: bool):
        data = self.decrypt_result if decrypting else self.encrypt_result
        if not data:
            QMessageBox.information(self, "Диаграмма", "Сначала выполните операцию.")
            return
        self.diagram_source = data
        self.diagram_round_index = 0
        self.tabs.setCurrentWidget(self.diagram_page)
        self._refresh_diagram()

    def _open_table_round(self, decrypting: bool, row: int):
        data = self.decrypt_result if decrypting else self.encrypt_result
        if not data or not (0 <= row < len(data["rounds"])):
            return
        self.diagram_source = data
        self.diagram_round_index = row
        self.tabs.setCurrentWidget(self.diagram_page)
        self._refresh_diagram()

    def _change_round(self, delta: int):
        if not self.diagram_source or not self.diagram_source.get("rounds"):
            return
        count = len(self.diagram_source["rounds"])
        self.diagram_round_index = max(0, min(count - 1, self.diagram_round_index + delta))
        self._refresh_diagram()

    def _refresh_diagram(self):
        rounds = (self.diagram_source or {}).get("rounds", [])
        if not rounds:
            self.diagram.clear()
            self.round_label.setText("Раунд —")
            self.prev_round_btn.setEnabled(False)
            self.next_round_btn.setEnabled(False)
            self.diagram_detail.clear()
            return

        self.diagram_round_index = max(0, min(len(rounds)-1, self.diagram_round_index))
        step = rounds[self.diagram_round_index]
        self.diagram.set_round_data(step)
        self.round_label.setText(f"Раунд {self.diagram_round_index + 1} из {len(rounds)}")
        self.prev_round_btn.setEnabled(self.diagram_round_index > 0)
        self.next_round_btn.setEnabled(self.diagram_round_index < len(rounds)-1)

        self.diagram_detail.setPlainText(
            f"L{step['round']-1} = {step['L_in']}\n"
            f"K{step['round']} = {step['K']}\n"
            f"1) L XOR K = {step['xor_lk']}\n"
            f"2) S-box = {step['sbox_out']}\n"
            f"3) RotateRight(1) = F(L,K) = {step['F_out']}\n"
            f"4) R XOR F = новый L = {step['L_out']}\n"
            f"5) старый L → новый R = {step['R_out']}\n"
            f"6) Получены L{step['round']} и R{step['round']}"
        )

        lookups = step.get("sbox_lookups", [])
        self.sbox_widget.set_highlights([int(x["input_hex"], 16) for x in lookups])
        lines = []
        for x in lookups:
            lines.append(
                f"{x['input_bits']} → row {x['row']:X}, col {x['column']:X} → {x['output_bits']}"
            )
        self.sbox_detail.setPlainText("\n".join(lines))

    def apply_theme(self, dark: bool):
        self.diagram.set_theme(dark)
