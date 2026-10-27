# -*- coding: utf-8 -*-
from __future__ import annotations

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QPlainTextEdit,
    QTabWidget, QGroupBox, QComboBox, QScrollArea, QFrame, QApplication,
    QMessageBox, QSplitter
)

from app.crypto.hash_visual import trace_hash


RU_EN = {
    'HASH — хеширование': 'HASH — hashing',
    'Два алгоритма, две отдельные учебные схемы. IV фиксирован стандартом, функция сжатия показана по раундам.':
        'Two algorithms, two separate educational diagrams. The IV is fixed by the standard and the compression function is shown round by round.',
    'MD5': 'MD5', 'SHA-256': 'SHA-256',
    'Исходное сообщение': 'Input message',
    'Введите слово или фразу': 'Enter a word or phrase',
    'Вычислить хэш': 'Calculate hash',
    'Скопировать хэш': 'Copy hash', 'Скопировано ✓': 'Copied ✓',
    'Режим визуализации': 'Visualization mode',
    'Учебный — первые 16 раундов': 'Educational — first 16 rounds',
    'Стандартный — все 64 раунда': 'Standard — all 64 rounds',
    'Результат': 'Result', 'Итоговый хэш': 'Final hash',
    'Хэширование': 'Hashing', 'Диаграмма': 'Diagram', 'Детали текущего раунда': 'Current round details',
    'Предыдущий': 'Previous', 'Следующий': 'Next',
    'Блок': 'Block', 'Раунд': 'Round', 'из': 'of',
    'Фиксированный IV': 'Fixed IV', 'Текущий блок сообщения': 'Current message block',
    'Функция сжатия F': 'Compression function F', 'Промежуточное состояние': 'Intermediate state',
    'Итоговый хэш после всех блоков': 'Final hash after all blocks',
    'Сообщение после padding': 'Message after padding',
    '512-битные блоки': '512-bit blocks',
    'Первые 16 слов блока': 'First 16 block words',
    'Расширение W[0..63]': 'Schedule W[0..63]',
    'В MD5 используются 16 слов M[0..15], выбираемые в разном порядке на 64 операциях.':
        'MD5 uses 16 words M[0..15], selected in a different order across 64 operations.',
    'В SHA-256 первые 16 слов берутся из блока, остальные W[16..63] вычисляются из предыдущих.':
        'In SHA-256 the first 16 words come from the block; W[16..63] are derived from earlier words.',
    'Функция сжатия принимает текущее состояние и 512-битный блок. Выход становится состоянием для следующего блока.':
        'The compression function takes the current state and a 512-bit block. Its output becomes the state for the next block.',
}


def hx(values):
    return '  '.join(f'{v:08X}' for v in values)


