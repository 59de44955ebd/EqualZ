from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont
from PyQt5.QtWidgets import QPlainTextEdit


########################################
#
########################################
class HighlightingRule():
    def __init__(self, pattern, format):
        self.pattern = pattern
        self.format = format


########################################
#
########################################
class LatexHighlighter(QSyntaxHighlighter):

    ########################################
    #
    ########################################
    def __init__(self, parent=None):
        super().__init__(parent)

        self.rules = []

        comment_format = QTextCharFormat()  # starting with '%'
        comment_format.setForeground(Qt.gray)
        comment_format.setFontWeight(QFont.Normal)
        self.rules.append(HighlightingRule(QRegExp("%.*"), comment_format))

        control_format = QTextCharFormat()  # words starting with '\'
        control_format.setForeground(Qt.blue)
        control_format.setFontWeight(QFont.Bold)
        self.rules.append(HighlightingRule(QRegExp("\\\\[A-Za-z]*"), control_format))

        braces_format = QTextCharFormat()  # {, }
        braces_format.setForeground(Qt.red)
        braces_format.setFontWeight(QFont.Normal)
        self.rules.append(HighlightingRule(QRegExp("[\\{\\}\\(\\)\\[\\]\\^\\_]"), braces_format))

    ########################################
    #
    ########################################
    def highlightBlock(self, text):
        for rule in self.rules:
            idx = rule.pattern.indexIn(text)
            while idx >= 0:
                length = rule.pattern.matchedLength()
                self.setFormat(idx, length, rule.format)
                idx = rule.pattern.indexIn(text, idx + length)
        self.setCurrentBlockState(0)


########################################
#
########################################
class LatexEditor(QPlainTextEdit):

    ########################################
    #
    ########################################
    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlighter = LatexHighlighter(self.document())
