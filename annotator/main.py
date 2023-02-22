import sys

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QFileDialog,
)

from annotator.annotation_window import AnnotationWindow
from annotator.gems.io import Json


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Annotating ECG Scans")

        self.data_dir = ""

        ###

        self.button_select = QPushButton("Select Data Directory")
        self.chosen_directory = QLabel()
        self.chosen_directory.setText("Data directory: ")
        self.button_accept = QPushButton("Start annotating")
        self.button_close = QPushButton("Close App")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.button_select)
        self.layout.addWidget(self.chosen_directory)
        self.layout.addWidget(self.button_accept)
        self.layout.addWidget(self.button_close)

        self.widget = QWidget()
        self.widget.setLayout(self.layout)

        self.setCentralWidget(self.widget)

        self.button_select.clicked.connect(self.select_directory)
        self.button_accept.clicked.connect(self.show_annotation_window)
        self.button_close.clicked.connect(self.close_app)

        ## Annotation window

        self.annotation_window = None

    def select_directory(self):
        self.data_dir = QFileDialog.getExistingDirectory(self, "Select Directory")
        self.chosen_directory.setText(f"Data directory {self.data_dir}")

    def show_annotation_window(self):
        self.annotation_window = AnnotationWindow(self.data_dir)
        self.annotation_window.show()

    def close_app(self):
        annotations = self.annotation_window.annotations_dict
        if annotations is not None:
            Json.save("./annotations.json", annotations)
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
