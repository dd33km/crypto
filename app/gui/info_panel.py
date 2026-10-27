# -*- coding: utf-8 -*-
"""
Reusable informational widgets/dialogs for the application footer.

What the user requested:
- remove the old AES internal tabs "Настройки" and "О программе" from the
  visible AES tab strip;
- move "О программе" content to the footer button;
- move the glossary of terms to footer "Q&A" as a separate standalone view.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QScrollArea, QMessageBox, QRadioButton, QButtonGroup, QTextEdit,
    QDialog
)
from PySide6.QtCore import Signal

from app.gui import themes


TERMS = [
    ("Блок", "Фиксированный по размеру кусок данных (например, 128 бит), "
             "который шифр обрабатывает целиком за один раз.",
     "Блочные шифры работают не побайтово, а сразу над целым блоком, что "
     "позволяет применять сложные перемешивающие преобразования "
     "(перестановки, линейные преобразования) внутри блока."),
    ("Ключ", "Секретное значение, определяющее, как именно данные будут "
             "преобразованы шифром.",
     "Без знания ключа число возможных вариантов дешифрования равно "
     "2^(число бит ключа) — при достаточной длине ключа перебор "
     "вычислительно неосуществим."),
    ("S-box", "Таблица подстановки: заменяет один байт на другой по "
              "фиксированному правилу, добавляя нелинейность.",
     "Без нелинейного элемента (S-box) шифр был бы просто линейной "
     "функцией от ключа и открытого текста, что делает его легко "
     "взламываемым линейной алгеброй."),
    ("SubBytes", "Применение S-box к каждому байту состояния независимо.",
     "Обеспечивает нелинейность на уровне отдельных байт — "
     "фундаментальное свойство против линейного и дифференциального "
     "криптоанализа."),
    ("ShiftRows", "Циклический сдвиг каждой строки состояния на "
                  "количество позиций, равное номеру строки.",
     "Гарантирует, что байты одного столбца после нескольких раундов "
     "будут происходить из разных столбцов исходного состояния — "
     "это называется диффузией."),
    ("MixColumns", "Линейное преобразование каждого столбца состояния "
                    "путём умножения на фиксированную матрицу в GF(2^8).",
     "Совместно со ShiftRows обеспечивает полное перемешивание "
     "(diffusion): изменение одного бита входа влияет на весь блок "
     "уже после 2 раундов."),
    ("AddRoundKey", "Побитовый XOR состояния с текущим раундовым ключом.",
     "Это единственный шаг, где непосредственно используется секретный "
     "ключ — без него шифр был бы одинаков для любого ключа."),
    ("Key Expansion", "Процесс получения отдельного раундового ключа для "
                       "каждого раунда из одного исходного ключа.",
     "Позволяет использовать относительно короткий исходный ключ, но "
     "иметь разные (криптографически несвязанные на вид) ключи в каждом "
     "раунде."),
    ("Round Key", "16-байтовый (для AES-128) фрагмент расширенного ключа, "
                  "используемый в AddRoundKey конкретного раунда.",
     "Каждый Round Key вычисляется из предыдущего через RotWord, "
     "SubWord, XOR с Rcon — это гарантирует лавинный эффект уже на "
     "уровне ключевого расписания."),
    ("XOR", "Операция 'исключающее ИЛИ' над битами: 0⊕0=0, 1⊕0=1, "
            "0⊕1=1, 1⊕1=0.",
     "XOR обратим сам себе: (A⊕B)⊕B=A — именно поэтому AddRoundKey "
     "одинаково применяется и при шифровании, и (в обратном порядке "
     "раундовых ключей) при дешифровании."),
    ("Padding", "Дополнение данных (в этом приложении — нулевыми "
                "байтами) до размера, кратного размеру блока.",
     "Блочный шифр может обрабатывать только целые блоки, поэтому "
     "данные произвольной длины нужно предварительно дополнить."),
    ("Раунд", "Один цикл применения SubBytes-ShiftRows-MixColumns-"
              "AddRoundKey (или их обратных версий).",
     "Многократное повторение простых операций даёт стойкое к "
     "криптоанализу преобразование — это ключевая идея SPN-шифров "
     "(Substitution-Permutation Network)."),
    ("Inverse S-box", "Таблица, обратная S-box: inv_sbox[sbox[x]] = x.",
     "Необходима для дешифрования — позволяет восстановить исходный "
     "байт после того, как SubBytes заменил его на другой."),
]


class SettingsView(QWidget):
    """Retained only for backward compatibility inside code base.
    The user asked to remove the visible AES "Настройки" tab.
    Global theme switching is now done from the footer.
    """
    theme_changed = Signal(str)

    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Настройки")
        title.setObjectName("heading")
        layout.addWidget(title)

        theme_box = QGroupBox("Тема оформления")
        theme_layout = QHBoxLayout(theme_box)
        self.group = QButtonGroup(self)
        self.rb_light = QRadioButton("☀ Утро (светлая)")
        self.rb_dark = QRadioButton("🌙 Ночь (тёмная)")
        self.group.addButton(self.rb_light, 0)
        self.group.addButton(self.rb_dark, 1)
        if self.app_state.theme == "dark":
            self.rb_dark.setChecked(True)
        else:
            self.rb_light.setChecked(True)
        self.rb_light.toggled.connect(self._on_theme_toggle)
        theme_layout.addWidget(self.rb_light)
        theme_layout.addWidget(self.rb_dark)
        theme_layout.addStretch()
        layout.addWidget(theme_box)
        layout.addStretch()

    def _on_theme_toggle(self):
        theme = "light" if self.rb_light.isChecked() else "dark"
        self.app_state.theme = theme
        themes.save_theme(theme)
        self.theme_changed.emit(theme)


class AboutContent(QWidget):
    def __init__(self, parent=None, show_heading=True):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        if show_heading:
            title = QLabel("О программе")
            title.setObjectName("heading")
            outer.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)

        intro = QLabel(
            "<b>AES Visualizer</b> - учебное приложение для демонстрации "
            "блочного шифрования. Поддерживает два режима:<br>"
            "• <b>AES Standard</b> - строгая реализация AES-128/192/256 "
            "по спецификации NIST FIPS-197.<br>"
            "• <b>Experimental AES-like Cipher</b> - экспериментальный "
            "режим с изменяемыми параметрами (размер блока/ключа, число "
            "раундов, S-box, линейное преобразование), который "
            "<u>не является стандартом AES</u> и предназначен только для "
            "обучения."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        selftest_box = QGroupBox("Самопроверка AES (официальные тестовые векторы FIPS-197)")
        selftest_layout = QVBoxLayout(selftest_box)
        self.selftest_output = QTextEdit()
        self.selftest_output.setReadOnly(True)
        self.selftest_output.setMaximumHeight(160)
        run_btn = QPushButton("Запустить самопроверку")
        run_btn.clicked.connect(self._run_selftest)
        selftest_layout.addWidget(run_btn)
        selftest_layout.addWidget(self.selftest_output)
        layout.addWidget(selftest_box)
        self._run_selftest()

        layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _run_selftest(self):
        from app.crypto.aes import AESCipher
        vectors = [
            (128, "000102030405060708090a0b0c0d0e0f", "69c4e0d86a7b0430d8cdb78070b4c55a"),
            (192, "000102030405060708090a0b0c0d0e0f1011121314151617", "dda97ca4864cdfe06eaf70a0ec0d7191"),
            (256, "000102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f",
             "8ea2b7ca516745bfeafc49904b496089"),
        ]
        pt = bytes.fromhex("00112233445566778899aabbccddeeff"[:32])
        lines = []
        all_ok = True
        for keybits, key_hex, expected_hex in vectors:
            try:
                cipher = AESCipher(bytes.fromhex(key_hex), keybits)
                ct, _ = cipher.encrypt_blocks([pt])
                ok = ct[0].hex() == expected_hex
                pt2, _ = cipher.decrypt_blocks(ct)
                ok = ok and (pt2[0] == pt)
            except Exception as e:
                ok = False
                lines.append(f"AES-{keybits}: FAILED (исключение: {e})")
                all_ok = False
                continue
            all_ok = all_ok and ok
            lines.append(f"AES-{keybits}: {'PASS' if ok else 'FAILED'}")
        lines.append("")
        lines.append(f"Итог: AES self-test: {'PASS' if all_ok else 'FAILED'}")
        self.selftest_output.setPlainText("\n".join(lines))


class TermsContent(QWidget):
    def __init__(self, parent=None, show_heading=True):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        if show_heading:
            title = QLabel("Q&A / Словарь терминов")
            title.setObjectName("heading")
            outer.addWidget(title)

        helper = QLabel(
            "Нажмите «Почему это нужно?», чтобы открыть короткое объяснение термина."
        )
        helper.setWordWrap(True)
        outer.addWidget(helper)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)

        terms_box = QGroupBox("Словарь терминов")
        terms_layout = QVBoxLayout(terms_box)
        for term, short_desc, why in TERMS:
            row = QHBoxLayout()
            label = QLabel(f"<b>{term}</b>: {short_desc}")
            label.setWordWrap(True)
            row.addWidget(label, 4)
            btn = QPushButton("Почему это нужно?")
            btn.setObjectName("secondary")
            btn.clicked.connect(lambda checked=False, t=term, w=why: self._show_why(t, w))
            row.addWidget(btn, 1)
            terms_layout.addLayout(row)
        layout.addWidget(terms_box)

        layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def _show_why(self, term, why):
        QMessageBox.information(self, f"{term} - почему это нужно?", why)


class AboutView(AboutContent):
    """Compatibility wrapper. Not shown in AES tabs anymore."""

    def __init__(self, app_state, parent=None):
        self.app_state = app_state
        super().__init__(parent=parent, show_heading=True)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.resize(980, 680)
        layout = QVBoxLayout(self)
        layout.addWidget(AboutContent(show_heading=False))


class QADialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Q&A")
        self.resize(1100, 720)
        layout = QVBoxLayout(self)
        layout.addWidget(TermsContent(show_heading=False))
