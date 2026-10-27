# -*- coding: utf-8 -*-
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import Qt

from app.gui.app_state import AppState
from app.gui import themes
from app.gui.config_loader import load_ui_config
from app.gui.aes_tab import AESTab
from app.gui.feistel_tab import FeistelTab
from app.gui.hash_tab import HashTab
from app.gui.footer_widget import FooterWidget
from app.gui.info_panel import AboutDialog, QADialog
from app.gui.i18n import apply_language


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui_config = load_ui_config()
        window_cfg = self.ui_config.get("window", {})
        self.setWindowTitle(window_cfg.get("title", "Crypto Visualizer"))
        self.resize(window_cfg.get("width", 1200), window_cfg.get("height", 820))
        self.setMinimumSize(1000, 720)

        self.app_state = AppState()
        self.app_state.theme = themes.load_saved_theme()

        logo_path = Path(__file__).resolve().parents[2] / "assets" / "encryption_app_logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        shell = QWidget()
        shell.setObjectName("appShell")
        shell_layout = QVBoxLayout(shell)
        shell_layout.setContentsMargins(12, 10, 12, 8)
        shell_layout.setSpacing(8)
        self.setCentralWidget(shell)

        brand = QHBoxLayout()
        brand.setContentsMargins(4, 0, 4, 0)
        if logo_path.exists():
            logo = QLabel()
            pm = QPixmap(str(logo_path)).scaled(38, 38, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pm)
            logo.setFixedSize(42, 42)
            brand.addWidget(logo)
        brand_title = QLabel("Crypto Visualizer")
        brand_title.setObjectName("brandTitle")
        brand.addWidget(brand_title)
        brand.addStretch(1)
        shell_layout.addLayout(brand)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainAlgorithmTabs")
        shell_layout.addWidget(self.tabs, 1)

        self.aes_tab = AESTab(self.app_state)
        self.feistel_tab = FeistelTab(self.app_state, self.ui_config)
        self.hash_tab = HashTab(self.app_state)

        tabs_cfg = self.ui_config.get("tabs", [])
        titles_by_id = {t.get("id"): t.get("title") for t in tabs_cfg}
        self.tabs.addTab(self.aes_tab, titles_by_id.get("aes", "AES (SPN)"))
        self.tabs.addTab(self.feistel_tab, titles_by_id.get("feistel", "Feistel"))
        self.tabs.addTab(self.hash_tab, titles_by_id.get("hash", "HASH"))

        self.footer = FooterWidget(self.app_state.theme, self.app_state.language)
        self.footer.theme_changed.connect(self._apply_theme)
        self.footer.language_changed.connect(self._apply_language)
        self.footer.about_requested.connect(self._show_about_dialog)
        self.footer.qa_requested.connect(self._show_qa_dialog)
        shell_layout.addWidget(self.footer)

        self._about_dialog = None
        self._qa_dialog = None
        self._apply_theme(self.app_state.theme)
        self._apply_language(self.app_state.language)

    def _apply_theme(self, theme: str):
        self.app_state.theme = theme
        themes.save_theme(theme)
        app = QApplication.instance()
        app.setStyleSheet(themes.stylesheet_for(theme))
        self.footer.set_theme(theme)
        self.feistel_tab.apply_theme(theme == "dark")
        self.hash_tab.apply_theme(theme == "dark")

    def _apply_language(self, language: str):
        self.app_state.language = "en" if language == "en" else "ru"
        self.footer.set_language(self.app_state.language, emit=False)
        apply_language(self, self.app_state.language)
        self.hash_tab.set_language(self.app_state.language)

    def _show_about_dialog(self):
        self._about_dialog = AboutDialog(self)
        apply_language(self._about_dialog, self.app_state.language)
        self._about_dialog.exec()

    def _show_qa_dialog(self):
        self._qa_dialog = QADialog(self)
        apply_language(self._qa_dialog, self.app_state.language)
        self._qa_dialog.exec()
