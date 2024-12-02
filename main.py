from datetime import datetime
import os
import sys
import traceback
import uuid

import ziamath as zm
import cairosvg_min as cairosvg

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5 import uic

APP_NAME = 'EqualZ'
APP_VERSION = 1

APP_DIR = os.path.dirname(os.path.realpath(__file__))

IS_FROZEN = getattr(sys, "frozen", False)
IS_PORTABLE = IS_FROZEN and os.path.isfile(os.path.join(APP_DIR, '..', 'portable'))

if IS_FROZEN:
    if IS_PORTABLE:
        DATA_DIR = os.path.join(APP_DIR, '..', 'data')
    else:
        DATA_DIR = os.path.join(os.environ['USERPROFILE'], f'.{APP_NAME.lower()}')
else:
    DATA_DIR = os.path.join(APP_DIR, 'data')

if not os.path.isdir(DATA_DIR):
    os.mkdir(DATA_DIR)

BOOKMARKS_DIR = os.path.join(DATA_DIR, 'bookmarks')
if not os.path.isdir(BOOKMARKS_DIR):
    os.mkdir(BOOKMARKS_DIR)

HISTORY_DIR = os.path.join(DATA_DIR, 'history')
if not os.path.isdir(HISTORY_DIR):
    os.mkdir(HISTORY_DIR)

class RenderMode():
    Display = 0
    Inline = 1
    Text = 2
    MathML = 3


