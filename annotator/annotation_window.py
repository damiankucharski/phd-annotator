import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageQt

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QDialog
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from annotation_box import AnnotationBox, AnnotationLabel
from open_annotated_dialog import OpenAnnotatedDialog

from pathlib import Path

from gems.io import Json
from collections import defaultdict

import pandas as pd


JSON_PATH = Path(__file__).parent / "data" / "annotations.json"


class AnnotationWindow(QWidget):
    def __init__(self, data_directory):
        super().__init__()

        self.cur_im_index = -1

        self.annotations_dict = defaultdict(lambda: defaultdict(bool))
        self.annotations_dict.update(Json.load(JSON_PATH))

        self.data_directory = Path(data_directory)
        self.file_paths = pd.Series(list(self.data_directory.rglob("*.jpg")))

        self.setMinimumWidth(500)
        self.setMinimumHeight(720)

        self.main_layout = QVBoxLayout()

        self.path_label = QLabel()
        self.path_label.setFixedHeight(16)
        self.path_label.setAlignment(Qt.AlignCenter)

        self.image_label = QLabel()
        self.select_annotation_check = AnnotationBox()

        self.next_annotation_button = QPushButton("Next")
        self.next_annotation_button.clicked.connect(self.next_image)

        self.open_annotated_button = QPushButton("Choose from annotated")
        self.open_annotated_button.clicked.connect(self._choose_annotated)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_window)

        self.show_only_unlabeled_checkbox = QCheckBox("Show only unlabeled images")

        self.main_layout.addWidget(self.path_label)
        self.main_layout.addWidget(self.image_label)
        self.main_layout.addWidget(self.select_annotation_check)
        self.main_layout.addWidget(self.next_annotation_button)
        self.main_layout.addWidget(self.open_annotated_button)
        self.main_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.show_only_unlabeled_checkbox)

        #####
        self.current_annotation = None
        self.next_image()

        self.setLayout(self.main_layout)

    def next_image(self, image_index=None):
        if image_index is not None and image_index is not False:
            self.cur_im_index = image_index
        else:
            self._find_next_image_index()

        cur_relative_path = self._get_cur_relative_path()

        np_image = plt.imread(self.file_paths[self.cur_im_index])
        np_image_transposed = np.transpose(np_image, (1, 0, 2))[:, ::-1, :]
        pil_image = Image.fromarray(np_image_transposed)
        pil_image.thumbnail((500, 500), Image.ANTIALIAS)

        self.loaded_image = ImageQt.ImageQt(pil_image)
        self.image_label.setPixmap(QPixmap.fromImage(self.loaded_image))
        self.current_annotation = self.annotations_dict[cur_relative_path]
        self.select_annotation_check.update_annotation(self.current_annotation)

        self.path_label.setText(cur_relative_path)

        self._save_annotations()

    def save_annotation(self):
        relative_path = self._get_cur_relative_path()
        selected_annotation = self.select_annotation_radio.selected_annotation_option.value

        self.annotations_dict[relative_path] = selected_annotation

    def close_window(self):
        self.close()

    def _get_cur_relative_path(self):
        current_path = self.file_paths[self.cur_im_index]
        relative_path = current_path.relative_to(self.data_directory)
        return str(relative_path)

    def _next_image_index(self):
        return self.cur_im_index + 1 if self.cur_im_index < len(self.file_paths) else 0

    def _find_next_image_index(self):
        self.cur_im_index = self._next_image_index()

        if self.show_only_unlabeled_checkbox.isChecked():
            cur_relative_path = self._get_cur_relative_path()

            while cur_relative_path in self.annotations_dict:
                self.cur_im_index = self._next_image_index()
                cur_relative_path = self._get_cur_relative_path()

    def _save_annotations(self):
        to_save = {}
        for k, v in self.annotations_dict.items():
            to_save[k] = dict(v)

        Json.save(JSON_PATH, to_save)

    def _find_annotation_index(self, path):
        entry = self.file_paths[self.file_paths == path]
        return entry.index[0]

    def _choose_annotated(self):

        annotated = [key for key, val in self.annotations_dict.items() if any(list(val.values()))]

        dlg = OpenAnnotatedDialog(annotated)

        if dlg.exec_() == QDialog.Accepted:
            index = self._find_annotation_index(self.data_directory / dlg.annotations.currentText())
            self.next_image(index)
