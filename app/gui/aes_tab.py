# -*- coding: utf-8 -*-
"""
Whole AES Visualizer as the first top-level tab.
User request: keep AES logic intact, but remove visible internal tabs
"Настройки" and "О программе" from the AES tab strip. Their content is now
accessible from the global footer.
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from app.gui.key_view import KeyView
from app.gui.sbox_view import SboxView
from app.gui.encryption_view import EncryptionView
from app.gui.decryption_view import DecryptionView
from app.gui.round_view import RoundView
from app.gui.info_panel import SettingsView, AboutView


class AESTab(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent)
        self.app_state = app_state

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.inner_tabs = QTabWidget()
        layout.addWidget(self.inner_tabs)

        self.key_view = KeyView(self.app_state)
        self.sbox_view = SboxView(self.app_state)
        self.encryption_view = EncryptionView(self.app_state, self.key_view)
        self.decryption_view = DecryptionView(self.app_state)
        self.round_view = RoundView(self.app_state)

        # Kept as hidden compatibility objects; not shown in tab strip.
        self.settings_view = SettingsView(self.app_state)
        self.about_view = AboutView(self.app_state)

        self.inner_tabs.addTab(self.encryption_view, "Шифрование")
        self.inner_tabs.addTab(self.decryption_view, "Дешифрование")
        self.inner_tabs.addTab(self.key_view, "Ключ")
        self.inner_tabs.addTab(self.sbox_view, "S-box")
        self.inner_tabs.addTab(self.round_view, "Раунды")

        self.encryption_view.encryption_done.connect(self.round_view.refresh_from_state)
        self.decryption_view.decryption_done.connect(self.round_view.refresh_from_state)
        self.encryption_view.request_switch_to_round_tab.connect(
            lambda: self.inner_tabs.setCurrentWidget(self.round_view))
        self.decryption_view.request_switch_to_round_tab.connect(
            lambda: self.inner_tabs.setCurrentWidget(self.round_view))

    def show_settings_subtab(self):
        # no-op compatibility
        pass

    def show_about_subtab(self):
        # no-op compatibility
        pass