########################################
#
########################################
class Main(QMainWindow):

    def __init__(self):
        super().__init__()

        self._text_filename = None
        self._current_png = None
        self._current_svg = None

        QResource.registerResource(os.path.join(APP_DIR, 'resources', 'main.rcc'))
        uic.loadUi(os.path.join(APP_DIR, 'resources', 'main.ui'), self)

        qss = QFile(':/stylesheet.qss')
        qss.open(QFile.ReadOnly)
        qApp.setStyleSheet(bytes(qss.readAll()).decode())

        self._state = QSettings(os.path.join(DATA_DIR, 'state.ini'), QSettings.IniFormat)

        self._bookmarks = self._state.value('Bookmarks')
        if type(self._bookmarks) != dict:
            self._bookmarks = {}

        self._history = self._state.value('History')
        if type(self._history) != dict:
            self._history = {}

        self.renderButton.clicked.connect(self.slot_render)

        self.toolButtonColor.clicked.connect(self.slot_select_color)
        self.toolButtonBgColor.setColor(QColor(Qt.white))
        self.toolButtonBgColor.clicked.connect(self.slot_select_bgcolor)
        self.toolButtonBgColor.hide()

        self.toolButtonNewEquation.clicked.connect(self.slot_new_equation)
        self.toolButtonBookmark.clicked.connect(self.slot_bookmark_add)

        self.button_group_render_mode = QButtonGroup(self)
        self.button_group_render_mode.addButton(self.renderModeDisplay, RenderMode.Display)
        self.button_group_render_mode.addButton(self.renderModeInline, RenderMode.Inline)
        self.button_group_render_mode.addButton(self.renderModeText, RenderMode.Text)
        self.button_group_render_mode.addButton(self.renderModeMathML, RenderMode.MathML)

        self.editor.textChanged.connect(self.slot_text_changed)

        self.setup_actions()
        self.setup_render_label()
        self.setup_bookmarks()
        self.setup_history()

        self.toolBarTemplates.addWidget(self.templatesBar)

        symbol_settings = QSettings(os.path.join(APP_DIR, 'resources', 'symbols', 'symbols.ini'),
                QSettings.IniFormat)
        for g in symbol_settings.childGroups():
            group_dir = os.path.join(APP_DIR, 'resources', 'symbols', g)

            symbol_settings.beginGroup(g)

            tb = QToolButton(self)
            tb.setToolTip(g)
            tb.setIcon(QIcon(os.path.join(group_dir, symbol_settings.value('symbols/1/icon'))))
            tb.setPopupMode(QToolButton.MenuButtonPopup)
            tb.triggered.connect(self.slot_symbol_selected)
            self.toolBarSymbols.addWidget(tb)

            menu = QMenu(tb)
            tb.setMenu(menu)
            cnt = int(symbol_settings.value('symbols/size'))
            for i in range(1, cnt + 1):
                action = menu.addAction(QIcon(os.path.join(group_dir, symbol_settings.value(f'symbols/{i}/icon'))),
                        symbol_settings.value(f'symbols/{i}/name'))
                action.setData(symbol_settings.value(f'symbols/{i}/latex'))
                if i == 1:
                    tb.setDefaultAction(action)

            symbol_settings.endGroup()

        templates_settings = QSettings(os.path.join(APP_DIR, 'resources', 'templates', 'templates.ini'),
                QSettings.IniFormat)
        for g in templates_settings.childGroups():
            group_dir = os.path.join(APP_DIR, 'resources', 'templates', g)
            templates_settings.beginGroup(g)

            page = QWidget(self)
            self.templatesBar.addTab(page, g)

            layout = QHBoxLayout()
            layout.setContentsMargins(1, 1, 1, 1)
            page.setLayout(layout)

            for k in templates_settings.allKeys():
                v = templates_settings.value(k)
                if type(v) == list:
                    v = ','.join(v)
                ico = QIcon(os.path.join(group_dir, k))
                s = ico.availableSizes()[0]
                s.setHeight(46)
                tb = QToolButton(self)
                tb.setIconSize(s)
                tb.setIcon(ico)
                layout.addWidget(tb)
                tb.pressed.connect(lambda tex=v: self.editor.insertPlainText(tex))

            templates_settings.endGroup()

            layout.addStretch()

        # restore saved state
        val = self._state.value('MainWindow/Geometry')
        if val:
            self.restoreGeometry(val)
        val = self._state.value('MainWindow/State')
        if val:
            self.restoreState(val)
        val = self._state.value('MainWindow/Splitter')
        if val:
            self.splitter.restoreState(val)
        else:
            self.splitter.setSizes([300, 100])
        val = self._state.value('Editor/Font')
        if val:
            font = QFont()
            font.fromString(val)
            self.editor.setFont(font)

        self.show()

        self.actionViewBookmarks.setChecked(self.dockWidgetBookmarks.isVisible())
        self.actionViewHistory.setChecked(self.dockWidgetHistory.isVisible())

    ########################################
    #
    ########################################
    def setup_actions(self):
        self.actionAbout.triggered.connect(self.slot_about)
        self.actionBookmark.triggered.connect(self.slot_bookmark_add)
        self.actionEditDelete.triggered.connect(lambda: self.editor.insertPlainText(''))
        self.actionEditorFont.triggered.connect(self.slot_set_editor_font)
        self.actionExportAs.triggered.connect(self.slot_export_as)
        self.actionNewEquation.triggered.connect(self.slot_new_equation)
        self.actionOpenTextFile.triggered.connect(self.slot_open_text_file)
        self.actionRender.triggered.connect(self.slot_render)
        self.actionSaveTextFile.triggered.connect(self.slot_save_text_file)

    ########################################
    #
    ########################################
    def setup_render_label(self):

        def _context_menu_requested(pos):
            cm = QMenu(self.renderLabel)
            cm.addAction(self.actionBookmark)
            cm.addAction(self.actionExportAs)
            cm.exec(QCursor.pos())

        self.renderLabel.customContextMenuRequested.connect(_context_menu_requested)

    ########################################
    #
    ########################################
    def setup_bookmarks(self):

        def _context_menu_requested(pos):
            if self.listWidgetBookmarks.count() == 0:
                return
            cm = QMenu(self.listWidgetBookmarks)
            a = cm.addAction('Load Equation')
            a.triggered.connect(lambda: self.slot_bookmark_double_clicked(
                    self.listWidgetBookmarks.currentItem()))
            cm.addSeparator()
            a = cm.addAction('Remove Equation')
            a.triggered.connect(self.slot_bookmark_remove)
            cm.exec(QCursor.pos())

        self.listWidgetBookmarks.customContextMenuRequested.connect(_context_menu_requested)

        self._bookmarks = dict(sorted(self._bookmarks.items(), key=lambda row: row[1]['datetime'],
                reverse=True))

        for uid, row in self._bookmarks.items():
            lwi = QListWidgetItem(self.listWidgetBookmarks)
            lwi.setIcon(QIcon(os.path.join(BOOKMARKS_DIR, f'{uid}.png')))
            lwi.setData(Qt.UserRole, uid)
            lwi.setToolTip(f"Saved on: {row['datetime']}")

        self.listWidgetBookmarks.itemDoubleClicked.connect(self.slot_bookmark_double_clicked)

        self.dockWidgetBookmarks.visibilityChanged.connect(lambda _:
                self.actionViewBookmarks.setChecked(self.dockWidgetBookmarks.isVisible()))

    ########################################
    #
    ########################################
    def setup_history(self):

        def _context_menu_requested(pos):
            if self.listWidgetHistory.count() == 0:
                return
            cm = QMenu(self.listWidgetHistory)
            a = cm.addAction('Load Equation')
            a.triggered.connect(lambda: self.slot_history_double_clicked(self.listWidgetHistory.currentItem()))
            cm.addSeparator()
            a = cm.addAction('Remove Equation')
            a.triggered.connect(self.slot_history_remove)
            cm.addSeparator()
            a = cm.addAction('Clear All History')
            a.triggered.connect(self.slot_history_clear)

            cm.exec(QCursor.pos())

        self.listWidgetHistory.customContextMenuRequested.connect(_context_menu_requested)

        self._history = dict(sorted(self._history.items(), key=lambda row: row[1]['datetime'], reverse=True))

        for uid, row in self._history.items():
            lwi = QListWidgetItem(self.listWidgetHistory)
            lwi.setIcon(QIcon(os.path.join(HISTORY_DIR, f'{uid}.png')))
            lwi.setData(Qt.UserRole, uid)
            lwi.setToolTip(f"Saved on: {row['datetime']}")

        self.listWidgetHistory.itemDoubleClicked.connect(self.slot_history_double_clicked)

        self.dockWidgetHistory.visibilityChanged.connect(lambda _: self.actionViewHistory.setChecked(
                self.dockWidgetHistory.isVisible()))

    def __EVENTS(): pass

    ########################################
    #
    ########################################
    def closeEvent(self, e):
        self._state.setValue('MainWindow/Geometry', self.saveGeometry())
        self._state.setValue('MainWindow/State', self.saveState())
        self._state.setValue('MainWindow/Splitter', self.splitter.saveState())
        self._state.setValue('Editor/Font', self.editor.font().toString())
        self._state.setValue('Bookmarks', self._bookmarks)
        self._state.setValue('History', self._history)

    ########################################
    #
    ########################################
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            if e.mimeData().urls()[0].toLocalFile().lower().endswith('.txt'):
                e.accept()

    ########################################
    #
    ########################################
    def dropEvent(self, e):
        e.accept()
        fn = e.mimeData().urls()[0].toLocalFile()
        with open(fn, 'r') as f:
            self.editor.setPlainText(f.read())
        self._text_filename = fn

    def __SLOTS(): pass

    ########################################
    #
    ########################################
    def slot_new_equation(self):
        self.actionExportAs.setDisabled(True)
        self._text_filename = None
        self.editor.clear()
        self.renderLabel.clear()

    ########################################
    #
    ########################################
    def slot_about(self):
        QMessageBox.about(
            self,
            f'About {APP_NAME}',
            f'<b>{APP_NAME} v0.{APP_VERSION}</b><br><br>'\
            'A simple standalone LaTeX Math and MathML Equation editor<br>based on Python, PyQt5, '\
            '<a href="https://pypi.org/project/ziamath/">Ziamath</a> and '\
            '<a href="https://cairosvg.org/">CairoSVG</a>.<br><br>'\
            f'<a href="https://github.com/59de44955ebd/equalz">{APP_NAME} on GitHub</a>'
        )

    ########################################
    #
    ########################################
    def slot_set_editor_font(self):
        font, ok = QFontDialog.getFont(self.editor.font(), self)
        if ok:
            self.editor.setFont(font)

    ########################################
    #
    ########################################
    def slot_bookmark_add(self):
        bookmarks_png = os.path.join(BOOKMARKS_DIR, f'{self._current_uid}.png')
        with open(bookmarks_png, 'wb') as f:
            f.write(self._current_png)

        dt = datetime.now().isoformat(' ', timespec='seconds')

        self._bookmarks[self._current_uid] = {
            'datetime': dt,
            'tex': self._current_tex,
            'color': self._current_color,
            'bgcolor': self._current_bgcolor,
            'fontsize': self._current_fontsize,
            'render_mode': self._current_rendermode,
        }

        lwi = QListWidgetItem()
        lwi.setIcon(QIcon(bookmarks_png))
        lwi.setData(Qt.UserRole, self._current_uid)
        lwi.setToolTip(f"Saved on: {dt}")
        self.listWidgetBookmarks.insertItem(0, lwi)

    ########################################
    #
    ########################################
    def slot_bookmark_remove(self):
        lwi = self.listWidgetBookmarks.currentItem()
        if lwi is None:
            return
        uid = lwi.data(Qt.UserRole)
        png = os.path.join(BOOKMARKS_DIR, f'{uid}.png')
        if os.path.isfile(png):
            os.unlink(png)
        del self._bookmarks[uid]
        self.listWidgetBookmarks.takeItem(self.listWidgetBookmarks.row(lwi))

    ########################################
    #
    ########################################
    def slot_bookmark_double_clicked(self, lwi):
        if lwi is None:
            return
        uid = lwi.data(Qt.UserRole)
        bm = self._bookmarks[uid]

        self._text_filename = None
        self.renderLabel.clear()
        self.editor.setPlainText(bm['tex'])
        self.spinBoxFontSize.setValue(bm['fontsize'])
        self.toolButtonColor.setColor(QColor(bm['color']))
        if bm['bgcolor']:
            self.checkBoxTransparent.setChecked(False)
            self.toolButtonBgColor.setColor(QColor(bm['bgcolor']))
        else:
            self.checkBoxTransparent.setChecked(True)
        self.button_group_render_mode.button(bm['render_mode']).setChecked(True)
        self.slot_render()

    ########################################
    #
    ########################################
    def slot_history_clear(self):
        res = QMessageBox.question(self, 'Clear History',
                'Do you really want to remove all equations from the history?')
        if res != QMessageBox.Yes:
            return

        for uid in self._history.keys():
            png = os.path.join(HISTORY_DIR, f'{uid}.png')
            if os.path.isfile(png):
                os.unlink(png)
        self._history = {}
        self.listWidgetHistory.clear()

    ########################################
    #
    ########################################
    def slot_history_remove(self):
        lwi = self.listWidgetHistory.currentItem()
        if lwi is None:
            return
        uid = lwi.data(Qt.UserRole)
        png = os.path.join(HISTORY_DIR, f'{uid}.png')
        if os.path.isfile(png):
            os.unlink(png)
        del self._history[uid]
        self.listWidgetHistory.takeItem(self.listWidgetHistory.row(lwi))

    ########################################
    #
    ########################################
    def slot_history_double_clicked(self, lwi):
        if lwi is None:
            return
        uid = lwi.data(Qt.UserRole)
        bm = self._history[uid]
        self._text_filename = None
        self.renderLabel.clear()
        self.editor.setPlainText(bm['tex'])
        self.spinBoxFontSize.setValue(bm['fontsize'])
        self.toolButtonColor.setColor(QColor(bm['color']))
        if bm['bgcolor']:
            self.checkBoxTransparent.setChecked(False)
            self.toolButtonBgColor.setColor(QColor(bm['bgcolor']))
        else:
            self.checkBoxTransparent.setChecked(True)
        self.button_group_render_mode.button(bm['render_mode']).setChecked(True)
        self.slot_render(add_to_history=False)

    ########################################
    #
    ########################################
    def slot_text_changed(self):
        self.actionBookmark.setEnabled(False)
        self.toolButtonBookmark.setEnabled(False)
        is_empty = self.editor.document().isEmpty()
        self.renderButton.setDisabled(is_empty)
        self.actionRender.setDisabled(is_empty)
        self.actionSaveTextFile.setDisabled(is_empty)

    ########################################
    #
    ########################################
    def slot_symbol_selected(self, action):
        self.editor.insertPlainText(action.data())

    ########################################
    #
    ########################################
    def slot_open_text_file(self):
        fltr = 'Text File (*.txt)'
        fn, _ = QFileDialog.getOpenFileName(self, 'Open Text File...', os.path.join(APP_DIR, 'equation'), fltr)
        if not fn:
            return
        with open(fn, 'r') as f:
            self.editor.setPlainText(f.read())
        self._text_filename = fn

    ########################################
    #
    ########################################
    def slot_save_text_file(self):
        if self._text_filename is None:
            fltr = 'Text File (*.txt)'
            fn, _ = QFileDialog.getSaveFileName(self, 'Save Text File...', os.path.join(APP_DIR, 'equation'), fltr)
            if not fn:
                return
            self._text_filename = fn
        with open(self._text_filename, 'w') as f:
            f.write(self.editor.toPlainText())

    ########################################
    #
    ########################################
    def slot_export_as(self):
        tex = self.editor.toPlainText()
        if not tex:
            return

        fltr = 'BMP File (*.bmp);;JPEG File (*.jpg);;PNG File (*.png);;PDF File (*.pdf);;SVG File (*.svg);;'\
            'TeX File (*.tex);;TIFF File (*.tif)'
        fn, fltr = QFileDialog.getSaveFileName(self, 'Save Equation as...', os.path.join(APP_DIR, 'equation'), fltr)
        if not fn:
            return
        fmt = fltr.split(' ')[0]

        if fmt == 'TeX':
            with open(fn, 'w') as f:
                f.write(r'''\documentclass[10pt]{article} % required
\pagestyle{empty} % required
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{color}
\usepackage[T1]{fontenc}

\begin{document}\definecolor{fgC}{rgb}{''')
                r, g, b, _ = self.toolButtonColor.color().getRgbF()
                f.write('{},{},{}'.format(r, g, b))
                f.write(r'}\color{fgC}')
                if not self.checkBoxTransparent.isChecked():
                    f.write(r'\definecolor{bgC}{rgb}{')
                    r, g, b, _ = self.toolButtonBgColor.color().getRgbF()
                    f.write('{},{},{}'.format(r, g, b))
                    f.write(r'}\pagecolor{bgC}')
                f.write(r' \[')
                f.write(tex)
                f.write(r'\]\end{document}')

        else:
            try:
                if fmt == 'BMP' or fmt == 'JPEG':
                    # no transparency support, so always use current bgcolor
                    png_data = cairosvg.svg2png(
                        bytestring=self._current_svg,
                        background_color=self.toolButtonBgColor.color().name()
                    )
                    pm = QPixmap()
                    pm.loadFromData(png_data, 'png')
                    pm.save(fn, quality=100)
                elif fmt == 'TIFF':
                    pm = QPixmap()
                    pm.loadFromData(self._current_png, 'png')
                    pm.save(fn, quality=100)
                else:
                    with open(fn, 'wb') as f:
                        if fmt == 'PNG':
                            f.write(self._current_png)
                        elif fmt == 'PDF':
                            f.write(cairosvg.svg2pdf(
                                bytestring=self._current_svg,
                                background_color=self._current_bgcolor if self._current_bgcolor else None
                            ))
                        elif fmt == 'SVG':
                            f.write(self._current_svg.encode())
            except Exception as e:
                print(e)
                self.statusBar.showMessage(str(e))

    ########################################
    #
    ########################################
    def slot_select_color(self):
        col = QColorDialog.getColor(self.toolButtonColor.color(), self)
        if col.isValid():
            self.toolButtonColor.setColor(col)

    ########################################
    #
    ########################################
    def slot_select_bgcolor(self):
        col = QColorDialog.getColor(self.toolButtonBgColor.color(), self)
        if col.isValid():
            self.toolButtonBgColor.setColor(col)

    ########################################
    #
    ########################################
    def slot_render(self, _=None, add_to_history=True):
        tex = self.editor.toPlainText()
        if not tex:
            return
        self.statusBar.clearMessage()
        try:
            self._current_tex = tex
            self._current_rendermode = self.button_group_render_mode.checkedId()
            self._current_color = self.toolButtonColor.color().name()
            self._current_bgcolor = '' if self.checkBoxTransparent.isChecked() else self.toolButtonBgColor.color().name()
            self._current_fontsize = self.spinBoxFontSize.value()

            if self._current_rendermode == RenderMode.MathML:
                zm.config.math.color = self._current_color
                res = zm.Math(
                    tex,
                    size=self._current_fontsize
                )
            elif self._current_rendermode == RenderMode.Text:
                #######################################
                # Mixed text and latex math. Inline math delimited by single $..$, and display-mode math delimited
                # by double $$…$$. Can contain multiple lines. Drawn to SVG
                #######################################
                res = zm.zmath.Text(
                    tex,
                    size=self._current_fontsize,
                    color=self._current_color,
                    linespacing=1.6,
                )
            else:
                ########################################
                # Create Math Renderer from a single LaTeX expression.
                ########################################
                res = zm.Latex(
                    tex,
                    size=self._current_fontsize,
                    color=self._current_color,
                    inline=self._current_rendermode==RenderMode.Inline
                )

            self._current_uid = str(uuid.uuid4())
            self._current_svg = res.svg()
            self._current_png = cairosvg.svg2png(
                bytestring=self._current_svg,
                background_color=self._current_bgcolor if self._current_bgcolor else None
            )

            pm = QPixmap()
            pm.loadFromData(self._current_png, 'png')
            self.renderLabel.setPixmap(pm)

            if add_to_history:
                history_png = os.path.join(HISTORY_DIR, f'{self._current_uid}.png')
                with open(history_png, 'wb') as f:
                    f.write(self._current_png)

                dt = datetime.now().isoformat(' ', timespec='seconds')

                self._history[self._current_uid] = {
                    'datetime': dt,
                    'tex': self._current_tex,
                    'color': self._current_color,
                    'bgcolor': self._current_bgcolor,
                    'fontsize': self._current_fontsize,
                    'render_mode': self._current_rendermode,
                }

                lwi = QListWidgetItem()
                lwi.setIcon(QIcon(history_png))
                lwi.setData(Qt.UserRole, self._current_uid)
                lwi.setToolTip(f"Saved on: {dt}")
                self.listWidgetHistory.insertItem(0, lwi)

            self.actionBookmark.setEnabled(True)
            self.toolButtonBookmark.setEnabled(True)
            self.actionExportAs.setEnabled(True)
        except Exception as e:
            print('ERROR', e)
            self.statusBar.showMessage(f'Error: {e}')
            self.actionBookmark.setEnabled(False)
            self.toolButtonBookmark.setEnabled(False)
            self.actionExportAs.setEnabled(False)


########################################
#
########################################
if __name__ == '__main__':
    sys.excepthook = traceback.print_exception
    QApplication.setStyle('Fusion')
    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec_())
