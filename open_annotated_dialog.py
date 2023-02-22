from PySide6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QComboBox


class OpenAnnotatedDialog(QDialog):
    def __init__(self, annotation_paths):
        super().__init__()

        self.setWindowTitle("Choose annotation file from the list")

        self.setMinimumWidth(350)

        self.annotations = QComboBox()
        self.annotations.addItems(sorted(annotation_paths))

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()

        self.layout.addWidget(self.annotations)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
