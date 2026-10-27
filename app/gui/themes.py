# -*- coding: utf-8 -*-
"""
app/gui/themes.py

Светлая ("Утро") и тёмная ("Ночь") темы оформления приложения, а также
сохранение выбора темы между запусками через QSettings.
"""
from PySide6.QtCore import QSettings

ORG_NAME = "AESDemoApp"
APP_NAME = "AES Visualizer"

LIGHT_QSS = """
QWidget {
    background-color: #F7F8FA;
    color: #1B1F27;
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #F7F8FA; }
QTabWidget::pane { border: 1px solid #E1E4EA; border-radius: 10px; top: -1px; background: #FFFFFF; }
QTabBar::tab {
    background: #ECEEF2; color: #4B5160; padding: 9px 18px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: 600;
}
QTabBar::tab:selected { background: #FFFFFF; color: #2952E3; }
QTabBar::tab:hover { background: #E4E7EF; }
QGroupBox {
    border: 1px solid #E1E4EA; border-radius: 10px; margin-top: 14px; padding: 12px;
    font-weight: 600; background: #FFFFFF;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #2952E3; }
QPushButton {
    background-color: #2952E3; color: white; border: none; border-radius: 8px;
    padding: 9px 16px; font-weight: 600;
}
QPushButton:hover { background-color: #1F42C4; }
QPushButton:pressed { background-color: #17359C; }
QPushButton:disabled { background-color: #C8CDDA; color: #F0F1F5; }
QPushButton#secondary { background-color: #EDEFF5; color: #2952E3; }
QPushButton#secondary:hover { background-color: #E0E3EE; }
QPushButton#danger { background-color: #E23B3B; }
QPushButton#danger:hover { background-color: #C22E2E; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox {
    background: #FFFFFF; border: 1px solid #D7DAE3; border-radius: 8px; padding: 6px 8px;
    selection-background-color: #C7D3FB;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #2952E3; }
QTableWidget, QTreeWidget, QListWidget {
    background: #FFFFFF; border: 1px solid #E1E4EA; border-radius: 8px; gridline-color: #EEF0F4;
}
QHeaderView::section { background: #F1F2F7; border: none; padding: 6px; font-weight: 600; }
QLabel#heading { font-size: 18px; font-weight: 700; color: #12162A; }
QLabel#subheading { font-size: 12px; color: #6A7181; }
QLabel#warning { color: #B5460B; background: #FFF3E6; border-radius: 6px; padding: 6px 10px; }
QLabel#badgeAES { background: #E4F5E9; color: #1D8A48; border-radius: 6px; padding: 3px 10px; font-weight: 700; }
QLabel#badgeExp { background: #FDEBE3; color: #C1470E; border-radius: 6px; padding: 3px 10px; font-weight: 700; }
QScrollBar:vertical { background: #F1F2F7; width: 10px; }
QScrollBar::handle:vertical { background: #C6CBDA; border-radius: 5px; }

QLabel#brandTitle { font-size: 18px; font-weight: 800; color: #13254A; }
QLabel#feistelBadge { background: #EDF4FF; color: #1E5BD8; border: 1px solid #C9DAFF; border-radius: 11px; padding: 7px 12px; font-weight: 700; }
QLabel#roundNavigator { background: #F2F6FF; border: 1px solid #C9DAFF; border-radius: 9px; padding: 8px 22px; font-weight: 700; color: #193B7A; }
QWidget#appFooter { background: #FFFFFF; border: 1px solid #E1E7F0; border-radius: 10px; }
QPushButton#footerButton { background: transparent; color: #43506A; padding: 5px 9px; font-weight: 600; }
QPushButton#footerButton:hover { background: #EFF4FF; color: #1E5BD8; }
QLabel#footerSep { color: #CCD3DF; }
QLabel#themeGlyph { color: #4B648E; font-size: 17px; }
QLabel#footerLanguage { color: #53617A; font-weight: 600; }
QCheckBox#themeSwitch::indicator { width: 38px; height: 20px; border-radius: 10px; border: 1px solid #B9C8E8; background: #E9EFFB; }
QCheckBox#themeSwitch::indicator:checked { background: #2B6FFF; border: 1px solid #2B6FFF; }
QTabWidget#mainAlgorithmTabs > QTabBar::tab { min-width: 150px; font-size: 14px; padding: 11px 22px; }
QTabWidget#feistelInnerTabs > QTabBar::tab { min-width: 120px; }
QTabWidget#hashInnerTabs > QTabBar::tab { min-width: 150px; font-size: 14px; }
"""

