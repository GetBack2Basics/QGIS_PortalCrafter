# DeployUTCMarker=202607020620
from qgis.PyQt.QtWidgets import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)
from qgis.PyQt.QtCore import Qt


class PortalStartupSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PortalCrafter Workspace")
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowTitleHint
            | Qt.WindowType.WindowSystemMenuHint
        )
        self.setModal(True)

        self.full_qgis = QRadioButton("Full QGIS")
        self.full_qgis.setChecked(True)
        self.cultural = QRadioButton("Cultural")

        group = QButtonGroup(self)
        group.addButton(self.full_qgis)
        group.addButton(self.cultural)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Select workspace environment:"))
        layout.addWidget(self.full_qgis)
        layout.addWidget(self.cultural)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_profile(self):
        if self.cultural.isChecked():
            return "Cultural"
        return "FullQGIS"
