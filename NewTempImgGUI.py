from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontDatabase, QFontInfo, QImage, QPainter
from PyQt5.QtWidgets import QDialog, QFontDialog, QMessageBox

from DataBase import DataBase
from MyLogger import log_exception
from ui.Ui_NewTempImg import Ui_NewTempImg
from utils import remove_namespace


class NewTempImgGUI(QDialog, Ui_NewTempImg):
    def __init__(self, parent=None, name=''):
        super().__init__(parent)
        self.setupUi(self)

        self.editName.setText(remove_namespace(name))

        self.font = QFontDatabase.systemFont(QFontDatabase.GeneralFont)
        self.font.setPointSize(32)
        info = QFontInfo(self.font)
        self.editFont.setText(f'{info.family()} {info.pointSize()}')
        self.editFont.mouseDoubleClickEvent = self.edit_font_mouse_double_click_event

    def edit_font_mouse_double_click_event(self, _):
        font, ok = QFontDialog.getFont(self.font, self)
        if not ok:
            return

        self.font = font
        self.editFont.setText(f'{font.family()} {font.pointSize()}')

    @log_exception(True)
    def accept(self):
        if not self.editName.text():
            QMessageBox.warning(self, self.tr('Warning'), self.tr('Please enter name'))
            return

        if self.path().exists():
            reply = QMessageBox.question(self, self.tr('Information'),
                                         self.tr('File already exists. Do you want to continue?'),
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No:
                return

        self.create_img()
        super().accept()

    @log_exception(True)
    def create_img(self):
        image = QImage(self.spinWidth.value(), self.spinHeight.value(), QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setFont(self.font)
        painter.setPen(Qt.GlobalColor.black)
        painter.drawText(image.rect(), Qt.AlignmentFlag.AlignCenter, self.editText.text())
        painter.end()

        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(str(path))

    def path(self) -> Path:
        return DataBase.CurModPath / 'Resource/Texture2D' / f'{self.editName.text()}.png'

    def ref_name(self) -> str:
        return f'{DataBase.CurModName}:{Path(self.editName.text()).stem}'
