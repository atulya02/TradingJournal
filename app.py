import sys
import os
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QDate, QPointF, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QFont, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QLineEdit, QComboBox, QDoubleSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox,
    QFrame, QScrollArea, QFormLayout, QDialog, QDialogButtonBox, QGraphicsOpacityEffect,
    QAbstractItemView, QDateEdit, QAbstractButton, QSizePolicy
)

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / 'data'
SHOT_DIR = APP_DIR / 'screenshots'
BACKUP_DIR = APP_DIR / 'backups'
DB_PATH = DATA_DIR / 'journal.db'
for p in (DATA_DIR, SHOT_DIR, BACKUP_DIR):
    p.mkdir(exist_ok=True)

PRE_ROWS = [
    ('TREND', 'trend', 10),
    ('AOI', 'aoi', 10),
    ('RPL', 'rpl', 5),
    ('EMA', 'ema', 5),
    ('PREVIOUS STRUCTURE', 'previous_structure', 10),
    ('CANDLE REJECTION', 'candle_rejection', 10),
    ('PATTERN', 'pattern', 10),
]
ENTRY_ROWS = [('SOS', 'sos', 10), ('ENGULFING', 'engulfing', 10), ('PATTERN', 'pattern', 5)]
PRE_TFS = ['WEEKLY', 'DAILY', '4H']
ENTRY_TFS = ['4H', '2H', '1H', '30M', '15M']
SYMBOLS = [
    'AUDJPY', 'EURNZD', 'GBPCAD', 'AUDCHF', 'EURGBP', 'GBPAUD', 'NZDCAD', 'NZDJPY', 'USDCHF',
    'AUDCAD', 'AUDNZD', 'AUDUSD', 'EURAUD', 'EURCAD', 'EURCHF', 'EURUSD', 'GBPCHF', 'GBPNZD',
    'GBPUSD', 'NZDUSD', 'USDCAD', 'CADJPY', 'CHFJPY', 'EURJPY', 'GBPJPY', 'USDJPY',
    'XAUUSD', 'NAS100', 'US30', 'GER40'
]

SCHEMA = '''
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    starting_balance REAL NOT NULL DEFAULT 0,
    daily_loss_limit REAL DEFAULT 0,
    max_loss REAL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    symbol TEXT NOT NULL,
    direction TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    timeframe TEXT,
    strategy TEXT,
    entry REAL DEFAULT 0,
    stop_loss REAL DEFAULT 0,
    take_profit REAL DEFAULT 0,
    exit_price REAL DEFAULT 0,
    lots REAL DEFAULT 0,
    risk_pct REAL DEFAULT 0,
    risk_amount REAL DEFAULT 0,
    reward_amount REAL DEFAULT 0,
    rr REAL DEFAULT 0,
    outcome TEXT DEFAULT 'OPEN',
    pnl REAL DEFAULT 0,
    r_multiple REAL DEFAULT 0,
    before_image TEXT,
    after_image TEXT,
    created_at TEXT NOT NULL,
    checklist_score REAL DEFAULT 0,
    checklist_json TEXT,
    pre_grade REAL DEFAULT 0,
    entry_grade REAL DEFAULT 0,
    overall_grade REAL DEFAULT 0,
    grade_letter TEXT DEFAULT 'F',
    sync_timeframes TEXT DEFAULT '',
    lot_size REAL DEFAULT 0,
    tick_size REAL DEFAULT 0,
    tick_value REAL DEFAULT 0,
    balance_after REAL DEFAULT 0,
    pnl_currency TEXT DEFAULT 'USD'
);
'''

STYLE = '''
* { outline: none; }
QMainWindow, QWidget { background: #F7F8FA; color: #111827; font-family: "Segoe UI Variable", "Segoe UI"; font-size: 13px; }
QLabel { color: #374151; }
QFrame#sidebar { background: #FFFFFF; border-right: 1px solid #E5E7EB; }
QFrame#glass { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 14px; }
QFrame#glass:hover { border-color: #C8D0DB; }
QPushButton { background: #FFFFFF; color: #374151; border: 1px solid #D9DEE6; border-radius: 9px; padding: 9px 13px; min-height: 24px; font-weight: 650; }
QPushButton:hover { background: #F1F5F9; border-color: #BFC8D4; }
QPushButton:pressed { background: #E8EDF3; padding-top: 10px; padding-bottom: 8px; }
QPushButton:disabled { color: #98A2B3; background: #F3F4F6; border-color: #E5E7EB; }
QPushButton#nav { text-align: left; border: 1px solid transparent; border-left: 2px solid transparent; padding: 11px 12px; border-radius: 9px; min-height: 28px; font-size: 13px; color: #667085; }
QPushButton#nav:hover { background: #F3F6FA; border-color: #E5E7EB; color: #1F2937; }
QPushButton#nav[active="true"] { background: #EEF4FF; border: 1px solid #D4E2F8; border-left: 2px solid #2563EB; color: #111827; font-weight: 800; }
QPushButton#primary { background: #2563EB; border: 1px solid #3B82F6; color: white; min-height: 34px; font-weight: 800; }
QPushButton#primary:hover { background: #3B82F6; }
QPushButton#primary:pressed { background: #1D4ED8; }
QPushButton#success { background: #ECFDF3; border: 1px solid #A7E3C3; color: #15803D; font-weight: 800; }
QPushButton#success:hover { background: #DCFCE7; }
QPushButton#danger { background: #FEF2F2; border: 1px solid #F3B4BC; color: #C2414F; font-weight: 800; }
QPushButton#danger:hover { background: #FEE2E2; }
QPushButton#cell { background: #FFFFFF; border: 1px solid #D9DEE6; border-radius: 9px; min-height: 40px; padding: 7px 10px; font-size: 12px; font-weight: 700; color: #475467; }
QPushButton#cell:hover { background: #111827; border-color: #B6C0CC; }
QPushButton#cell:checked { background: #DCFCE7; border: 1px solid #86C5A1; color: #166534; font-weight: 850; }
QPushButton#cell[counted="true"] { border-color: #B8CCE3; background: #EEF4FF; }
QPushButton#cell[counted="true"]:checked { background: #DCFCE7; border-color: #86C5A1; }
QPushButton#trend { min-height: 40px; font-weight: 850; border-radius: 9px; }
QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QDateEdit { background: #FFFFFF; color: #1F2937; border: 1px solid #D0D5DD; border-radius: 9px; padding: 9px 11px; min-height: 24px; selection-background-color: #2563EB; }
QLineEdit:hover, QComboBox:hover, QDoubleSpinBox:hover, QDateEdit:hover { border-color: #BFC8D4; }
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus { border: 1px solid #6B9AF0; background: #F8FAFC; }
QComboBox::drop-down, QDateEdit::drop-down { border: none; width: 32px; }
QComboBox QAbstractItemView { background: #FFFFFF; color: #1F2937; border: 1px solid #C7CDD6; selection-background-color: #DCEBFF; selection-color: #111827; padding: 5px; outline: 0; }
QCalendarWidget, QCalendarWidget QWidget { background: #FFFFFF; color: #1F2937; }
QCalendarWidget QToolButton { color: #1F2937; background: #FFFFFF; border: none; border-radius: 6px; padding: 6px; }
QCalendarWidget QToolButton:hover { background: #F1F5F9; }
QCalendarWidget QSpinBox { background: #FFFFFF; color: #1F2937; border: 1px solid #D0D5DD; }
QCalendarWidget QAbstractItemView:enabled { background: #FFFFFF; color: #1F2937; selection-background-color: #2563EB; selection-color: #111827; alternate-background-color: #FFFFFF; }
QTableWidget { background: #FFFFFF; alternate-background-color: #FAFBFC; gridline-color: transparent; border: 1px solid #E5E7EB; border-radius: 12px; selection-background-color: #E5F0FF; selection-color: #111827; }
QTableWidget::item { padding: 9px 10px; border-bottom: 1px solid #E5E7EB; }
QTableWidget::item:selected { background: #E5F0FF; }
QHeaderView::section { background: #FFFFFF; color: #667085; border: none; border-bottom: 1px solid #E5E7EB; padding: 11px 10px; font-size: 10px; font-weight: 850; }
QScrollArea { border: none; background: transparent; }
QScrollBar:vertical { background: transparent; width: 9px; margin: 5px 1px; }
QScrollBar::handle:vertical { background: #C7CDD6; border-radius: 4px; min-height: 36px; }
QScrollBar::handle:vertical:hover { background: #98A4B3; }
QScrollBar::add-line, QScrollBar::sub-line { height: 0; }
QDialog { background: #F7F8FA; }
QToolTip { background: #FFFFFF; color: #1F2937; border: 1px solid #C8D0DB; padding: 7px 9px; border-radius: 6px; }
QTabWidget::pane { border: 1px solid #E5E7EB; background: #F7F8FA; border-radius: 10px; }
QTabBar::tab { background: #FFFFFF; color: #667085; padding: 8px 14px; border: none; }
QTabBar::tab:selected { color: #111827; background: #FFFFFF; }
'''
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)

    account_cols = {r['name'] for r in con.execute('PRAGMA table_info(accounts)').fetchall()}
    if 'current_balance' not in account_cols:
        con.execute('ALTER TABLE accounts ADD COLUMN current_balance REAL NOT NULL DEFAULT 0')
        con.execute('UPDATE accounts SET current_balance=starting_balance')

    if 'balance_adjustment' not in account_cols:
        con.execute('ALTER TABLE accounts ADD COLUMN balance_adjustment REAL NOT NULL DEFAULT 0')

    con.commit()
    return con


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def today_str():
    return datetime.now().strftime('%Y-%m-%d')


def grade_letter(score):
    if score > 100: return 'A'
    if score > 90: return 'B'
    if score > 80: return 'C'
    if score > 70: return 'D'
    return 'F'


def display_outcome(value):
    v = str(value).upper()
    return 'STILL RUNNING' if v in ('OPEN', 'RUNNING', 'STILL RUNNING') else v


def trade_net(row):
    result = display_outcome(row['outcome'])
    if result == 'PROFIT':
        return float(row['reward_amount'] or 0)
    if result == 'LOSS':
        return -float(row['risk_amount'] or 0)
    return float(row['pnl'] or 0) if row['pnl'] else 0.0


def rebuild_account_balances(con):
    accounts = con.execute(
        'SELECT id,starting_balance,balance_adjustment FROM accounts'
    ).fetchall()

    for account in accounts:
        trades = con.execute(
            'SELECT outcome,reward_amount,risk_amount,pnl FROM trades WHERE account_id=?',
            (account['id'],)
        ).fetchall()

        net = sum(trade_net(t) for t in trades)
        balance = (
            float(account['starting_balance'] or 0)
            + float(account['balance_adjustment'] or 0)
            + net
        )

        con.execute(
            'UPDATE accounts SET current_balance=? WHERE id=?',
            (balance, account['id'])
        )

    con.commit()


class ClickableComboBox(QComboBox):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.showPopup()
            event.accept()
            return
        super().mousePressEvent(event)


class ClickableDateEdit(QDateEdit):
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.calendarPopup():
            for button in self.findChildren(QAbstractButton):
                if button.isVisible() and button.isEnabled():
                    try:
                        button.click()
                        event.accept()
                        return
                    except RuntimeError:
                        break
        super().mousePressEvent(event)

class GlassCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('glass')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)


