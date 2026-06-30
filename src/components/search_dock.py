from __future__ import annotations

from typing import Dict, List

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QTableWidget, QTableWidgetItem, QHeaderView
from qgis.PyQt.QtCore import Qt


class PortalSearchDock(QDockWidget):
    def __init__(self, parent=None, registry=None, config=None):
        super().__init__("Portal Custom Search", parent)
        self.registry = registry
        self.config = config
        self.current_search = None
        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)

        # Component selector
        top = QHBoxLayout()
        top.addWidget(QLabel("Search:"))
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_search_changed)
        top.addWidget(self.combo)
        layout.addLayout(top)

        # Contextual hint
        self.hint_label = QLabel("Select a search definition.")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

        # Results grid
        self.table = QTableWidget()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.table)

        self.setWidget(container)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self._load_definitions()

    def _load_definitions(self) -> None:
        searches = self.config.custom_searches if self.config and self.config.custom_searches else []
        self.combo.blockSignals(True)
        self.combo.clear()
        for search in searches:
            self.combo.addItem(search.search_name, search)
        self.combo.blockSignals(False)
        if self.combo.count() > 0:
            self.combo.setCurrentIndex(0)
        else:
            self.hint_label.setText("No custom searches configured.")

    def _on_search_changed(self, index: int) -> None:
        data = self.combo.currentData()
        if not data:
            return
        self.current_search = data
        self.hint_label.setText(data.ui_hint)
        self.table.clear()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if not self.registry or not self.current_search:
            return
        target_name = self.current_search.target_layer_name
        item_map = self.registry.item_by_layer_name(target_name)
        if item_map is None:
            return
        layer = self.registry.create_vector_layer(item_map) or self.registry.create_raster_layer(item_map)
        if layer is None:
            return
        row = item.row()
        if row >= layer.featureCount():
            return
        feature = layer.getFeature(row)
        if not feature or not feature.geometry():
            return
        canvas = self.parent().iface.mapCanvas() if hasattr(self.parent(), 'iface') else None
        if canvas is None:
            return
        rect = feature.geometry().boundingBox()
        canvas.setExtent(rect)
        canvas.refresh()

    def refresh(self, config=None) -> None:
        if config is not None:
            self.config = config
        self._load_definitions()
        self.table.clear()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
