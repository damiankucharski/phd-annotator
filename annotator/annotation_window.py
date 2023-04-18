import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageQt

from sys import exit

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QCheckBox, QDialog, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

from .annotation_box import AnnotationBox, AnnotationLabel
from .open_annotated_dialog import OpenAnnotatedDialog

from pathlib import Path

import pandas as pd

CSV_PATH = Path(__file__).parent / "../../../.." / "annotations.csv"


class AnnotationWindow(QWidget):
    def __init__(self, data_directory):
        super().__init__()

        self.cur_im_index = -1

        self.data_directory = Path(data_directory)
        self.file_paths = pd.Series(list(self.data_directory.rglob("*.jpg")))
        self._check_if_any_filenames()

        self.annotations_frame = self._create_current_annotations_frame()
        self.all_annotations_frame = self._load_annotations_csv()

        self.annotations_frame.update(self.all_annotations_frame)

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

        self.previous_annotation_button = QPushButton("Previous")
        self.previous_annotation_button.clicked.connect(self.previous_image)

        self.open_annotated_button = QPushButton("Choose from annotated")
        self.open_annotated_button.clicked.connect(self._choose_annotated)

        self.save_annotations_button = QPushButton("Save annotations")
        self.save_annotations_button.clicked.connect(self._save_annotations)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_window)

        self.show_only_unlabeled_checkbox = QCheckBox("Show only unlabeled images")

        self.main_layout.addWidget(self.path_label)
        self.main_layout.addWidget(self.image_label)
        self.main_layout.addWidget(self.select_annotation_check)
        self.main_layout.addWidget(self.next_annotation_button)
        self.main_layout.addWidget(self.previous_annotation_button)
        self.main_layout.addWidget(self.open_annotated_button)
        self.main_layout.addWidget(self.save_annotations_button)
        self.main_layout.addWidget(self.close_button)
        self.main_layout.addWidget(self.show_only_unlabeled_checkbox)

        #####
        self.current_annotation = None
        self.next_image()

        self.setLayout(self.main_layout)

    def next_image(self, image_index=None, previous=False):
        if image_index is not None and image_index is not False:
            self.cur_im_index = image_index
        else:
            self._find_next_image_index(previous=previous)

        cur_relative_path = str(self._get_cur_relative_path())

        np_image = plt.imread(self.file_paths[self.cur_im_index])
        np_image_transposed = np.transpose(np_image, (1, 0, 2))[:, ::-1, :]
        pil_image = Image.fromarray(np_image_transposed)
        pil_image.thumbnail((500, 500), Image.ANTIALIAS)

        self.loaded_image = ImageQt.ImageQt(pil_image)
        self.image_label.setPixmap(QPixmap.fromImage(self.loaded_image))
        self.current_annotation = self.annotations_frame.loc[cur_relative_path]
        self.current_annotation.Seen = True

        self.select_annotation_check.update_annotation(self.current_annotation)

        self.path_label.setText(cur_relative_path)

    def previous_image(self):
        self.next_image(previous=True)

    def close_window(self):
        self.close()

    def _get_relative_path(self, path) -> Path:
        relative_path = path.relative_to(self.data_directory.parent)
        return relative_path

    def _get_cur_relative_path(self) -> Path:
        current_path = self.file_paths[self.cur_im_index]
        return self._get_relative_path(current_path)

    def _next_image_index(self, previous=False):
        if previous:
            return self.cur_im_index - 1 if self.cur_im_index > 0 else len(self.file_paths)
        else:
            return self.cur_im_index + 1 if self.cur_im_index < (len(self.file_paths) - 1) else 0

    def _find_next_image_index(self, previous=False):
        if self.show_only_unlabeled_checkbox.isChecked():
            index_list = np.array(self.file_paths.index)
            un_annotated_mask = ~self._get_annotated_mask()
            available = index_list[un_annotated_mask]

            if len(available) > 0:
                if previous:
                    mask = available < self.cur_im_index
                    if any(mask):
                        mask = np.cumsum(mask)
                        next_ind = available[np.argmax(mask)]
                        self.cur_im_index = next_ind
                    else:
                        self.cur_im_index = available[-1]

                else:
                    mask = available > self.cur_im_index
                    if any(mask):
                        self.cur_im_index = available[np.argmax(mask)]
                    else:
                        self.cur_im_index = available[0]
            else:
                self.cur_im_index = 0
                self._annotation_finished_dialog()
        else:
            self.cur_im_index = self._next_image_index(previous)

    def _save_annotations(self):
        merged_df = self.annotations_frame.merge(self.all_annotations_frame, how="outer", on="Filepath")
        merged_df = merged_df.fillna(value=False)
        self.all_annotations_frame = self.annotations_frame.combine_first(self.all_annotations_frame)
        self.all_annotations_frame.to_csv(CSV_PATH)
        self._info_dialog(f"Anootations saved to {str(CSV_PATH.resolve())}")

    def _find_annotation_index(self, path):
        path = self.data_directory.parent / path
        print(self.file_paths)
        print(path)
        entry = self.file_paths[self.file_paths == path]
        return entry.index[0]

    def _get_annotated_mask(self):
        return (self.annotations_frame.iloc[:, :-1] == True).any(axis=1)

    def _choose_annotated(self):
        annotated_names = list(self.annotations_frame.index[self._get_annotated_mask()])

        dlg = OpenAnnotatedDialog(annotated_names)

        if dlg.exec_() == QDialog.Accepted:
            index = self._find_annotation_index(dlg.annotations.currentText())
            self.next_image(image_index=index)

    def _create_current_annotations_frame(self):
        relative_paths = [str(self._get_relative_path(path)) for path in self.file_paths]
        frame = pd.DataFrame(
            columns=[str(e.value) for e in AnnotationLabel] + ["Seen"],
            index=relative_paths,
        )
        frame.index.name = "Filepath"
        frame.fillna(False, inplace=True)
        return frame

    def _load_annotations_csv(self):
        if Path(CSV_PATH).exists():
            self._info_dialog(f"The CSV PATH {str(CSV_PATH.resolve())} exists and file is loaded")
            frame = pd.read_csv(CSV_PATH, index_col=0)
        else:
            self._info_dialog(f"The CSV PATH {str(CSV_PATH.resolve())} does not exist and new file is being created")
            frame = self._create_current_annotations_frame()
        return frame

    def _annotation_finished_dialog(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Attention")
        dlg.setText("All images have been annotated")
        button = dlg.exec_()

    def _info_dialog(self, toShow):
        dlg = QMessageBox(self)
        dlg.setWindowTitle("Attention")
        dlg.setText(toShow)
        button = dlg.exec_()

    def _check_if_any_filenames(self):
        if len(self.file_paths) > 0:
            return
        else:
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error")
            dlg.setText("There are no .jpg files in this location, program will close")
            button = dlg.exec_()

            if button == QMessageBox.Ok:
                exit()