class StatCard(GlassCard):
    def __init__(self, title, value='—'):
        super().__init__()
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16,13,16,13)
        lay.setSpacing(5)

        top = QHBoxLayout()
        top.setSpacing(6)

        dot = QLabel('●')
        dot.setFixedWidth(9)
        dot.setStyleSheet(
            'color:#2563EB;font-size:8px;background:transparent;'
        )
        top.addWidget(dot)

        label = QLabel(title.upper())
        label.setStyleSheet(
            'color:#667085;font-size:10px;font-weight:850;'
            'letter-spacing:.8px;background:transparent;'
        )
        top.addWidget(label)
        top.addStretch()
        lay.addLayout(top)

        self.v = QLabel(str(value))
        self.v.setMinimumHeight(38)
        self.v.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.v.setStyleSheet(
            'color:#111827;background:transparent;'
            'font-family:"Segoe UI";font-size:24px;font-weight:900;'
        )
        lay.addWidget(self.v, 1)

    def set_value(self, value):
        self.v.setText(str(value))
        self.v.show()
        self.v.update()
class ImageDrop(QLabel):
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.path = ''
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(340,210)
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            'border:1px dashed #B6C0CC;border-radius:16px;color:#667085;'
            'background:#FFFFFF;padding:12px;'
        )
        self.setText(title+'\n\nClick to choose\nor drag & drop')

    def mousePressEvent(self,e):
        if e.button()==Qt.LeftButton:
            p,_=QFileDialog.getOpenFileName(
                self,'Select screenshot','','Images (*.png *.jpg *.jpeg *.webp)'
            )
            if p:self.load_path(p)

    def dragEnterEvent(self,e):
        if e.mimeData().hasUrls():
            self.setStyleSheet(
                'border:1px solid #3B82F6;border-radius:16px;color:#1D4ED8;'
                'background:#EEF4FF;padding:12px;'
            )
            e.acceptProposedAction()

    def dragLeaveEvent(self,e):
        self.setStyleSheet(
            'border:1px dashed #B6C0CC;border-radius:16px;color:#667085;'
            'background:#FFFFFF;padding:12px;'
        )

    def dropEvent(self,e):
        if e.mimeData().urls():
            self.load_path(e.mimeData().urls()[0].toLocalFile())
            e.acceptProposedAction()
        self.setStyleSheet(
            'border:1px dashed #B6C0CC;border-radius:16px;color:#667085;'
            'background:#FFFFFF;padding:12px;'
        )

    def load_path(self,p):
        self.path=p
        pix=QPixmap(p)
        if not pix.isNull():
            self.setPixmap(pix.scaled(self.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def resizeEvent(self,e):
        super().resizeEvent(e)
        if self.path:
            pix=QPixmap(self.path)
            if not pix.isNull():
                self.setPixmap(pix.scaled(self.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))


class ChecklistTable(QFrame):
    def __init__(self,on_change=None,parent=None):
        super().__init__(parent); self.on_change=on_change; self.setObjectName('glass'); self.buttons={}; self.trend_state={tf:None for tf in PRE_TFS}
        self.grid=QGridLayout(self); self.grid.setContentsMargins(12,12,12,12); self.grid.setHorizontalSpacing(8); self.grid.setVerticalSpacing(7)
        for c,h in enumerate(['CHECK',*PRE_TFS,'WEIGHT']):
            x=QLabel(h); x.setAlignment(Qt.AlignCenter); x.setStyleSheet('color:#667085;font-size:12px;font-weight:800;'); self.grid.addWidget(x,0,c)
        self.grid.setColumnStretch(0,2)
        for c in range(1,5): self.grid.setColumnStretch(c,1)
        for r,(label,key,weight) in enumerate(PRE_ROWS,1):
            x=QLabel(label);x.setStyleSheet('font-size:13px;font-weight:650;padding-left:7px;');self.grid.addWidget(x,r,0);self.grid.setRowMinimumHeight(r,48)
            for c,tf in enumerate(PRE_TFS,1):
                if key=='trend':
                    b=QPushButton('—');b.setObjectName('trend');b.setCursor(Qt.PointingHandCursor);b.clicked.connect(lambda checked=False,tf_=tf:self.cycle_trend(tf_))
                else:
                    b=QPushButton('○');b.setObjectName('cell');b.setCheckable(True);b.setCursor(Qt.PointingHandCursor);b.clicked.connect(self.recalc)
                self.buttons[(key,tf)]=b;self.grid.addWidget(b,r,c)
            w=QLabel(f'{weight}% / TF');w.setAlignment(Qt.AlignCenter);w.setStyleSheet('color:#667085;font-size:12px;font-weight:600;');self.grid.addWidget(w,r,4)
        self.total=QLabel('PRE-ENTRY GRADE  •  0');self.total.setStyleSheet('font-size:18px;font-weight:850;padding:9px 4px;');self.grid.addWidget(self.total,len(PRE_ROWS)+1,0,1,5)
    def notify(self):
        if callable(self.on_change):self.on_change()
    def cycle_trend(self,tf):
        cur=self.trend_state[tf];nxt={None:'BULLISH','BULLISH':'BEARISH','BEARISH':None}[cur];self.trend_state[tf]=nxt;b=self.buttons[('trend',tf)];b.setText(nxt or '—')
        if nxt=='BULLISH':b.setStyleSheet('background:#16A34A;border:1px solid #86EFAC;border-radius:11px;min-height:40px;font-weight:850;color:white;')
        elif nxt=='BEARISH':b.setStyleSheet('background:#DC2626;border:1px solid #FCA5A5;border-radius:11px;min-height:40px;font-weight:850;color:white;')
        else:b.setStyleSheet('')
        self.notify()
    def recalc(self):
        for (key,tf),b in self.buttons.items():
            if key!='trend':b.setText('✓' if b.isChecked() else '○')
        self.notify()
    def refresh_contributors(self,selected):
        s=set(selected)
        for (key,tf),b in self.buttons.items():
            if key!='trend':b.setProperty('counted',tf in s);b.style().unpolish(b);b.style().polish(b);b.update()
    def score(self,selected):
        total=0
        for _,key,weight in PRE_ROWS:
            if key=='trend':total += sum(weight for tf in selected if self.trend_state.get(tf))
            else:total += sum(weight for tf in selected if self.buttons[(key,tf)].isChecked())
        return total
    def values(self):return {f'{k}|{tf}':(b.isChecked() if k!='trend' else self.trend_state[tf]) for (k,tf),b in self.buttons.items()}

class EntryTable(QFrame):
    def __init__(self,on_change=None,parent=None):
        super().__init__(parent);self.on_change=on_change;self.setObjectName('glass');self.buttons={};self.grid=QGridLayout(self);self.grid.setContentsMargins(12,12,12,12);self.grid.setHorizontalSpacing(8);self.grid.setVerticalSpacing(7)
        for c,h in enumerate(['ENTRY SIGNAL',*ENTRY_TFS,'GRADE']):x=QLabel(h);x.setAlignment(Qt.AlignCenter);x.setStyleSheet('color:#667085;font-size:12px;font-weight:800;');self.grid.addWidget(x,0,c)
        self.grid.setColumnStretch(0,2)
        for c in range(1,7):self.grid.setColumnStretch(c,1)
        for r,(label,key,weight) in enumerate(ENTRY_ROWS,1):
            x=QLabel(label);x.setStyleSheet('font-size:13px;font-weight:650;padding-left:7px;');self.grid.addWidget(x,r,0);self.grid.setRowMinimumHeight(r,52)
            for c,tf in enumerate(ENTRY_TFS,1):
                b=QPushButton('○');b.setObjectName('cell');b.setCheckable(True);b.setCursor(Qt.PointingHandCursor);b.clicked.connect(lambda checked=False,k=key,tf_=tf:self.only_one(k,tf_));self.buttons[(key,tf)]=b;self.grid.addWidget(b,r,c)
            g=QLabel('0%');g.setAlignment(Qt.AlignCenter);g.setStyleSheet('font-weight:850;color:#2563EB;');self.grid.addWidget(g,r,6)
        self.total=QLabel('ENTRY GRADE  •  0');self.total.setStyleSheet('font-size:18px;font-weight:850;padding:9px 4px;');self.grid.addWidget(self.total,len(ENTRY_ROWS)+1,0,1,7)
    def only_one(self,key,tf):
        c=self.buttons[(key,tf)]
        if c.isChecked():
            for other in ENTRY_TFS:
                if other!=tf:self.buttons[(key,other)].setChecked(False)
        for b in self.buttons.values():b.setText('✓' if b.isChecked() else '○')
        self.recalc()
    def recalc(self):
        total=0
        for r,(_,key,weight) in enumerate(ENTRY_ROWS,1):
            active=any(self.buttons[(key,tf)].isChecked() for tf in ENTRY_TFS);total += weight if active else 0;item=self.grid.itemAtPosition(r,6)
            if item and item.widget():item.widget().setText(f'{weight if active else 0}%')
        self.total.setText(f'ENTRY GRADE  •  {total:g}');self.notify()
    def notify(self):
        if callable(self.on_change):self.on_change()
    def score(self):return sum(weight for _,key,weight in ENTRY_ROWS if any(self.buttons[(key,tf)].isChecked() for tf in ENTRY_TFS))
    def values(self):return {f'{k}|{tf}':b.isChecked() for (k,tf),b in self.buttons.items()}


class TradeResultDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Trade Status')
        self.resize(650, 200)
        self.result = None

        lay = QVBoxLayout(self)
        title = QLabel('How is this trade being recorded?')
        title.setStyleSheet('font-size:22px;font-weight:900;')
        lay.addWidget(title)

        hint = QLabel('Use STILL RUNNING for an open trade. You can edit it later and mark PROFIT or LOSS.')
        hint.setStyleSheet('color:#667085;')
        lay.addWidget(hint)

        row = QHBoxLayout()
        for label, code, obj in [
            ('PROFIT', 'PROFIT', 'success'),
            ('LOSS', 'LOSS', 'danger'),
            ('STILL RUNNING', 'STILL RUNNING', '')
        ]:
            b = QPushButton(label)
            b.setMinimumHeight(50)
            b.setCursor(Qt.PointingHandCursor)
            if obj:
                b.setObjectName(obj)
            b.clicked.connect(lambda checked=False, c=code: self.choose(c))
            row.addWidget(b)
        lay.addLayout(row)

        cancel = QPushButton('CANCEL')
        cancel.clicked.connect(self.reject)
        lay.addWidget(cancel)

    def choose(self, code):
        self.result = code
        self.accept()


class TradeEditDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle(f'Edit Trade #{row["id"]}')
        self.resize(980, 700)

        root = QVBoxLayout(self)

        head = QHBoxLayout()
        title = QLabel(f'Edit Trade  •  #{row["id"]}')
        title.setStyleSheet('font-size:24px;font-weight:900;')
        head.addWidget(title)
        head.addStretch()
        self.status = QLabel(display_outcome(row['outcome']))
        self.status.setStyleSheet('font-size:16px;font-weight:900;')
        head.addWidget(self.status)
        root.addLayout(head)

        form = GlassCard()
        fg = QGridLayout(form)
        fg.setContentsMargins(16,15,16,15)
        fg.setHorizontalSpacing(12)
        fg.setVerticalSpacing(7)

        self.account = ClickableComboBox()
        self.load_accounts(row['account_id'])

        self.symbol = ClickableComboBox()
        self.symbol.addItems(SYMBOLS)
        self.symbol.setCurrentText(row['symbol'])

        self.date = ClickableDateEdit(QDate.fromString(row['trade_date'], 'yyyy-MM-dd'))
        self.date.setCalendarPopup(True)
        self.date.setDisplayFormat('yyyy-MM-dd')

        self.lots = QDoubleSpinBox()
        self.lots.setDecimals(3)
        self.lots.setRange(0,10000)
        self.lots.setSingleStep(0.01)
        self.lots.setValue(float(row['lots'] or 0))

        self.outcome = ClickableComboBox()
        self.outcome.addItems(['PROFIT','LOSS','STILL RUNNING'])
        self.outcome.setCurrentText(display_outcome(row['outcome']))
        self.outcome.currentIndexChanged.connect(self.on_outcome)

        self.risk = QDoubleSpinBox()
        self.risk.setDecimals(2)
        self.risk.setRange(0,1e9)
        self.risk.setPrefix('$ ')
        self.risk.setValue(float(row['risk_amount'] or 0))
        self.risk.valueChanged.connect(self.update_rr)

        self.profit = QDoubleSpinBox()
        self.profit.setDecimals(2)
        self.profit.setRange(0,1e9)
        self.profit.setPrefix('$ ')
        self.profit.setValue(float(row['reward_amount'] or 0))
        self.profit.valueChanged.connect(self.update_rr)

        fields = [
            ('ACCOUNT',self.account),('SYMBOL',self.symbol),('DATE',self.date),
            ('LOT SIZE',self.lots),('RESULT',self.outcome),('AMOUNT RISKED',self.risk),
            ('PROFIT AMOUNT',self.profit)
        ]
        for i,(label,w) in enumerate(fields):
            r,c=divmod(i,3)
            lab=QLabel(label)
            lab.setStyleSheet('color:#667085;font-size:11px;font-weight:800;letter-spacing:.7px;')
            fg.addWidget(lab,r*2,c)
            fg.addWidget(w,r*2+1,c)
            fg.setColumnStretch(c,1)
        root.addWidget(form)

        rr_card=GlassCard()
        rr_layout=QHBoxLayout(rr_card)
        rr_layout.setContentsMargins(16,12,16,12)
        self.rr_label=QLabel('R:R  —')
        self.rr_label.setStyleSheet('font-size:18px;font-weight:900;')
        rr_layout.addWidget(self.rr_label)
        rr_layout.addStretch()
        root.addWidget(rr_card)

        shots=GlassCard()
        sv=QVBoxLayout(shots)
        sv.setContentsMargins(16,16,16,16)
        st=QLabel('SCREENSHOTS')
        st.setStyleSheet('font-size:16px;font-weight:850;')
        sv.addWidget(st)
        sh=QHBoxLayout()
        self.before=ImageDrop('BEFORE TRADE')
        self.before.original_path=''
        self.after=ImageDrop('AFTER TRADE')
        self.after.original_path=''
        self.load_image(self.before,row['before_image'])
        self.load_image(self.after,row['after_image'])
        sh.addWidget(self.before,1)
        sh.addWidget(self.after,1)
        sv.addLayout(sh)
        root.addWidget(shots)

        actions=QHBoxLayout()
        actions.addStretch()
        cancel=QPushButton('CANCEL')
        cancel.clicked.connect(self.reject)
        save=QPushButton('SAVE CHANGES')
        save.setObjectName('primary')
        save.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(save)
        root.addLayout(actions)

        self.on_outcome()
        self.update_rr()

    def load_accounts(self, account_id):
        con=db()
        rows=con.execute('SELECT id,name FROM accounts ORDER BY id DESC').fetchall()
        con.close()
        for r in rows:
            self.account.addItem(r['name'],r['id'])
        idx=self.account.findData(account_id)
        if idx>=0:
            self.account.setCurrentIndex(idx)

    def load_image(self, widget, path):
        widget.original_path = path or ''
        if path and os.path.exists(path):
            widget.load_path(path)
            widget.path = path

    def on_outcome(self):
        result=self.outcome.currentText()
        is_profit=result=='PROFIT'
        self.profit.setEnabled(is_profit)
        if not is_profit:
            self.profit.setValue(0)
        self.status.setText(result)
        self.status.setStyleSheet(
            'font-size:16px;font-weight:900;color:' +
            ('#16A34A' if result=='PROFIT' else '#C2414F' if result=='LOSS' else '#B7791F')
        )
        self.update_rr()

    def update_rr(self):
        risk=self.risk.value()
        result=self.outcome.currentText()
        if result=='PROFIT' and risk>0:
            rr=self.profit.value()/risk
            self.rr_label.setText(f'R:R  1:{rr:.2f}  •  +{rr:.2f}R')
        elif result=='LOSS' and risk>0:
            self.rr_label.setText('R:R  1:1  •  -1R')
        else:
            self.rr_label.setText('R:R  —')


class TradeDetailDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row=row
        self.parent_window=parent
        self.setWindowTitle(f'Trade #{row["id"]}')
        self.resize(1050,700)

        lay=QVBoxLayout(self)
        head=QHBoxLayout()
        title=QLabel(f'{row["symbol"]}  •  {row["direction"]}  •  #{row["id"]}')
        title.setStyleSheet('font-size:25px;font-weight:900;')
        head.addWidget(title)
        head.addStretch()
        self.status=QLabel(display_outcome(row['outcome']))
        self.status.setStyleSheet('font-size:17px;font-weight:900;')
        head.addWidget(self.status)
        lay.addLayout(head)

        info=QGridLayout()
        vals=[
            ('Account',row['account'] or '—'),
            ('Date',row['trade_date']),
            ('Lot Size',row['lots']),
            ('Risked',f'${row["risk_amount"]:,.2f}'),
            ('Profit',f'${row["reward_amount"]:,.2f}' if display_outcome(row['outcome'])=='PROFIT' else '—'),
            ('R:R',f'1:{abs(row["rr"]):.2f}' if display_outcome(row['outcome'])!='STILL RUNNING' else '—'),
            ('Pre-entry',row['pre_grade']),
            ('Entry',row['entry_grade']),
            ('Overall',row['overall_grade']),
            ('Grade',row['grade_letter']),
            ('Entry TF',row['timeframe'] or '—'),
            ('Signal',row['strategy'] or '—')
        ]
        for i,(a,b) in enumerate(vals):
            info.addWidget(QLabel(a),i//4*2,i%4)
            x=QLabel(str(b));x.setStyleSheet('font-weight:850;font-size:15px;')
            info.addWidget(x,i//4*2+1,i%4)
        lay.addLayout(info)

        imgs=QHBoxLayout()
        for key,label in [('before_image','BEFORE'),('after_image','AFTER')]:
            box=QLabel()
            box.setAlignment(Qt.AlignCenter)
            box.setMinimumSize(430,280)
            box.setStyleSheet('border:1px solid #E5E7EB;border-radius:12px;background:#FFFFFF;')
            path=row[key]
            if path and os.path.exists(path):
                box.setPixmap(QPixmap(path).scaled(430,280,Qt.KeepAspectRatio,Qt.SmoothTransformation))
            else:
                box.setText(label+'\\nNo image')
            col=QVBoxLayout()
            col.addWidget(QLabel(label))
            col.addWidget(box)
            imgs.addLayout(col)
        lay.addLayout(imgs)

        actions=QHBoxLayout()
        actions.addStretch()
        edit=QPushButton('EDIT TRADE')
        edit.setObjectName('primary')
        edit.clicked.connect(self.edit_trade)
        close=QPushButton('CLOSE')
        close.clicked.connect(self.accept)
        actions.addWidget(edit)
        actions.addWidget(close)
        lay.addLayout(actions)

    def edit_trade(self):
        dlg = TradeEditDialog(self.row, self)

        if dlg.exec() != QDialog.Accepted:
            return

        result = dlg.outcome.currentText()
        risk = dlg.risk.value()
        profit = dlg.profit.value()

        if risk <= 0:
            QMessageBox.warning(
                self,
                'Risk required',
                'Amount risked must be greater than zero.'
            )
            return

        if result == 'PROFIT' and profit <= 0:
            QMessageBox.warning(
                self,
                'Profit required',
                'Enter the profit amount.'
            )
            return

        account_id = dlg.account.currentData()
        if account_id is None:
            QMessageBox.warning(
                self,
                'Account required',
                'Select an account.'
            )
            return

        rr = (
            profit / risk
            if result == 'PROFIT'
            else -1.0
            if result == 'LOSS'
            else 0.0
        )

        trade_id = int(self.row['id'])
        trade_dir = SHOT_DIR / f'trade_{trade_id}'
        trade_dir.mkdir(exist_ok=True)

        # Preserve the existing image unless the user picked a new one.
        before_path = self.row['before_image'] or ''
        after_path = self.row['after_image'] or ''

        before_selected = getattr(dlg.before, 'path', '') or ''
        before_original = getattr(dlg.before, 'original_path', '') or ''

        if before_selected:
            same_as_original = (
                bool(before_original)
                and os.path.abspath(before_selected).lower()
                == os.path.abspath(before_original).lower()
            )
            if not same_as_original:
                ext = Path(before_selected).suffix.lower() or '.png'
                dst = trade_dir / f'before{ext}'
                if os.path.abspath(before_selected).lower() != os.path.abspath(str(dst)).lower():
                    shutil.copy2(before_selected, dst)
                before_path = str(dst)

        after_selected = getattr(dlg.after, 'path', '') or ''
        after_original = getattr(dlg.after, 'original_path', '') or ''

        if after_selected:
            same_as_original = (
                bool(after_original)
                and os.path.abspath(after_selected).lower()
                == os.path.abspath(after_original).lower()
            )
            if not same_as_original:
                ext = Path(after_selected).suffix.lower() or '.png'
                dst = trade_dir / f'after{ext}'
                if os.path.abspath(after_selected).lower() != os.path.abspath(str(dst)).lower():
                    shutil.copy2(after_selected, dst)
                after_path = str(dst)

        con = db()
        try:
            con.execute(
                """UPDATE trades
                   SET account_id=?,
                       symbol=?,
                       trade_date=?,
                       lots=?,
                       risk_amount=?,
                       reward_amount=?,
                       rr=?,
                       outcome=?,
                       r_multiple=?,
                       before_image=?,
                       after_image=?
                   WHERE id=?""",
                (
                    account_id,
                    dlg.symbol.currentText().strip(),
                    dlg.date.date().toString('yyyy-MM-dd'),
                    dlg.lots.value(),
                    risk,
                    profit if result == 'PROFIT' else 0,
                    rr,
                    result,
                    rr,
                    before_path,
                    after_path,
                    trade_id
                )
            )

            # Rebuild the balance from the journal only after the trade update
            # is staged successfully.
            rebuild_account_balances(con)
            con.commit()

            updated = con.execute(
                """SELECT t.*, a.name account
                   FROM trades t
                   LEFT JOIN accounts a ON a.id=t.account_id
                   WHERE t.id=?""",
                (trade_id,)
            ).fetchone()

        except Exception as exc:
            con.rollback()
            QMessageBox.critical(
                self,
                'Could not save changes',
                f'The trade could not be saved.\n\n{exc}'
            )
            return
        finally:
            con.close()

        self.row = updated

        # Refresh the real MainWindow before showing the success dialog.
        # This guarantees Dashboard, History, Analytics and Accounts all read
        # the just-committed database state immediately.
        host = self.parent()
        while host is not None and not hasattr(host, 'refresh_all'):
            try:
                host = host.parent()
            except Exception:
                host = None

        if host is not None:
            host.refresh_all()
            QApplication.processEvents()

        QMessageBox.information(
            self,
            'Trade updated',
            f'Trade #{trade_id} saved successfully.\n\n'
            f'Status: {result}\n'
            + (
                f'R:R: 1:{rr:.2f}'
                if result == 'PROFIT'
                else '-1R'
                if result == 'LOSS'
                else 'Still running'
            )
        )
        self.accept()


class NewTrade(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.parent_window=parent
        self.build()

    def build(self):
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff);outer.addWidget(scroll)
        content=QWidget();scroll.setWidget(content)
        root=QVBoxLayout(content);root.setContentsMargins(28,26,28,32);root.setSpacing(15)

        top=QHBoxLayout()
        title=QLabel('New Trade');title.setStyleSheet('font-size:30px;font-weight:850;');top.addWidget(title);top.addStretch()
        self.overall=QLabel('OVERALL  0  •  F');self.overall.setAlignment(Qt.AlignCenter);self.overall.setMinimumWidth(190);self.overall.setMinimumHeight(58);self.overall.setStyleSheet('font-size:17px;font-weight:900;color:#111827;padding:10px 18px;border-radius:18px;background:#FFFFFF;border:1px solid #E5E7EB;');top.addWidget(self.overall);root.addLayout(top)

        info=GlassCard();il=QGridLayout(info);il.setContentsMargins(18,16,18,18);il.setHorizontalSpacing(12);il.setVerticalSpacing(6)
        self.account=ClickableComboBox();self.load_accounts()
        self.symbol=ClickableComboBox();self.symbol.addItems(SYMBOLS);self.symbol.setCurrentText('AUDJPY')
        self.date=ClickableDateEdit(QDate.currentDate());self.date.setCalendarPopup(True);self.date.setDisplayFormat('yyyy-MM-dd')
        self.lots=QDoubleSpinBox();self.lots.setDecimals(3);self.lots.setRange(0,10000);self.lots.setSingleStep(0.01);self.lots.setValue(0.01)
        self.outcome=ClickableComboBox();self.outcome.addItems(['PROFIT','LOSS','STILL RUNNING']);self.outcome.setCurrentText('STILL RUNNING');self.outcome.currentIndexChanged.connect(self.on_outcome)
        self.risk=QDoubleSpinBox();self.risk.setDecimals(2);self.risk.setRange(0,1e9);self.risk.setPrefix('$ ');self.risk.valueChanged.connect(self.update_rr)
        self.profit=QDoubleSpinBox();self.profit.setDecimals(2);self.profit.setRange(0,1e9);self.profit.setPrefix('$ ');self.profit.valueChanged.connect(self.update_rr)

        fields=[('ACCOUNT',self.account),('SYMBOL',self.symbol),('DATE',self.date),('LOT SIZE',self.lots),('RESULT',self.outcome),('AMOUNT RISKED',self.risk),('PROFIT AMOUNT',self.profit)]
        for i,(lab,w) in enumerate(fields):
            r,c=divmod(i,3);l=QLabel(lab);l.setStyleSheet('color:#667085;font-size:11px;font-weight:800;letter-spacing:.7px;');il.addWidget(l,r*2,c);il.addWidget(w,r*2+1,c);il.setColumnStretch(c,1)
        root.addWidget(info)

        rr=GlassCard();rg=QHBoxLayout(rr);rg.setContentsMargins(18,13,18,13)
        self.rr_label=QLabel('R:R  —');self.rr_label.setStyleSheet('font-size:18px;font-weight:900;');rg.addWidget(self.rr_label);rg.addStretch()
        self.direction=QLabel('DIRECTION  —');self.entry_tf=QLabel('ENTRY TF  —');self.direction.setStyleSheet('font-weight:850;');self.entry_tf.setStyleSheet('font-weight:850;');rg.addWidget(self.direction);rg.addWidget(self.entry_tf);root.addWidget(rr)

        bias=GlassCard();bl=QVBoxLayout(bias);bl.setContentsMargins(20,17,20,17);bh=QHBoxLayout();lab=QLabel('MARKET BIAS');lab.setStyleSheet('color:#667085;font-size:11px;font-weight:850;letter-spacing:1px;');bh.addWidget(lab);bh.addStretch();self.bias_label=QLabel('SET WEEKLY / DAILY / 4H TRENDS');self.bias_label.setStyleSheet('font-size:19px;font-weight:900;color:#B7791F;');bh.addWidget(self.bias_label);bl.addLayout(bh);self.bias_detail=QLabel('Only the timeframes matching the bias contribute to the pre-entry grade.');self.bias_detail.setStyleSheet('color:#667085;font-size:12px;');bl.addWidget(self.bias_detail);root.addWidget(bias)

        prebox=GlassCard();pl=QVBoxLayout(prebox);pl.setContentsMargins(14,14,14,14);ph=QLabel('PRE-ENTRY CHECKLIST');ph.setStyleSheet('font-size:16px;font-weight:850;');pl.addWidget(ph);note=QLabel('CONTINUOUS SYNC ONLY: Weekly + Daily, Daily + 4H, or all three. Weekly + 4H with Daily opposite = invalid.');note.setStyleSheet('color:#667085;font-size:12px;');pl.addWidget(note);self.pre=ChecklistTable(on_change=self.update_bias_and_grades,parent=self);pl.addWidget(self.pre);root.addWidget(prebox)

        enbox=GlassCard();el=QVBoxLayout(enbox);el.setContentsMargins(14,14,14,14);eh=QLabel('ENTRY CHECKLIST');eh.setStyleSheet('font-size:16px;font-weight:850;');el.addWidget(eh);en=QLabel('One timeframe per row. Entry timeframe is inferred automatically.');en.setStyleSheet('color:#667085;font-size:12px;');el.addWidget(en);self.entry_list=EntryTable(on_change=self.update_entry_info,parent=self);el.addWidget(self.entry_list);root.addWidget(enbox)

        grade=GlassCard();gg=QHBoxLayout(grade);gg.setContentsMargins(18,15,18,15);self.pre_grade=self.metric(gg,'PRE-ENTRY');self.entry_grade=self.metric(gg,'ENTRY');self.overall_grade=self.metric(gg,'OVERALL');self.letter=self.metric(gg,'GRADE');self.decision=QLabel('Set all three trends to calculate bias');self.decision.setAlignment(Qt.AlignCenter);self.decision.setWordWrap(True);self.decision.setStyleSheet('font-size:13px;font-weight:850;color:#B7791F;padding:8px;');gg.addWidget(self.decision,2);root.addWidget(grade)

        shots=GlassCard();sv=QVBoxLayout(shots);sv.setContentsMargins(16,16,16,16);st=QLabel('TRADE SCREENSHOTS');st.setStyleSheet('font-size:16px;font-weight:850;');sv.addWidget(st);hint=QLabel('Before and after only.');hint.setStyleSheet('color:#667085;font-size:12px;');sv.addWidget(hint);sh=QHBoxLayout();self.before=ImageDrop('BEFORE TRADE');self.after=ImageDrop('AFTER TRADE');sh.addWidget(self.before,1);sh.addWidget(self.after,1);sv.addLayout(sh);root.addWidget(shots)

        actions=QHBoxLayout();actions.addStretch();clr=QPushButton('CLEAR');clr.clicked.connect(self.clear_form);save=QPushButton('SAVE TRADE');save.setObjectName('primary');save.clicked.connect(self.save_trade);actions.addWidget(clr);actions.addWidget(save);root.addLayout(actions)

        self.on_outcome();self.update_bias_and_grades()

    def metric(self,layout,title):
        box=GlassCard();v=QVBoxLayout(box);v.setContentsMargins(13,10,13,10);l=QLabel(title);l.setStyleSheet('color:#667085;font-size:10px;font-weight:850;letter-spacing:.8px;');val=QLabel('0');val.setStyleSheet('font-size:20px;font-weight:900;');v.addWidget(l);v.addWidget(val);layout.addWidget(box,1);return val

    def load_accounts(self):
        old=self.account.currentData()
        self.account.blockSignals(True)
        self.account.clear()
        con=db();rows=con.execute('SELECT id,name FROM accounts ORDER BY id DESC').fetchall();con.close()
        if not rows:self.account.addItem('Create account first')
        else:
            for r in rows:self.account.addItem(r['name'],r['id'])
        if old is not None:
            idx=self.account.findData(old)
            if idx>=0:self.account.setCurrentIndex(idx)
        self.account.blockSignals(False)

    def valid_sync(self):
        weekly = self.pre.trend_state.get('WEEKLY')
        daily = self.pre.trend_state.get('DAILY')
        h4 = self.pre.trend_state.get('4H')

        if any(v not in ('BULLISH', 'BEARISH') for v in (weekly, daily, h4)):
            return []

        # Valid blocks must be continuous in the hierarchy:
        # WEEKLY+DAILY, DAILY+4H, or WEEKLY+DAILY+4H.
        # WEEKLY+4H while DAILY is opposite is invalid.
        if weekly == daily == h4:
            return ['WEEKLY', 'DAILY', '4H']
        if weekly == daily:
            return ['WEEKLY', 'DAILY']
        if daily == h4:
            return ['DAILY', '4H']
        return []

    def market_bias(self):
        sync = self.valid_sync()
        if not sync:
            return None
        return self.pre.trend_state[sync[0]]

    def selected_sync(self):
        return self.valid_sync()

    def inferred_entry_tf(self):
        for key in ('engulfing','sos','pattern'):
            for tf in ENTRY_TFS:
                if self.entry_list.buttons[(key,tf)].isChecked():return tf
        return None

    def inferred_entry_signal(self):
        for key in ('engulfing','sos','pattern'):
            for tf in ENTRY_TFS:
                if self.entry_list.buttons[(key,tf)].isChecked():return key.upper()
        return None

    def update_entry_info(self):
        tf=self.inferred_entry_tf();sig=self.inferred_entry_signal();self.entry_tf.setText(f'ENTRY TF  {tf or "—"}'+(f'  •  {sig}' if sig else ''));self.update_grades()

    def update_bias_and_grades(self):
        bias = self.market_bias()
        all_set = all(
            self.pre.trend_state.get(tf) in ('BULLISH', 'BEARISH')
            for tf in PRE_TFS
        )

        if not all_set:
            self.bias_label.setText('SET WEEKLY / DAILY / 4H TRENDS')
            self.bias_label.setStyleSheet('font-size:19px;font-weight:900;color:#B7791F;')
            self.bias_detail.setText(
                'Set all three Trend cells before the journal validates the setup.'
            )
            self.direction.setText('DIRECTION  —')
        elif not bias:
            self.bias_label.setText('NO VALID CONTINUOUS SYNC')
            self.bias_label.setStyleSheet('font-size:19px;font-weight:900;color:#C2414F;')
            self.bias_detail.setText(
                'Valid sync: WEEKLY + DAILY, DAILY + 4H, or WEEKLY + DAILY + 4H. '
                'WEEKLY + 4H with DAILY opposite is invalid.'
            )
            self.direction.setText('DIRECTION  —')
        else:
            selected = self.selected_sync()
            self.bias_label.setText(f'{bias}  •  {", ".join(selected)} CONTRIBUTING')
            self.bias_label.setStyleSheet(
                f'font-size:19px;font-weight:900;color:{"#16A34A" if bias=="BULLISH" else "#C2414F"};'
            )
            self.bias_detail.setText(
                'Only the continuous timeframe block matching the bias contributes grades.'
            )
            self.direction.setText(
                f'DIRECTION  {"BUY" if bias=="BULLISH" else "SELL"}'
            )

        self.update_grades()

    def update_grades(self):
        selected = self.selected_sync()
        self.pre.refresh_contributors(selected)

        pre = self.pre.score(selected)
        ent = self.entry_list.score()
        overall = pre + ent
        letter = grade_letter(overall)

        self.pre_grade.setText(f'{pre:g}')
        self.entry_grade.setText(f'{ent:g}')
        self.overall_grade.setText(f'{overall:g}')
        self.letter.setText(letter)
        self.overall.setText(f'OVERALL  {overall:g}  •  {letter}')

        all_set = all(
            self.pre.trend_state.get(tf) in ('BULLISH', 'BEARISH')
            for tf in PRE_TFS
        )

        if not all_set:
            msg, color = 'Set all three trends to calculate bias', '#B7791F'
        elif not selected:
            # Invalid non-contiguous sync: no pre-entry grades are allowed.
            msg, color = 'NO VALID SYNC  •  PRE-ENTRY GRADES = 0', '#C2414F'
            pre = 0
            overall = ent
            letter = grade_letter(overall)
            self.pre_grade.setText('0')
            self.overall_grade.setText(f'{overall:g}')
            self.letter.setText(letter)
            self.overall.setText(f'OVERALL  {overall:g}  •  {letter}')
        elif overall > 100:
            msg, color = 'GRADE A  •  setup exceeds 100', '#16A34A'
        elif overall > 90:
            msg, color = 'GRADE B  •  setup above 90', '#2563EB'
        elif overall > 80:
            msg, color = 'GRADE C  •  setup above 80', '#2563EB'
        elif overall > 70:
            msg, color = 'GRADE D  •  trade threshold reached', '#B7791F'
        else:
            msg, color = 'BELOW 70  •  NO TRADE', '#C2414F'

        self.decision.setText(msg)
        self.decision.setStyleSheet(
            f'font-size:13px;font-weight:850;color:{color};padding:8px;'
        )
        self.pre.total.setText(
            f'PRE-ENTRY GRADE  •  {pre:g}   |   '
            f'BIAS TFs: {", ".join(selected) if selected else "NONE"}'
        )
        self.update_rr()

    def on_outcome(self):
        is_profit=self.outcome.currentText()=='PROFIT'
        self.profit.setEnabled(is_profit)
        if not is_profit:self.profit.setValue(0)
        self.update_rr()

    def update_rr(self):
        risk=self.risk.value();result=self.outcome.currentText()
        if result=='PROFIT' and risk>0:
            rr=self.profit.value()/risk;self.rr_label.setText(f'R:R  1:{rr:.2f}  •  +{rr:.2f}R')
        elif result=='LOSS' and risk>0:
            self.rr_label.setText('R:R  1:1  •  -1R')
        else:
            self.rr_label.setText('R:R  —')

    def save_trade(self):
        if self.account.currentData() is None:
            QMessageBox.warning(self,'Account required','Create an account before saving a trade.');return
        bias = self.market_bias()
        all_set = all(
            self.pre.trend_state.get(tf) in ('BULLISH', 'BEARISH')
            for tf in PRE_TFS
        )
        if not all_set:
            QMessageBox.warning(
                self, 'Set market bias',
                'Set Weekly, Daily and 4H Trend before saving.'
            )
            return
        if not self.selected_sync():
            QMessageBox.warning(
                self, 'Invalid timeframe sync',
                'Valid sync is Weekly + Daily, Daily + 4H, or Weekly + Daily + 4H. '
                'Weekly + 4H with Daily opposite is invalid.'
            )
            return
        if not self.symbol.currentText().strip():
            QMessageBox.warning(self,'Symbol required','Select a symbol.');return
        if self.lots.value()<=0:
            QMessageBox.warning(self,'Lot size required','Enter the lot size used for this trade.');return
        if self.risk.value()<=0:
            QMessageBox.warning(self,'Risk required','Enter the amount risked.');return

        result=self.outcome.currentText();profit=self.profit.value()
        if result=='PROFIT' and profit<=0:
            QMessageBox.warning(self,'Profit required','Enter the profit amount.');return

        selected=self.selected_sync();pre=self.pre.score(selected);ent=self.entry_list.score();overall=pre+ent;letter=grade_letter(overall)
        rr=profit/self.risk.value() if result=='PROFIT' else -1.0 if result=='LOSS' else 0.0
        direction='BUY' if bias=='BULLISH' else 'SELL';tf=self.inferred_entry_tf();sig=self.inferred_entry_signal()
        data={'pre':self.pre.values(),'entry':self.entry_list.values(),'bias':bias,'bias_timeframes':selected,'entry_timeframe':tf,'entry_signal':sig}

        con=db()
        cur=con.execute(
            '''INSERT INTO trades(
                account_id,symbol,direction,trade_date,timeframe,strategy,lots,
                risk_amount,reward_amount,rr,outcome,r_multiple,
                before_image,after_image,created_at,checklist_score,checklist_json,
                pre_grade,entry_grade,overall_grade,grade_letter,sync_timeframes
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (
                self.account.currentData(),self.symbol.currentText().strip(),direction,
                self.date.date().toString('yyyy-MM-dd'),tf or '',sig or '',self.lots.value(),
                self.risk.value(),profit if result=='PROFIT' else 0,rr,result,rr,
                '','',now(),overall,json.dumps(data),pre,ent,overall,letter,json.dumps(selected)
            )
        )
        tid=cur.lastrowid
        td=SHOT_DIR/f'trade_{tid}';td.mkdir(exist_ok=True)
        before=after=''
        if self.before.path:
            dst=td/('before'+Path(self.before.path).suffix.lower());shutil.copy2(self.before.path,dst);before=str(dst)
        if self.after.path:
            dst=td/('after'+Path(self.after.path).suffix.lower());shutil.copy2(self.after.path,dst);after=str(dst)
        con.execute('UPDATE trades SET before_image=?,after_image=? WHERE id=?',(before,after,tid))
        rebuild_account_balances(con)
        con.commit();con.close()

        QMessageBox.information(
            self,'Trade saved',
            f'Trade #{tid} saved.\\nStatus: {result}\\n'
            + (f'R:R 1:{rr:.2f}' if result=='PROFIT' else '-1R' if result=='LOSS' else 'Still running — edit later to close it.')
        )
        # Clear the entry form only after the trade has been committed,
        # then force every screen to reread SQLite.
        self.clear_form()
        if self.parent_window:
            self.parent_window.refresh_all()
            QApplication.processEvents()

    def clear_form(self):
        self.lots.setValue(0.01);self.risk.setValue(0);self.profit.setValue(0);self.outcome.setCurrentText('STILL RUNNING');self.pre.trend_state={tf:None for tf in PRE_TFS}
        for (key,tf),b in self.pre.buttons.items():b.setChecked(False);b.setText('○' if key!='trend' else '—');b.setStyleSheet('')
        for b in self.entry_list.buttons.values():b.setChecked(False);b.setText('○')
        self.before.path='';self.before.setPixmap(QPixmap());self.before.setText('BEFORE TRADE\\n\\nDrag & drop or click')
        self.after.path='';self.after.setPixmap(QPixmap());self.after.setText('AFTER TRADE\\n\\nDrag & drop or click')
        self.update_bias_and_grades()



class History(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.build()

    def build(self):
        lay=QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,28)
        lay.setSpacing(13)

        head=QHBoxLayout()
        title_box=QVBoxLayout()
        title_box.setSpacing(3)
        t=QLabel('Trade History')
        t.setStyleSheet('font-size:30px;font-weight:900;')
        sub=QLabel('Every journal entry in one place. Double-click a row to open it.')
        sub.setStyleSheet('color:#667085;font-size:12px;')
        title_box.addWidget(t);title_box.addWidget(sub)
        head.addLayout(title_box);head.addStretch()

        refresh=QPushButton('↻  REFRESH')
        refresh.setCursor(Qt.PointingHandCursor)
        refresh.clicked.connect(self.load)
        head.addWidget(refresh)
        lay.addLayout(head)

        filters=GlassCard()
        fl=QHBoxLayout(filters)
        fl.setContentsMargins(12,10,12,10)
        search_label=QLabel('SEARCH')
        search_label.setStyleSheet('color:#667085;font-size:10px;font-weight:850;')
        fl.addWidget(search_label)
        self.search=QLineEdit()
        self.search.setPlaceholderText('Search symbol, side or result…')
        self.search.textChanged.connect(self.apply_filter)
        fl.addWidget(self.search,2)

        res_label=QLabel('RESULT')
        res_label.setStyleSheet('color:#667085;font-size:10px;font-weight:850;')
        fl.addWidget(res_label)
        self.result_filter=ClickableComboBox()
        self.result_filter.addItems(['ALL','PROFIT','LOSS','STILL RUNNING'])
        self.result_filter.currentIndexChanged.connect(self.apply_filter)
        fl.addWidget(self.result_filter)

        clear=QPushButton('CLEAR')
        clear.clicked.connect(lambda:(self.search.clear(),self.result_filter.setCurrentIndex(0)))
        fl.addWidget(clear)
        lay.addWidget(filters)

        self.table=QTableWidget(0,11)
        self.table.setHorizontalHeaderLabels(['#','DATE','SYMBOL','SIDE','LOT','RESULT','RISKED','PROFIT','R:R','OVERALL','ACTION'])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        for c in range(10):
            self.table.horizontalHeader().setSectionResizeMode(c,QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(10,QHeaderView.Fixed)
        self.table.setColumnWidth(10,138)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.doubleClicked.connect(self.open_selected)
        lay.addWidget(self.table,1)
        self.load()

    def load(self):
        con=db()
        self.all_rows=con.execute(
            'SELECT t.*,a.name account FROM trades t LEFT JOIN accounts a ON a.id=t.account_id ORDER BY t.id DESC'
        ).fetchall()
        con.close()
        self.apply_filter()

    def apply_filter(self):
        rows=getattr(self,'all_rows',[])
        query=self.search.text().strip().lower() if hasattr(self,'search') else ''
        result=self.result_filter.currentText() if hasattr(self,'result_filter') else 'ALL'
        if query:
            rows=[
                r for r in rows
                if query in str(r['symbol']).lower()
                or query in str(r['direction']).lower()
                or query in display_outcome(r['outcome']).lower()
            ]
        if result!='ALL':
            rows=[r for r in rows if display_outcome(r['outcome'])==result]

        self.rows=rows
        self.table.setRowCount(0)
        for row in rows:
            i=self.table.rowCount()
            self.table.insertRow(i)
            result_text=display_outcome(row['outcome'])
            vals=[
                row['id'],row['trade_date'],row['symbol'],row['direction'],
                f'{float(row["lots"] or 0):g}',result_text,
                f'${float(row["risk_amount"] or 0):,.2f}',
                f'${float(row["reward_amount"] or 0):,.2f}' if result_text=='PROFIT' else '—',
                f'1:{abs(float(row["rr"] or 0)):.2f}' if result_text!='STILL RUNNING' else '—',
                f'{float(row["overall_grade"] or 0):g}',''
            ]
            for j,v in enumerate(vals):
                if j==10:
                    b=QPushButton('VIEW / EDIT')
                    b.setCursor(Qt.PointingHandCursor)
                    b.clicked.connect(lambda checked=False,r=row:self.open_row(r))
                    self.table.setCellWidget(i,j,b)
                else:
                    item=QTableWidgetItem(str(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i,j,item)

            result_item=self.table.item(i,5)
            if result_item:
                result_item.setForeground(
                    QColor('#16A34A') if result_text=='PROFIT'
                    else QColor('#C2414F') if result_text=='LOSS'
                    else QColor('#B7791F')
                )
                result_item.setFont(QFont('Segoe UI',10,QFont.Weight.Bold))

    def open_selected(self,index):
        if 0<=index.row()<len(self.rows):
            self.open_row(self.rows[index.row()])

    def open_row(self,row):
        TradeDetailDialog(row,self).exec()
        self.load()
        if self.parent():
            self.parent().refresh_all()


class EquityCurve(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points = []
        self.setMinimumHeight(280)
        self.setStyleSheet(
            'background:#FFFFFF;border:1px solid #E5E7EB;border-radius:14px;'
        )

    def set_points(self, points):
        self.points = list(points or [])
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect()
        painter.fillRect(rect, QColor('#FFFFFF'))

        if len(self.points) < 2:
            painter.setPen(QPen(QColor('#667085')))
            painter.drawText(20, rect.height() // 2, 'No closed trades yet')
            return

        pad_left, pad_right = 52, 20
        pad_top, pad_bottom = 28, 35
        width = max(10, rect.width() - pad_left - pad_right)
        height = max(10, rect.height() - pad_top - pad_bottom)

        values = [p[1] for p in self.points]
        lo, hi = min(values), max(values)
        if abs(hi - lo) < 1e-9:
            lo -= 1
            hi += 1

        painter.setPen(QPen(QColor('#D9DEE6'), 1))
        for k in range(5):
            y = pad_top + height * k / 4
            painter.drawLine(pad_left, int(y), pad_left + width, int(y))

        painter.setPen(QPen(QColor('#2563EB'), 3))
        coords = []
        for i, (_, value) in enumerate(self.points):
            x = pad_left + width * i / max(1, len(self.points) - 1)
            y = pad_top + height * (hi - value) / (hi - lo)
            coords.append((x, y))

        for a, b in zip(coords, coords[1:]):
            painter.drawLine(int(a[0]), int(a[1]), int(b[0]), int(b[1]))

        painter.setPen(QPen(QColor('#667085'), 1))
        painter.setFont(QFont('Segoe UI', 9))
        painter.drawText(10, 17, 'CUMULATIVE R')
        painter.drawText(8, int(pad_top + height + 23), f'{lo:.1f}R')
        painter.drawText(8, int(pad_top + 10), f'{hi:.1f}R')


class Analytics(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.build()

    def build(self):
        outer = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24,24,24,30)
        lay.setSpacing(14)

        head = QHBoxLayout()
        title = QLabel('Analytics')
        title.setStyleSheet('font-size:30px;font-weight:900;')
        head.addWidget(title)
        head.addStretch()
        head.addWidget(QLabel('ACCOUNT'))
        self.account_filter = ClickableComboBox()
        self.account_filter.setMinimumWidth(270)
        self.account_filter.currentIndexChanged.connect(self.load)
        head.addWidget(self.account_filter)
        lay.addLayout(head)

        sub = QLabel('R-based analytics from closed PROFIT / LOSS trades. STILL RUNNING is excluded until closed.')
        sub.setStyleSheet('color:#667085;')
        lay.addWidget(sub)

        cards = QGridLayout()
        self.closed = StatCard('Closed Trades')
        self.profits = StatCard('Profit Trades')
        self.losses = StatCard('Loss Trades')
        self.win = StatCard('Win Rate')
        self.avg = StatCard('Avg R')
        self.expectancy = StatCard('Expectancy')
        self.net_r = StatCard('Net R')
        self.drawdown = StatCard('Max Drawdown')
        for i, w in enumerate([
            self.closed,self.profits,self.losses,self.win,
            self.avg,self.expectancy,self.net_r,self.drawdown
        ]):
            cards.addWidget(w, i//4, i%4)
        lay.addLayout(cards)

        curve_card = GlassCard()
        cv = QVBoxLayout(curve_card)
        cv.setContentsMargins(16,16,16,16)
        lab = QLabel('EQUITY CURVE')
        lab.setStyleSheet('font-size:15px;font-weight:900;')
        cv.addWidget(lab)
        self.curve = EquityCurve()
        cv.addWidget(self.curve)
        lay.addWidget(curve_card)

        self.pair_table = self.make_table_card(lay, 'PERFORMANCE BY PAIR')
        self.setup_table = self.make_table_card(lay, 'PERFORMANCE BY SETUP')
        self.tf_table = self.make_table_card(lay, 'PERFORMANCE BY TIMEFRAME')
        self.check_table = self.make_table_card(lay, 'CHECKLIST ANALYSIS')

        self.load()

    def make_table_card(self, parent_layout, title):
        card = GlassCard()
        box = QVBoxLayout(card)
        box.setContentsMargins(16,16,16,16)

        label = QLabel(title)
        label.setStyleSheet('font-size:15px;font-weight:900;')
        box.addWidget(label)

        table = QTableWidget(0,5)
        table.setHorizontalHeaderLabels(['GROUP','TRADES','WINS','WIN RATE','AVG R'])
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setDefaultSectionSize(42)
        box.addWidget(table)
        parent_layout.addWidget(card)
        return table

    def load_accounts(self):
        old = self.account_filter.currentData()
        self.account_filter.blockSignals(True)
        self.account_filter.clear()
        self.account_filter.addItem('All Accounts', None)
        con = db()
        rows = con.execute('SELECT id,name FROM accounts ORDER BY id DESC').fetchall()
        con.close()
        for r in rows:
            self.account_filter.addItem(r['name'], r['id'])
        if old is not None:
            idx = self.account_filter.findData(old)
            if idx >= 0:
                self.account_filter.setCurrentIndex(idx)
        self.account_filter.blockSignals(False)

    def load(self):
        self.load_accounts()
        account_id = self.account_filter.currentData()

        con = db()
        if account_id is None:
            rows = con.execute(
                "SELECT * FROM trades WHERE outcome IN ('PROFIT','LOSS') ORDER BY id"
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM trades WHERE account_id=? AND outcome IN ('PROFIT','LOSS') ORDER BY id",
                (account_id,)
            ).fetchall()
        con.close()

        n = len(rows)
        wins = sum(r['outcome'] == 'PROFIT' for r in rows)
        rs = [float(r['r_multiple'] or 0) for r in rows]
        net = sum(rs)
        avg = net/n if n else 0

        equity = 0
        peak = 0
        max_dd = 0
        points = []
        for r in rows:
            equity += float(r['r_multiple'] or 0)
            peak = max(peak, equity)
            max_dd = max(max_dd, peak-equity)
            points.append((r['id'], equity))

        self.closed.set_value(n)
        self.profits.set_value(wins)
        self.losses.set_value(n-wins)
        self.win.set_value(f'{wins/n*100:.1f}%' if n else '—')
        self.avg.set_value(f'{avg:.2f}R')
        self.expectancy.set_value(f'{avg:.2f}R / trade')
        self.net_r.set_value(f'{net:.2f}R')
        self.drawdown.set_value(f'{max_dd:.2f}R')
        self.curve.set_points(points)

        self.fill_group(self.pair_table, rows, lambda r: r['symbol'] or '—')
        self.fill_group(self.setup_table, rows, lambda r: r['strategy'] or '—')
        self.fill_group(self.tf_table, rows, lambda r: r['timeframe'] or '—')
        self.fill_checklist(rows)

    def fill_group(self, table, rows, key_fn):
        groups = {}
        for r in rows:
            groups.setdefault(key_fn(r), []).append(r)

        table.setRowCount(0)
        for key, items in sorted(
            groups.items(),
            key=lambda kv: sum(float(x['r_multiple'] or 0) for x in kv[1]),
            reverse=True
        ):
            n = len(items)
            wins = sum(x['outcome'] == 'PROFIT' for x in items)
            avg = sum(float(x['r_multiple'] or 0) for x in items) / n if n else 0
            i = table.rowCount()
            table.insertRow(i)
            vals = [key, n, wins, f'{wins/n*100:.1f}%' if n else '—', f'{avg:.2f}R']
            for j, value in enumerate(vals):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i,j,item)

    def fill_checklist(self, rows):
        # Shows the observed performance of trades where each checklist item
        # was actually marked YES. Trend cells are intentionally excluded.
        import json
        groups = {}

        for r in rows:
            try:
                payload = json.loads(r['checklist_json'] or '{}')
            except Exception:
                continue

            for raw_key, value in payload.get('pre', {}).items():
                if raw_key.startswith('trend|') or value is not True:
                    continue
                item_name = 'PRE • ' + raw_key.split('|')[0].replace('_',' ').title()
                groups.setdefault(item_name, []).append(r)

            for raw_key, value in payload.get('entry', {}).items():
                if value is not True:
                    continue
                item_name = 'ENTRY • ' + raw_key.split('|')[0].replace('_',' ').title()
                groups.setdefault(item_name, []).append(r)

        table = self.check_table
        table.setRowCount(0)
        for key, items in sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True):
            n = len(items)
            wins = sum(x['outcome'] == 'PROFIT' for x in items)
            avg = sum(float(x['r_multiple'] or 0) for x in items) / n if n else 0
            i = table.rowCount()
            table.insertRow(i)
            vals = [key, n, wins, f'{wins/n*100:.1f}%' if n else '—', f'{avg:.2f}R']
            for j, value in enumerate(vals):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i,j,item)


class Dashboard(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.parent_window=parent
        self.build()

    def build(self):
        lay=QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,28)
        lay.setSpacing(14)

        head=QHBoxLayout()
        title_box=QVBoxLayout()
        title_box.setSpacing(3)
        title=QLabel('Trading Dashboard')
        title.setStyleSheet('font-size:30px;font-weight:900;')
        sub=QLabel('A clean view of your account, risk and current journal state.')
        sub.setStyleSheet('color:#667085;font-size:12px;')
        title_box.addWidget(title);title_box.addWidget(sub)
        head.addLayout(title_box);head.addStretch()

        head.addWidget(QLabel('ACCOUNT'))
        self.account_filter=ClickableComboBox()
        self.account_filter.setMinimumWidth(250)
        self.account_filter.currentIndexChanged.connect(self.load)
        head.addWidget(self.account_filter)

        self.edit_account_button=QPushButton('EDIT ACCOUNT')
        self.edit_account_button.setCursor(Qt.PointingHandCursor)
        self.edit_account_button.clicked.connect(self.edit_selected_account)
        head.addWidget(self.edit_account_button)

        lay.addLayout(head)

        cards=QGridLayout()
        cards.setHorizontalSpacing(11);cards.setVerticalSpacing(11)
        self.balance=StatCard('Current Balance')
        self.total=StatCard('Total Trades')
        self.profits=StatCard('Profit Trades')
        self.losses=StatCard('Loss Trades')
        self.running=StatCard('Still Running')
        self.win=StatCard('Win Rate')
        self.avg=StatCard('Avg R')
        self.exp=StatCard('Expectancy')
        for i,w in enumerate([
            self.balance,self.total,self.profits,self.losses,
            self.running,self.win,self.avg,self.exp
        ]):
            cards.addWidget(w,i//4,i%4)
        lay.addLayout(cards)

        risk=GlassCard()
        rg=QGridLayout(risk)
        rg.setContentsMargins(18,15,18,15)
        rg.setHorizontalSpacing(28)
        rg.setVerticalSpacing(5)

        self.daily=QLabel('Daily loss remaining  •  —')
        self.maxloss=QLabel('Max loss remaining  •  —')
        self.daily_status=QLabel('')
        self.max_status=QLabel('')
        self.daily.setStyleSheet('font-size:14px;font-weight:850;')
        self.maxloss.setStyleSheet('font-size:14px;font-weight:850;')
        self.daily_status.setStyleSheet('color:#667085;font-size:11px;')
        self.max_status.setStyleSheet('color:#667085;font-size:11px;')
        rg.addWidget(self.daily,0,0);rg.addWidget(self.daily_status,1,0)
        rg.addWidget(self.maxloss,0,1);rg.addWidget(self.max_status,1,1)
        lay.addWidget(risk)

        section=QHBoxLayout()
        rt=QLabel('RECENT TRADES')
        rt.setStyleSheet('font-size:15px;font-weight:900;')
        section.addWidget(rt)
        section.addStretch()
        hint=QLabel('Double-click a row to view / edit')
        hint.setStyleSheet('color:#667085;font-size:11px;')
        section.addWidget(hint)
        lay.addLayout(section)

        self.table=QTableWidget(0,8)
        self.table.setHorizontalHeaderLabels(['#','DATE','SYMBOL','SIDE','LOT','RESULT','R:R','ACTION'])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        for c in range(7):
            self.table.horizontalHeader().setSectionResizeMode(c,QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(7,QHeaderView.Fixed)
        self.table.setColumnWidth(7,138)
        self.table.verticalHeader().setDefaultSectionSize(50)
        self.table.doubleClicked.connect(self.open_selected)
        lay.addWidget(self.table,1)
        self.load()

    def edit_selected_account(self):
        account_id=self.account_filter.currentData()

        if account_id is None:
            if self.parent_window:
                self.parent_window.set_page(4)
            return

        con=db()
        row=con.execute(
            'SELECT * FROM accounts WHERE id=?',
            (int(account_id),)
        ).fetchone()
        con.close()

        if row is None:
            return

        dlg=AccountEditDialog(row,self)
        if dlg.exec()==QDialog.Accepted and self.parent_window:
            self.parent_window.accounts.save_account_dialog(row,dlg)

    def load_accounts(self):
        old=self.account_filter.currentData()
        self.account_filter.blockSignals(True)
        self.account_filter.clear()
        self.account_filter.addItem('All Accounts',None)
        con=db()
        rows=con.execute('SELECT id,name FROM accounts ORDER BY id DESC').fetchall()
        con.close()
        for r in rows:self.account_filter.addItem(r['name'],r['id'])
        if old is not None:
            idx=self.account_filter.findData(old)
            if idx>=0:self.account_filter.setCurrentIndex(idx)
        self.account_filter.blockSignals(False)

    def load(self):
        self.load_accounts()
        aid=self.account_filter.currentData()
        con=db()
        rebuild_account_balances(con)
        if aid is None:
            rows=con.execute('SELECT t.*,a.name account FROM trades t LEFT JOIN accounts a ON a.id=t.account_id ORDER BY t.id DESC').fetchall()
            accounts=con.execute('SELECT * FROM accounts').fetchall()
        else:
            rows=con.execute('SELECT t.*,a.name account FROM trades t LEFT JOIN accounts a ON a.id=t.account_id WHERE t.account_id=? ORDER BY t.id DESC',(aid,)).fetchall()
            accounts=con.execute('SELECT * FROM accounts WHERE id=?',(aid,)).fetchall()
        con.commit();con.close()

        closed=[r for r in rows if display_outcome(r['outcome']) in ('PROFIT','LOSS')]
        profits=sum(display_outcome(r['outcome'])=='PROFIT' for r in rows)
        losses=sum(display_outcome(r['outcome'])=='LOSS' for r in rows)
        running=sum(display_outcome(r['outcome'])=='STILL RUNNING' for r in rows)
        avg=sum(r['r_multiple'] or 0 for r in closed)/len(closed) if closed else 0

        if accounts:
            balance=(float(accounts[0]['current_balance'] or accounts[0]['starting_balance'] or 0) if aid is not None else sum(float(a['current_balance'] or a['starting_balance'] or 0) for a in accounts))
            daily_limit=(float(accounts[0]['daily_loss_limit'] or 0) if aid is not None else sum(float(a['daily_loss_limit'] or 0) for a in accounts))
            max_limit=(float(accounts[0]['max_loss'] or 0) if aid is not None else sum(float(a['max_loss'] or 0) for a in accounts))
        else:
            balance=daily_limit=max_limit=0

        daily_used=sum(float(r['risk_amount'] or 0) for r in rows if display_outcome(r['outcome'])=='LOSS' and r['trade_date']==today_str())
        max_used=sum(float(r['risk_amount'] or 0) for r in rows if display_outcome(r['outcome'])=='LOSS')

        self.balance.set_value(f'${balance:,.2f}' if accounts else '—')
        self.total.set_value(len(rows))
        self.profits.set_value(profits)
        self.losses.set_value(losses)
        self.running.set_value(running)
        self.win.set_value(f'{profits/len(closed)*100:.1f}%' if closed else '—')
        self.avg.set_value(f'{avg:.2f}R')
        self.exp.set_value(f'{avg:.2f}R / trade' if closed else '—')

        self.daily.setText(f'Daily loss remaining  •  ${max(0,daily_limit-daily_used):,.2f}' if daily_limit else 'Daily loss remaining  •  limit not set')
        self.daily_status.setText(f'Used today: ${daily_used:,.2f} of ${daily_limit:,.2f}' if daily_limit else '')
        self.maxloss.setText(f'Max loss remaining  •  ${max(0,max_limit-max_used):,.2f}' if max_limit else 'Max loss remaining  •  limit not set')
        self.max_status.setText(f'Used: ${max_used:,.2f} of ${max_limit:,.2f}' if max_limit else '')

        self._rows=rows
        self.table.setRowCount(0)
        for row in rows[:14]:
            i=self.table.rowCount();self.table.insertRow(i)
            result=display_outcome(row['outcome'])
            vals=[row['id'],row['trade_date'],row['symbol'],row['direction'],row['lots'],result,f'1:{abs(row["rr"]):.2f}' if result!='STILL RUNNING' else '—','']
            for j,v in enumerate(vals):
                if j==7:
                    b=QPushButton('VIEW / EDIT')
                    b.setCursor(Qt.PointingHandCursor)
                    b.clicked.connect(lambda checked=False,r=row:self.open_row(r))
                    self.table.setCellWidget(i,j,b)
                else:
                    item=QTableWidgetItem(str(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i,j,item)
            item=self.table.item(i,5)
            if item:
                item.setForeground(
                    QColor('#16A34A') if result=='PROFIT'
                    else QColor('#C2414F') if result=='LOSS'
                    else QColor('#B7791F')
                )
                item.setFont(QFont('Segoe UI',10,QFont.Weight.Bold))

    def open_selected(self,index):
        if 0<=index.row()<len(self._rows):
            self.open_row(self._rows[index.row()])

    def open_row(self,row):
        TradeDetailDialog(row,self).exec()
        self.load()
        if self.parent_window:self.parent_window.refresh_all()


class AccountEditDialog(QDialog):
    def __init__(self, row, parent=None):
        super().__init__(parent)
        self.row = row
        self.setWindowTitle(f'Edit Account • {row["name"]}')
        self.resize(520, 430)

        root = QVBoxLayout(self)

        title = QLabel('Edit Account')
        title.setStyleSheet('font-size:24px;font-weight:900;')
        root.addWidget(title)

        sub = QLabel(
            'Set the account values directly. Future journal profits and losses '
            'will continue updating from the new current balance.'
        )
        sub.setWordWrap(True)
        sub.setStyleSheet('color:#667085;font-size:12px;')
        root.addWidget(sub)

        card = GlassCard()
        form = QFormLayout(card)
        form.setContentsMargins(18,18,18,18)
        form.setVerticalSpacing(11)

        self.name = QLineEdit(str(row['name']))

        self.starting = QDoubleSpinBox()
        self.starting.setRange(0, 1000000000)
        self.starting.setDecimals(2)
        self.starting.setPrefix('$ ')
        self.starting.setValue(float(row['starting_balance'] or 0))

        self.current = QDoubleSpinBox()
        self.current.setRange(0, 1000000000)
        self.current.setDecimals(2)
        self.current.setPrefix('$ ')
        self.current.setValue(
            float(row['current_balance'] or row['starting_balance'] or 0)
        )

        self.daily = QDoubleSpinBox()
        self.daily.setRange(0, 1000000000)
        self.daily.setDecimals(2)
        self.daily.setPrefix('$ ')
        self.daily.setValue(float(row['daily_loss_limit'] or 0))

        self.max_loss = QDoubleSpinBox()
        self.max_loss.setRange(0, 1000000000)
        self.max_loss.setDecimals(2)
        self.max_loss.setPrefix('$ ')
        self.max_loss.setValue(float(row['max_loss'] or 0))

        self.adjustment = QLabel('—')
        self.adjustment.setStyleSheet(
            'color:#2563EB;font-size:14px;font-weight:850;'
        )

        form.addRow('Account name', self.name)
        form.addRow('Starting balance', self.starting)
        form.addRow('Current balance', self.current)
        form.addRow('Daily loss limit', self.daily)
        form.addRow('Max loss', self.max_loss)
        form.addRow('Manual balance adjustment', self.adjustment)
        root.addWidget(card)

        note = QLabel(
            'Current Balance is editable. The app stores the required adjustment '
            'so a later PROFIT or LOSS updates from this balance.'
        )
        note.setWordWrap(True)
        note.setStyleSheet('color:#667085;font-size:11px;')
        root.addWidget(note)

        actions = QHBoxLayout()
        actions.addStretch()

        cancel = QPushButton('CANCEL')
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)

        save = QPushButton('SAVE ACCOUNT')
        save.setObjectName('primary')
        save.clicked.connect(self.accept)
        actions.addWidget(save)

        root.addLayout(actions)

        self.starting.valueChanged.connect(self.update_adjustment)
        self.current.valueChanged.connect(self.update_adjustment)
        self.update_adjustment()

    def update_adjustment(self):
        try:
            con = db()
            trades = con.execute(
                'SELECT outcome,reward_amount,risk_amount,pnl FROM trades WHERE account_id=?',
                (int(self.row['id']),)
            ).fetchall()
            con.close()

            journal_net = sum(trade_net(t) for t in trades)
            adjustment = self.current.value() - self.starting.value() - journal_net
            self.adjustment.setText(
                f'{adjustment:+,.2f}   •   Journal net {journal_net:+,.2f}'
            )
        except Exception:
            self.adjustment.setText('—')


class Accounts(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.build()

    def build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24,24,24,28)
        lay.setSpacing(13)

        head = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel('Accounts')
        title.setStyleSheet('font-size:30px;font-weight:900;')

        sub = QLabel(
            'Manage balances and prop-firm risk limits for every account.'
        )
        sub.setStyleSheet('color:#667085;font-size:12px;')

        title_box.addWidget(title)
        title_box.addWidget(sub)
        head.addLayout(title_box)
        head.addStretch()

        add = QPushButton('+  ADD ACCOUNT')
        add.setObjectName('primary')
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self.add_account)
        head.addWidget(add)

        lay.addLayout(head)

        note = QLabel(
            'Current balance updates automatically when a journal trade closes, '
            'and can also be changed directly from EDIT ACCOUNT.'
        )
        note.setStyleSheet('color:#667085;font-size:11px;padding:3px 2px;')
        lay.addWidget(note)

        self.table = QTableWidget(0,7)
        self.table.setHorizontalHeaderLabels([
            'ACCOUNT','STARTING','CURRENT','DAILY LOSS LIMIT',
            'MAX LOSS','CREATED','ACTION'
        ])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for c in range(6):
            self.table.horizontalHeader().setSectionResizeMode(c, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 140)
        self.table.verticalHeader().setDefaultSectionSize(54)

        lay.addWidget(self.table,1)
        self.load()

    def add_account(self):
        d = QDialog(self)
        d.setWindowTitle('Add Account')
        d.resize(460,310)

        f = QFormLayout(d)
        f.setContentsMargins(20,20,20,20)
        f.setVerticalSpacing(10)

        name = QLineEdit()
        name.setPlaceholderText('e.g. FundedNext 15K')

        start = QDoubleSpinBox()
        start.setRange(0, 1000000000)
        start.setDecimals(2)
        start.setPrefix('$ ')

        daily = QDoubleSpinBox()
        daily.setRange(0, 1000000000)
        daily.setDecimals(2)
        daily.setPrefix('$ ')

        maxl = QDoubleSpinBox()
        maxl.setRange(0, 1000000000)
        maxl.setDecimals(2)
        maxl.setPrefix('$ ')

        f.addRow('Account name', name)
        f.addRow('Starting balance', start)
        f.addRow('Daily loss limit', daily)
        f.addRow('Max loss', maxl)

        bb = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        bb.accepted.connect(d.accept)
        bb.rejected.connect(d.reject)
        f.addRow(bb)

        if d.exec() == QDialog.Accepted and name.text().strip():
            con = db()
            con.execute(
                '''INSERT INTO accounts(
                       name,starting_balance,current_balance,
                       daily_loss_limit,max_loss,created_at,balance_adjustment
                   ) VALUES(?,?,?,?,?,?,?)''',
                (
                    name.text().strip(),
                    start.value(),
                    start.value(),
                    daily.value(),
                    maxl.value(),
                    now(),
                    0
                )
            )
            con.commit()
            con.close()

            self.load()
            if self.parent_window:
                self.parent_window.refresh_all()

    def edit_account(self, row):
        dlg = AccountEditDialog(row, self)
        if dlg.exec() != QDialog.Accepted:
            return
        self.save_account_dialog(row, dlg)

    def save_account_dialog(self, row, dlg):
        name = dlg.name.text().strip()
        if not name:
            QMessageBox.warning(
                self,
                'Account name required',
                'Enter an account name.'
            )
            return

        starting = dlg.starting.value()
        desired_current = dlg.current.value()

        con = db()
        try:
            trades = con.execute(
                'SELECT outcome,reward_amount,risk_amount,pnl FROM trades WHERE account_id=?',
                (int(row['id']),)
            ).fetchall()

            journal_net = sum(trade_net(t) for t in trades)
            adjustment = desired_current - starting - journal_net

            con.execute(
                '''UPDATE accounts
                   SET name=?,
                       starting_balance=?,
                       current_balance=?,
                       daily_loss_limit=?,
                       max_loss=?,
                       balance_adjustment=?
                   WHERE id=?''',
                (
                    name,
                    starting,
                    desired_current,
                    dlg.daily.value(),
                    dlg.max_loss.value(),
                    adjustment,
                    int(row['id'])
                )
            )

            rebuild_account_balances(con)
            con.commit()

        except Exception as exc:
            con.rollback()
            QMessageBox.critical(
                self,
                'Could not update account',
                f'The account could not be updated.\n\n{exc}'
            )
            return
        finally:
            con.close()

        self.load()
        if self.parent_window:
            self.parent_window.refresh_all()

        QMessageBox.information(
            self,
            'Account updated',
            f'{name}\nCurrent balance: ${desired_current:,.2f}'
        )

    def load(self):
        con = db()
        rebuild_account_balances(con)
        rows = con.execute(
            'SELECT * FROM accounts ORDER BY id DESC'
        ).fetchall()
        con.close()

        self.rows = rows
        self.table.setRowCount(0)

        for r in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)

            vals = [
                r['name'],
                f'${float(r["starting_balance"] or 0):,.2f}',
                f'${float(r["current_balance"] or 0):,.2f}',
                f'${float(r["daily_loss_limit"] or 0):,.2f}',
                f'${float(r["max_loss"] or 0):,.2f}',
                r['created_at'][:10],
                ''
            ]

            for j,v in enumerate(vals):
                if j == 6:
                    b = QPushButton('EDIT ACCOUNT')
                    b.setCursor(Qt.PointingHandCursor)
                    b.clicked.connect(
                        lambda checked=False,row=r:self.edit_account(row)
                    )
                    self.table.setCellWidget(i,j,b)
                else:
                    item = QTableWidgetItem(str(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(i,j,item)

            current = self.table.item(i,2)
            if current:
                current.setFont(
                    QFont('Segoe UI',10,QFont.Weight.Bold)
                )
                current.setForeground(
                    QColor('#15803D')
                    if float(r['current_balance'] or 0)
                    >= float(r['starting_balance'] or 0)
                    else QColor('#C2414F')
                )


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('TradeLogix — Trading Journal')
        icon_path = APP_DIR / 'assets' / 'tradelogix.ico'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1500,950)
        self.setMinimumSize(1100,720)
        db().close()

        central=QWidget()
        central.setObjectName('content')
        self.setCentralWidget(central)

        root=QHBoxLayout(central)
        root.setContentsMargins(0,0,0,0)
        root.setSpacing(0)

        side=QFrame()
        side.setObjectName('sidebar')
        side.setMinimumWidth(215)
        side.setMaximumWidth(245)

        sl=QVBoxLayout(side)
        sl.setContentsMargins(14,18,14,16)
        sl.setSpacing(7)

        brand_wrap=QWidget()
        bw=QHBoxLayout(brand_wrap); bw.setContentsMargins(5,5,5,16); bw.setSpacing(9)
        brand_icon=QLabel(); brand_icon.setFixedSize(38,38)
        icon_png=APP_DIR / 'assets' / 'tradelogix_logo.png'
        if icon_png.exists():
            brand_icon.setPixmap(QPixmap(str(icon_png)).scaled(38,38,Qt.KeepAspectRatio,Qt.SmoothTransformation))
        bw.addWidget(brand_icon)
        brand=QLabel('TradeLogix')
        brand.setStyleSheet('font-size:19px;font-weight:900;color:#111827;letter-spacing:-.3px;')
        bw.addWidget(brand)
        bw.addStretch()
        sl.addWidget(brand_wrap)

        local=QLabel('WORKSPACE')
        local.setStyleSheet(
            'color:#667085;font-size:9px;font-weight:900;letter-spacing:1.4px;padding:0 7px 4px;'
        )
        sl.addWidget(local)

        account_card=QFrame(); account_card.setObjectName('glass')
        av=QVBoxLayout(account_card); av.setContentsMargins(11,10,11,10); av.setSpacing(5)
        al=QLabel('ACTIVE ACCOUNT'); al.setStyleSheet('color:#667085;font-size:9px;font-weight:900;letter-spacing:1px;')
        av.addWidget(al)
        self.global_account=ClickableComboBox(); self.global_account.setCursor(Qt.PointingHandCursor)
        self.global_account.currentIndexChanged.connect(self._global_account_changed)
        av.addWidget(self.global_account)
        self.global_balance=QLabel('$ —')
        self.global_balance.setStyleSheet('color:#111827;font-size:16px;font-weight:900;padding-top:2px;')
        av.addWidget(self.global_balance)
        self.global_pnl=QLabel('Journal P&L  —')
        self.global_pnl.setStyleSheet('color:#667085;font-size:10px;')
        av.addWidget(self.global_pnl)
        sl.addWidget(account_card)
        sl.addSpacing(7)

        self.stack=QTabWidget()
        self.stack.setObjectName('contentStack')
        self.stack.tabBar().hide()

        self.dashboard=Dashboard(self)
        self.new=NewTrade(self)
        self.history=History(self)
        self.analytics=Analytics(self)
        self.accounts=Accounts(self)

        for w,n in [
            (self.dashboard,'Dashboard'),
            (self.new,'New Trade'),
            (self.history,'Trade History'),
            (self.analytics,'Analytics'),
            (self.accounts,'Accounts')
        ]:
            self.stack.addTab(w,n)

        nav_data=[
            ('Dashboard',0),
            ('New Trade',1),
            ('Trade History',2),
            ('Analytics',3),
            ('Accounts',4)
        ]
        self.nav_buttons=[]
        for label,idx in nav_data:
            b=QPushButton(label)
            b.setObjectName('nav')
            b.setCursor(Qt.PointingHandCursor)
            b.setToolTip(label.replace('  ',''))
            b.clicked.connect(lambda checked=False,i=idx:self.set_page(i))
            sl.addWidget(b)
            self.nav_buttons.append(b)

        sl.addStretch()

        help_card=QFrame()
        help_card.setObjectName('glass')
        hv=QVBoxLayout(help_card)
        hv.setContentsMargins(12,11,12,11)
        hv.setSpacing(3)
        ht=QLabel('TRADELOGIX')
        ht.setStyleSheet('font-size:10px;font-weight:900;color:#667085;letter-spacing:.6px;')
        hb=QLabel('Everything stays on this PC.')
        hb.setWordWrap(True)
        hb.setStyleSheet('font-size:11px;color:#667085;')
        hv.addWidget(ht)
        hv.addWidget(hb)
        sl.addWidget(help_card)
        sl.addSpacing(8)

        f=QLabel('v1.0.0  •  LOCAL ONLY')
        f.setStyleSheet('color:#667085;font-size:9px;padding:0 5px;')
        sl.addWidget(f)

        root.addWidget(side)
        root.addWidget(self.stack,1)

        self.page_anim = None
        self._populate_global_account()
        self.set_page(0, animate=False)

    def _populate_global_account(self):
        con=db(); rows=con.execute('SELECT id,name,current_balance,starting_balance FROM accounts ORDER BY id DESC').fetchall(); con.close()
        self.global_account.blockSignals(True); self.global_account.clear()
        for r in rows: self.global_account.addItem(str(r['name']), int(r['id']))
        self.global_account.blockSignals(False)
        if rows:
            self.global_account.setCurrentIndex(0); self._update_global_account_meta(int(rows[0]['id']))
        else:
            self.global_balance.setText('$ —'); self.global_pnl.setText('Create an account to begin')

    def _update_global_account_meta(self, account_id):
        con=db(); r=con.execute('SELECT * FROM accounts WHERE id=?',(account_id,)).fetchone(); trades=con.execute('SELECT outcome,reward_amount,risk_amount,pnl FROM trades WHERE account_id=?',(account_id,)).fetchall() if r else []; con.close()
        if not r: return
        net=sum(trade_net(t) for t in trades)
        self.global_balance.setText(f'${float(r["current_balance"] or 0):,.2f}')
        self.global_pnl.setText(f'Journal P&L  {net:+,.2f}')
        self.global_pnl.setStyleSheet(f'color:{"#15803D" if net>=0 else "#C2414F"};font-size:10px;font-weight:700;')

    def _global_account_changed(self):
        aid=self.global_account.currentData()
        if aid is None: return
        for page, attr in ((self.dashboard,'account_filter'),(self.history,'account_filter'),(self.analytics,'account_filter')):
            combo=getattr(page,attr,None)
            if combo is not None:
                for i in range(combo.count()):
                    if combo.itemData(i)==aid:
                        combo.setCurrentIndex(i); break
        combo=getattr(self.new,'account',None)
        if combo is not None:
            for i in range(combo.count()):
                if combo.itemData(i)==aid: combo.setCurrentIndex(i); break
        self._update_global_account_meta(int(aid))

    def set_page(self,idx,animate=True):
        self.stack.setCurrentIndex(idx)
        for i,b in enumerate(self.nav_buttons):
            b.setProperty('active',i==idx)
            b.style().unpolish(b)
            b.style().polish(b)
            b.update()

        if animate:
            effect = QGraphicsOpacityEffect(self.stack)
            self.stack.setGraphicsEffect(effect)
            self.page_anim = QPropertyAnimation(effect,b'opacity',self)
            self.page_anim.setDuration(150)
            self.page_anim.setStartValue(0.72)
            self.page_anim.setEndValue(1.0)
            self.page_anim.setEasingCurve(QEasingCurve.OutCubic)
            self.page_anim.finished.connect(lambda: self.stack.setGraphicsEffect(None))
            self.page_anim.start()

        if idx==1:
            self.new.load_accounts()

    def refresh_all(self):
        # Canonical refresh path used after create/edit operations.
        pages = (
            self.new.load_accounts,
            self.dashboard.load,
            self.history.load,
            self.analytics.load,
            self.accounts.load,
        )
        for loader in pages:
            loader()
            QApplication.processEvents()
        self._populate_global_account()



def main():
    app=QApplication(sys.argv)
    app.setStyle('Fusion')
    icon_path = APP_DIR / 'assets' / 'tradelogix.ico'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    app.setStyleSheet(STYLE)
    w=MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__=='__main__':
    main()