DARK_QSS = """
QWidget {
    background-color: #14161F; color: #E7E9F2;
    font-family: 'Segoe UI', 'Inter', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #14161F; }
QTabWidget::pane { border: 1px solid #262A3A; border-radius: 10px; top: -1px; background: #1A1D29; }
QTabBar::tab {
    background: #1F2230; color: #9AA0B5; padding: 9px 18px; margin-right: 4px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; font-weight: 600;
}
QTabBar::tab:selected { background: #1A1D29; color: #7C93FF; }
QTabBar::tab:hover { background: #262A3A; }
QGroupBox {
    border: 1px solid #262A3A; border-radius: 10px; margin-top: 14px; padding: 12px;
    font-weight: 600; background: #1A1D29;
}
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #7C93FF; }
QPushButton {
    background-color: #4A66FF; color: white; border: none; border-radius: 8px;
    padding: 9px 16px; font-weight: 600;
}
QPushButton:hover { background-color: #5C76FF; }
QPushButton:pressed { background-color: #3B54D6; }
QPushButton:disabled { background-color: #33384A; color: #6D7286; }
QPushButton#secondary { background-color: #262A3A; color: #7C93FF; }
QPushButton#secondary:hover { background-color: #2E3346; }
QPushButton#danger { background-color: #E5534B; }
QPushButton#danger:hover { background-color: #C7423B; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox {
    background: #1F2230; border: 1px solid #2E3346; border-radius: 8px; padding: 6px 8px;
    color: #E7E9F2; selection-background-color: #3B54D6;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus { border: 1px solid #4A66FF; }
QTableWidget, QTreeWidget, QListWidget {
    background: #1A1D29; border: 1px solid #262A3A; border-radius: 8px; gridline-color: #262A3A;
    color: #E7E9F2;
}
QHeaderView::section { background: #1F2230; border: none; padding: 6px; font-weight: 600; color: #C6CBDA; }
QLabel#heading { font-size: 18px; font-weight: 700; color: #F3F4FA; }
QLabel#subheading { font-size: 12px; color: #8C93A8; }
QLabel#warning { color: #FFC98B; background: #3A2A17; border-radius: 6px; padding: 6px 10px; }
QLabel#badgeAES { background: #163825; color: #59D98A; border-radius: 6px; padding: 3px 10px; font-weight: 700; }
QLabel#badgeExp { background: #3A2417; color: #FF9C63; border-radius: 6px; padding: 3px 10px; font-weight: 700; }
QScrollBar:vertical { background: #1A1D29; width: 10px; }
QScrollBar::handle:vertical { background: #33384A; border-radius: 5px; }

QLabel#brandTitle { font-size: 18px; font-weight: 800; color: #F0F4FF; }
QLabel#feistelBadge { background: #1C2942; color: #86A8FF; border: 1px solid #334D7A; border-radius: 11px; padding: 7px 12px; font-weight: 700; }
QLabel#roundNavigator { background: #1E2942; border: 1px solid #334D7A; border-radius: 9px; padding: 8px 22px; font-weight: 700; color: #B8CBFF; }
QWidget#appFooter { background: #1A1D29; border: 1px solid #2B3142; border-radius: 10px; }
QPushButton#footerButton { background: transparent; color: #C5CEE0; padding: 5px 9px; font-weight: 600; }
QPushButton#footerButton:hover { background: #242B3D; color: #8AA7FF; }
QLabel#footerSep { color: #3D465A; }
QLabel#themeGlyph { color: #AFC0E4; font-size: 17px; }
QLabel#footerLanguage { color: #C5CEE0; font-weight: 600; }
QCheckBox#themeSwitch::indicator { width: 38px; height: 20px; border-radius: 10px; border: 1px solid #475574; background: #252B3A; }
QCheckBox#themeSwitch::indicator:checked { background: #5E7DFF; border: 1px solid #5E7DFF; }
QTabWidget#mainAlgorithmTabs > QTabBar::tab { min-width: 150px; font-size: 14px; padding: 11px 22px; }
QTabWidget#feistelInnerTabs > QTabBar::tab { min-width: 120px; }
QTabWidget#hashInnerTabs > QTabBar::tab { min-width: 150px; font-size: 14px; }
"""


def get_settings() -> QSettings:
    return QSettings(ORG_NAME, APP_NAME)


def load_saved_theme() -> str:
    s = get_settings()
    return s.value("theme", "light")


def save_theme(theme: str) -> None:
    s = get_settings()
    s.setValue("theme", theme)


def stylesheet_for(theme: str) -> str:
    return DARK_QSS if theme == "dark" else LIGHT_QSS
