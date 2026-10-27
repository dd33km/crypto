# -*- coding: utf-8 -*-
"""
app/visualization/sbox_image.py

Строит визуальное 16x16 изображение S-box: каждая ячейка окрашена в
оттенок, зависящий от значения байта (0..255), что позволяет "на глаз"
увидеть отсутствие явных структурных закономерностей.
"""
from PySide6.QtGui import QImage, QColor, QPainter, QFont, QPixmap
from PySide6.QtCore import Qt


def render_sbox_image(sbox, cell_size: int = 34, dark: bool = False) -> QPixmap:
    n = 16
    size = n * cell_size
    img = QImage(size, size, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    painter.setRenderHint(QPainter.Antialiasing)
    font = QFont("Consolas", 8)
    painter.setFont(font)

    for row in range(n):
        for col in range(n):
            value = sbox[row * 16 + col]
            # Цвет по значению байта: hue пропорционален значению
            hue = int((value / 255) * 260)
            color = QColor.fromHsv(hue, 160, 235 if not dark else 200)
            x = col * cell_size
            y = row * cell_size
            painter.fillRect(x, y, cell_size, cell_size, color)
            painter.setPen(QColor("#1B1F27") if not dark else QColor("#0B0D14"))
            painter.drawRect(x, y, cell_size, cell_size)
            painter.setPen(QColor("#12162A"))
            text = f"{value:02X}"
            painter.drawText(x, y, cell_size, cell_size, Qt.AlignCenter, text)

    painter.end()
    return QPixmap.fromImage(img)
