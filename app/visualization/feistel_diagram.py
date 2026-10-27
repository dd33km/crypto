# -*- coding: utf-8 -*-
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPolygonF
from PySide6.QtCore import Qt, QRectF, QPointF
import math


class FeistelDiagramWidget(QWidget):
    """Compact full-round Feistel block diagram.

    The function path starts from L, as requested by the user's sketch.
    Every displayed binary value is taken from the real executed trace.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(560)
        self.data = None
        self.dark = False

    def set_theme(self, dark: bool):
        self.dark = dark
        self.update()

    def set_round_data(self, data: dict | None):
        self.data = data
        self.update()

    def clear(self):
        self.data = None
        self.update()

    @staticmethod
    def _short(bits: str, limit: int = 28) -> str:
        if not bits:
            return ""
        if len(bits) <= limit:
            return bits
        half = (limit - 1) // 2
        return bits[:half] + "…" + bits[-half:]

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        bg = QColor("#151B2C" if self.dark else "#FBFCFF")
        fg = QColor("#F4F7FF" if self.dark else "#14213D")
        muted = QColor("#8EA1C8" if self.dark else "#667085")
        line = QColor("#6E8DFF" if self.dark else "#246BFD")
        card = QColor("#202A43" if self.dark else "#F5F8FF")
        border = QColor("#395185" if self.dark else "#BBD0FF")
        yellow = QColor("#F6C94C")
        blue = QColor("#4A90E2")
        red = QColor("#E5534B")

        p.fillRect(self.rect(), bg)
        if not self.data:
            p.setPen(muted)
            p.setFont(QFont("Segoe UI", 12))
            p.drawText(self.rect(), Qt.AlignCenter,
                       "Выполните шифрование или расшифровку,\nчтобы увидеть диаграмму раунда")
            return

        d = self.data
        w = max(self.width(), 900)
        h = self.height()
        margin = 34

        p.setPen(fg)
        p.setFont(QFont("Segoe UI", 15, QFont.Bold))
        p.drawText(QRectF(0, 12, self.width(), 28), Qt.AlignCenter, f"Раунд {d['round']}")
        p.setPen(muted)
        p.setFont(QFont("Segoe UI", 9))
        p.drawText(QRectF(0, 40, self.width(), 22), Qt.AlignCenter,
                   "F работает с левым блоком: L XOR K → S-box → RotateRight(1)")

        def rounded_box(rect, title, bits, fill, text_color=None, small=False):
            p.setBrush(fill)
            p.setPen(QPen(border if fill == card else fill.darker(125), 1.6))
            p.drawRoundedRect(rect, 10, 10)
            p.setPen(text_color or fg)
            p.setFont(QFont("Segoe UI", 9 if small else 10, QFont.Bold))
            p.drawText(QRectF(rect.x()+7, rect.y()+6, rect.width()-14, 19), Qt.AlignCenter, title)
            p.setFont(QFont("Consolas", 8 if small else 9))
            p.drawText(QRectF(rect.x()+7, rect.y()+27, rect.width()-14, rect.height()-31),
                       Qt.AlignCenter | Qt.TextWordWrap, self._short(bits, 34 if small else 28))

        def arrow(a: QPointF, b: QPointF, color=None, width=2.0):
            c = color or line
            p.setPen(QPen(c, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawLine(a, b)
            ang = math.atan2(b.y()-a.y(), b.x()-a.x())
            s = 8
            pts = [
                b,
                QPointF(b.x()-s*math.cos(ang-.45), b.y()-s*math.sin(ang-.45)),
                QPointF(b.x()-s*math.cos(ang+.45), b.y()-s*math.sin(ang+.45)),
            ]
            p.setBrush(c)
            p.drawPolygon(QPolygonF(pts))

        def label(text, x, y, color=None, size=8):
            p.setPen(color or muted)
            p.setFont(QFont("Segoe UI", size, QFont.Bold))
            p.drawText(QRectF(x, y, 150, 20), Qt.AlignCenter, text)

        box_w, box_h = 210, 68
        left_x = margin + 28
        right_x = self.width() - margin - box_w - 28
        top_y = 82
        func_x = left_x + 35
        func_y = 206
        func_w = 300
        func_h = 222
        xor_cx = right_x + box_w / 2
        xor_cy = 316
        out_y = min(h - 102, 458)

        # Inputs
        l_rect = QRectF(left_x, top_y, box_w, box_h)
        r_rect = QRectF(right_x, top_y, box_w, box_h)
        rounded_box(l_rect, f"Блок L{d['round']-1}", d['L_in'], yellow, QColor("#1D2433"))
        rounded_box(r_rect, f"Блок R{d['round']-1}", d['R_in'], blue, QColor("#FFFFFF"))

        # Function container, based on the user's hand sketch.
        p.setBrush(card)
        p.setPen(QPen(border, 1.5))
        p.drawRoundedRect(QRectF(func_x, func_y, func_w, func_h), 14, 14)
        p.setPen(fg)
        p.setFont(QFont("Segoe UI", 11, QFont.Bold))
        p.drawText(QRectF(func_x, func_y+9, func_w, 24), Qt.AlignCenter, "Функция F")

        key_rect = QRectF(func_x - 112, func_y + 46, 96, 50)
        rounded_box(key_rect, f"Ключ K{d['round']}", d['K'], card, fg, small=True)

        step_x = func_x + 22
        step_w = func_w - 44
        step_h = 49
        y1 = func_y + 47
        y2 = y1 + 57
        y3 = y2 + 57
        rounded_box(QRectF(step_x, y1, step_w, step_h), "1. L XOR K", d['xor_lk'], card, fg, small=True)
        rounded_box(QRectF(step_x, y2, step_w, step_h), "2. S-box", d['sbox_out'], card, fg, small=True)
        rounded_box(QRectF(step_x, y3, step_w, step_h), "3. RotateRight(1) = F", d['F_out'], red, QColor("#FFFFFF"), small=True)

        # L -> function and key -> XOR
        arrow(QPointF(l_rect.center().x(), l_rect.bottom()), QPointF(l_rect.center().x(), func_y - 8))
        arrow(QPointF(l_rect.center().x(), func_y - 8), QPointF(step_x + step_w/2, y1))
        arrow(QPointF(key_rect.right(), key_rect.center().y()), QPointF(step_x, y1 + step_h/2))
        arrow(QPointF(step_x + step_w/2, y1+step_h), QPointF(step_x + step_w/2, y2))
        arrow(QPointF(step_x + step_w/2, y2+step_h), QPointF(step_x + step_w/2, y3))

        # XOR node combines R with F(L,K)
        xor_r = 24
        p.setBrush(QColor("#FFFFFF" if not self.dark else "#182238"))
        p.setPen(QPen(line, 2.2))
        p.drawEllipse(QPointF(xor_cx, xor_cy), xor_r, xor_r)
        p.setPen(fg)
        p.setFont(QFont("Segoe UI", 20))
        p.drawText(QRectF(xor_cx-xor_r, xor_cy-xor_r-2, xor_r*2, xor_r*2), Qt.AlignCenter, "⊕")
        label("R XOR F", xor_cx-75, xor_cy+29, line, 8)

        arrow(QPointF(r_rect.center().x(), r_rect.bottom()), QPointF(xor_cx, xor_cy-xor_r))
        arrow(QPointF(step_x+step_w, y3+step_h/2), QPointF(xor_cx-xor_r, xor_cy), red)

        # Outputs: result of XOR becomes new L, old L becomes new R.
        l_out = QRectF(left_x, out_y, box_w, box_h)
        r_out = QRectF(right_x, out_y, box_w, box_h)
        rounded_box(l_out, f"Новый L{d['round']}", d['L_out'], yellow, QColor("#1D2433"))
        rounded_box(r_out, f"Новый R{d['round']}", d['R_out'], blue, QColor("#FFFFFF"))

        # Cross/swap paths.
        arrow(QPointF(xor_cx, xor_cy+xor_r), QPointF(l_out.center().x(), l_out.top()))
        arrow(QPointF(l_rect.left()+22, l_rect.bottom()), QPointF(l_rect.left()+22, out_y-32))
        arrow(QPointF(l_rect.left()+22, out_y-32), QPointF(r_out.center().x(), r_out.top()))
        label(f"L{d['round']-1} → R{d['round']}", (left_x+right_x)/2-20, out_y-38, line, 8)
