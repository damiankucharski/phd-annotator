from PySide6.QtWidgets import QWidget, QVBoxLayout, QCheckBox

from enum import Enum
from pandas import Series

from typing import List


class AnnotationLabel(Enum):
    Unreadable = "Unreadable"
    Obscured = "Parts of image are obscured"
    Low_Contrast = "Low contrast between signal and image"
    Signals_Intersect = "Signals intersect"
    Good_Quality = "Good quality and good contrast"


class AnnotationBox(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.checkboxes: List[QCheckBox] = self._create_checkboxes()
        for checkbox in self.checkboxes.values():
            self.layout.addWidget(checkbox)

        self.selected_labels = None

    def _create_checkboxes(self):
        checkboxes = {}

        for data in AnnotationLabel:
            checkbox = QCheckBox(data.value)
            checkbox.clicked.connect(self.onClicked)
            checkbox.label = data.value
            checkboxes[data.value] = checkbox

        return checkboxes

    def update_annotation(self, annotation: Series):
        self.selected_labels = annotation
        for data in AnnotationLabel:
            selected = annotation[data.value]
            if selected:
                self.checkboxes[data.value].setChecked(True)
            else:
                self.checkboxes[data.value].setChecked(False)

    def onClicked(self):
        checkbox: QCheckBox = self.sender()
        if checkbox.isChecked():
            self.selected_labels[checkbox.label] = True
        else:
            self.selected_labels[checkbox.label] = False