class HashFlowWidget(QWidget):
    """Painted block-chain diagram, intentionally similar to the Feistel teaching view."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(1120, 700)
        self.trace = None
        self.block_index = 0
        self.round_index = 0
        self.language = 'ru'
        self.dark = False

    def set_data(self, trace, block_index, round_index, language='ru'):
        self.trace, self.block_index, self.round_index, self.language = trace, block_index, round_index, language
        self.update()

    def set_dark(self, dark):
        self.dark = dark
        self.update()

    def _t(self, ru):
        return RU_EN.get(ru, ru) if self.language == 'en' else ru

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg = QColor('#1A1D29' if self.dark else '#FFFFFF')
        fg = QColor('#E7E9F2' if self.dark else '#182033')
        border = QColor('#3B4D72' if self.dark else '#B9C8E8')
        accent = QColor('#7C93FF' if self.dark else '#2952E3')
        soft = QColor('#222A3D' if self.dark else '#F2F6FF')
        p.fillRect(self.rect(), bg)
        if not self.trace:
            p.setPen(fg); p.drawText(self.rect(), Qt.AlignCenter, self._t('Введите слово или фразу'))
            return
        block = self.trace['blocks'][self.block_index]
        r = block['rounds'][self.round_index]
        W = self.width()
        def box(x,y,w,h,title,body='',fill=None):
            rect=QRectF(x,y,w,h)
            p.setPen(QPen(border,1.5)); p.setBrush(fill or soft); p.drawRoundedRect(rect,10,10)
            p.setPen(accent); f=QFont(); f.setBold(True); p.setFont(f); p.drawText(QRectF(x+10,y+7,w-20,22), Qt.AlignCenter, title)
            p.setPen(fg); f.setBold(False); f.setPointSize(9); p.setFont(f); p.drawText(QRectF(x+10,y+31,w-20,h-38), Qt.AlignCenter|Qt.TextWordWrap, body)
            return rect
        def arrow(x1,y1,x2,y2):
            p.setPen(QPen(accent,2)); p.drawLine(x1,y1,x2,y2)
            if y2>=y1: p.drawLine(x2,y2,x2-6,y2-8); p.drawLine(x2,y2,x2+6,y2-8)
        margin=35; wide=W-2*margin
        text=self.trace['text'] or '∅'
        box(margin,18,wide,68,self._t('Исходное сообщение'), text[:150] + ('…' if len(text)>150 else ''))
        p.setPen(fg); p.drawText(QRectF(margin,92,wide,30),Qt.AlignCenter,
            f"{self._t('512-битные блоки')}: " + ' | '.join(f"M{i}" for i in range(len(self.trace['blocks']))))
        cx=W/2
        state_title=self._t('Фиксированный IV') if self.block_index==0 else f"H{self.block_index}"
        state_body=hx(block['state_in'])
        left=box(margin,132,wide*0.42,86,state_title,state_body)
        right=box(W-margin-wide*0.42,132,wide*0.42,86,f"M{self.block_index} · {self._t('Текущий блок сообщения')}",block['bytes'].hex().upper()[:96]+'…')
        arrow(left.center().x(),left.bottom(),cx-70,258); arrow(right.center().x(),right.bottom(),cx+70,258)
        comp=box(cx-wide*0.32,258,wide*0.64,126,self._t('Функция сжатия F'),
            f"{self._t('Раунд')} {self.round_index+1} {self._t('из')} 64\n" + self._round_summary(r), QColor('#202C4A' if self.dark else '#EAF0FF'))
        arrow(cx,comp.bottom(),cx,421)
        out_title=self._t('Итоговый хэш после всех блоков') if self.block_index==len(self.trace['blocks'])-1 else self._t('Промежуточное состояние')
        box(margin,421,wide,64,out_title,hx(block['state_out']))

    def _round_summary(self, r):
        if self.trace['algorithm']=='sha256':
            return f"W[{r['round']}]={r['word']:08X}   K={r['k']:08X}\nT1={r['temp1']:08X}   T2={r['temp2']:08X}"
        return f"{r['func']}   M[{r['word_index']}]={r['word']:08X}   K={r['k']:08X}\nROL {r['shift']} → {r['rotated']:08X}"


class HashAlgorithmPage(QWidget):
    def __init__(self, algorithm, app_state, parent=None):
        super().__init__(parent)
        self.algorithm=algorithm; self.app_state=app_state; self.trace=None
        self.block_index=0; self.round_index=0; self.language=getattr(app_state,'language','ru')
        self._build()

    def _t(self, ru): return RU_EN.get(ru,ru) if self.language=='en' else ru

    def _build(self):
        root=QVBoxLayout(self); root.setContentsMargins(8,8,8,8); root.setSpacing(8)
        self.subtabs=QTabWidget(); self.subtabs.setObjectName(f'{self.algorithm}DetailTabs')
        root.addWidget(self.subtabs,1)

        # Main hashing page: input + final digest only. The large visualization lives
        # on its own tab so it is not squeezed into a narrow side panel.
        work=QWidget(); wl=QVBoxLayout(work); wl.setContentsMargins(10,10,10,10); wl.setSpacing(12)
        inp=QGroupBox('Исходное сообщение'); il=QVBoxLayout(inp)
        self.input=QPlainTextEdit(); self.input.setPlaceholderText('Введите слово или фразу'); self.input.setMinimumHeight(72); self.input.setMaximumHeight(96); il.addWidget(self.input)
        actions=QHBoxLayout(); self.run=QPushButton('Вычислить хэш'); self.run.clicked.connect(self.calculate); self.copy=QPushButton('Скопировать хэш'); self.copy.setObjectName('secondary'); self.copy.clicked.connect(self.copy_hash)
        actions.addStretch(1); actions.addWidget(self.run); actions.addWidget(self.copy); il.addLayout(actions); wl.addWidget(inp)
        res=QGroupBox('Результат'); rl=QVBoxLayout(res); self.digest=QPlainTextEdit(); self.digest.setReadOnly(True); self.digest.setMinimumHeight(88); self.digest.setMaximumHeight(110); self.digest.setStyleSheet('font-family: Consolas, monospace; font-size: 14px;'); rl.addWidget(self.digest); wl.addWidget(res)
        hint=QLabel('Функция сжатия принимает текущее состояние и 512-битный блок. Выход становится состоянием для следующего блока.'); hint.setWordWrap(True); hint.setObjectName('subheading'); wl.addWidget(hint)
        detail=QGroupBox('Детали текущего раунда'); detail_layout=QVBoxLayout(detail); self.details=QPlainTextEdit(); self.details.setReadOnly(True); self.details.setMinimumHeight(250); self.details.setStyleSheet('font-family: Consolas, monospace;'); detail_layout.addWidget(self.details); wl.addWidget(detail,1)
        self.subtabs.addTab(work,'Хэширование')

        # Full-width diagram page, intentionally laid out like Feistel's diagram.
        diagram_page=QWidget(); dl=QVBoxLayout(diagram_page); dl.setContentsMargins(8,8,8,8); dl.setSpacing(8)
        toolbar=QHBoxLayout(); toolbar.addWidget(QLabel('Режим визуализации'))
        self.mode=QComboBox(); self.mode.addItem('Учебный — первые 16 раундов','edu'); self.mode.addItem('Стандартный — все 64 раунда','full'); toolbar.addWidget(self.mode); toolbar.addStretch(1)
        self.diagram_digest=QLabel(''); self.diagram_digest.setObjectName('subheading'); self.diagram_digest.setTextInteractionFlags(Qt.TextSelectableByMouse); toolbar.addWidget(self.diagram_digest)
        dl.addLayout(toolbar)

        self.diagram=HashFlowWidget(); sc=QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame); sc.setWidget(self.diagram); dl.addWidget(sc,1)
        nav=QHBoxLayout(); self.prev=QPushButton('← Предыдущий'); self.prev.setObjectName('secondary'); self.next=QPushButton('Следующий →'); self.next.setObjectName('secondary'); self.pos=QLabel('Раунд —'); self.pos.setObjectName('roundNavigator'); self.prev.clicked.connect(lambda:self.shift(-1)); self.next.clicked.connect(lambda:self.shift(1)); nav.addStretch(1); nav.addWidget(self.prev); nav.addWidget(self.pos); nav.addWidget(self.next); nav.addStretch(1); dl.addLayout(nav)

        self.subtabs.addTab(diagram_page,'Диаграмма')
        self.mode.currentIndexChanged.connect(self._render)

    def calculate(self):
        try: self.trace=trace_hash(self.input.toPlainText(),self.algorithm)
        except Exception as e: QMessageBox.warning(self,'Ошибка',str(e)); return
        self.block_index=0; self.round_index=0; self.digest.setPlainText(self.trace['digest']); self.diagram_digest.setText(self.trace['digest']); self._render()

    def copy_hash(self):
        d=self.digest.toPlainText().strip()
        if not d: return
        QApplication.clipboard().setText(d); self.copy.setText(self._t('Скопировано ✓'))

    def shift(self, delta):
        if not self.trace: return
        limit=16 if self.mode.currentData()=='edu' else 64
        flat=self.block_index*limit+self.round_index+delta; total=len(self.trace['blocks'])*limit
        flat=max(0,min(total-1,flat)); self.block_index,self.round_index=divmod(flat,limit); self._render()

    def _render(self):
        if not self.trace: return
        limit=16 if self.mode.currentData()=='edu' else 64
        self.round_index=min(self.round_index,limit-1)
        b=self.trace['blocks'][self.block_index]; r=b['rounds'][self.round_index]
        self.pos.setText(f"{self._t('Блок')} {self.block_index+1}/{len(self.trace['blocks'])}   ·   {self._t('Раунд')} {self.round_index+1}/{limit}")
        if self.algorithm=='sha256':
            lines=[
                f"a={r['a']:08X}  b={r['b']:08X}  c={r['c']:08X}  d={r['d']:08X}",
                f"e={r['e']:08X}  f={r['f']:08X}  g={r['g']:08X}  h={r['h']:08X}", '',
                f"W[{r['round']}] = {r['word']:08X}", f"K[{r['round']}] = {r['k']:08X}",
                f"Ch = {r['ch']:08X}", f"Maj = {r['maj']:08X}", f"Σ0 = {r['sigma0']:08X}", f"Σ1 = {r['sigma1']:08X}",
                f"T1 = {r['temp1']:08X}", f"T2 = {r['temp2']:08X}", '',
                self._t('В SHA-256 первые 16 слов берутся из блока, остальные W[16..63] вычисляются из предыдущих.')]
        else:
            lines=[f"A={r['a']:08X}  B={r['b']:08X}  C={r['c']:08X}  D={r['d']:08X}",'',f"Function = {r['func']}",f"M[{r['word_index']}] = {r['word']:08X}",f"K[{r['round']}] = {r['k']:08X}",f"Shift = {r['shift']}",f"f = {r['func_value']:08X}",f"SUM = {r['sum']:08X}",f"ROL = {r['rotated']:08X}",f"new B = {r['new_b']:08X}",'',self._t('В MD5 используются 16 слов M[0..15], выбираемые в разном порядке на 64 операциях.')]
        lines += ['', self._t('Функция сжатия принимает текущее состояние и 512-битный блок. Выход становится состоянием для следующего блока.')]
        self.details.setPlainText('\n'.join(lines)); self.diagram.set_data(self.trace,self.block_index,self.round_index,self.language)

    def set_language(self, language):
        self.language='en' if language=='en' else 'ru'
        # Dynamic labels that generic i18n cannot safely reconstruct.
        if self.trace: self._render()
        self.diagram.language=self.language; self.diagram.update()

    def apply_theme(self, dark): self.diagram.set_dark(dark)


class HashTab(QWidget):
    def __init__(self, app_state, parent=None):
        super().__init__(parent); self.app_state=app_state
        root=QVBoxLayout(self); root.setContentsMargins(8,8,8,8); root.setSpacing(8)
        head=QHBoxLayout(); title=QLabel('HASH — хеширование'); title.setObjectName('heading'); sub=QLabel('Два алгоритма, две отдельные учебные схемы. IV фиксирован стандартом, функция сжатия показана по раундам.'); sub.setObjectName('subheading'); sub.setWordWrap(True); head.addWidget(title); head.addSpacing(12); head.addWidget(sub,1); root.addLayout(head)
        self.tabs=QTabWidget(); self.tabs.setObjectName('hashInnerTabs'); self.md5=HashAlgorithmPage('md5',app_state); self.sha=HashAlgorithmPage('sha256',app_state); self.tabs.addTab(self.md5,'MD5'); self.tabs.addTab(self.sha,'SHA-256'); root.addWidget(self.tabs,1)

    def set_language(self, language): self.md5.set_language(language); self.sha.set_language(language)
    def apply_theme(self, dark): self.md5.apply_theme(dark); self.sha.apply_theme(dark)
