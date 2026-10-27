# -*- coding: utf-8 -*-
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QCheckBox


class FooterWidget(QWidget):
    """Global footer with theme and real RU/EN language controls."""
    theme_changed = Signal(str)
    language_changed = Signal(str)
    about_requested = Signal()
    qa_requested = Signal()

    def __init__(self, current_theme="light", current_language="ru", parent=None):
        super().__init__(parent)
        self.setObjectName("appFooter")
        self.setFixedHeight(52)
        self._language = current_language

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 6, 14, 6)
        layout.setSpacing(10)

        self.about_btn = QPushButton("ⓘ  О программе")
        self.about_btn.setObjectName("footerButton")
        self.about_btn.clicked.connect(self.about_requested.emit)
        layout.addWidget(self.about_btn)

        self._sep(layout)

        self.qa_btn = QPushButton("?  Q&A")
        self.qa_btn.setObjectName("footerButton")
        self.qa_btn.clicked.connect(self.qa_requested.emit)
        layout.addWidget(self.qa_btn)

        layout.addStretch(1)

        self.sun = QLabel("☀")
        self.sun.setObjectName("themeGlyph")
        layout.addWidget(self.sun)

        self.theme_switch = QCheckBox()
        self.theme_switch.setObjectName("themeSwitch")
        self.theme_switch.setCursor(Qt.PointingHandCursor)
        self.theme_switch.setChecked(current_theme == "dark")
        self.theme_switch.toggled.connect(
            lambda checked: self.theme_changed.emit("dark" if checked else "light")
        )
        layout.addWidget(self.theme_switch)

        self.moon = QLabel("☾")
        self.moon.setObjectName("themeGlyph")
        layout.addWidget(self.moon)

        self._sep(layout)

        self.ru_btn = QPushButton("РУС")
        self.ru_btn.setObjectName("footerLanguageButton")
        self.ru_btn.setCursor(Qt.PointingHandCursor)
        self.ru_btn.clicked.connect(lambda: self.set_language("ru", emit=True))
        layout.addWidget(self.ru_btn)

        slash = QLabel("/")
        slash.setObjectName("footerSep")
        layout.addWidget(slash)

        self.en_btn = QPushButton("ENG")
        self.en_btn.setObjectName("footerLanguageButton")
        self.en_btn.setCursor(Qt.PointingHandCursor)
        self.en_btn.clicked.connect(lambda: self.set_language("en", emit=True))
        layout.addWidget(self.en_btn)

        self.set_language(current_language, emit=False)

    @staticmethod
    def _sep(layout):
        sep = QLabel("│")
        sep.setObjectName("footerSep")
        layout.addWidget(sep)

    def set_theme(self, theme: str):
        self.theme_switch.blockSignals(True)
        self.theme_switch.setChecked(theme == "dark")
        self.theme_switch.blockSignals(False)

    def set_language(self, language: str, emit: bool = False):
        language = "en" if language == "en" else "ru"
        changed = language != self._language
        self._language = language
        # Active language is visibly selected without depending on theme colors.
        self.ru_btn.setEnabled(language != "ru")
        self.en_btn.setEnabled(language != "en")
        self.ru_btn.setToolTip("Русский" if language != "ru" else "Текущий язык: русский")
        self.en_btn.setToolTip("English" if language != "en" else "Current language: English")
        if emit and changed:
            self.language_changed.emit(language)
