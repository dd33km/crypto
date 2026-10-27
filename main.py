# -*- coding: utf-8 -*-
"""
main.py

Точка входа приложения AES Visualizer.

Запуск:
    python main.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from app.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Crypto Visualizer")
    app.setOrganizationName("CryptoVisualizer")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
