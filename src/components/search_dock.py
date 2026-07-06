from __future__ import annotations

from typing import List, Optional

from qgis.core import QgsMessageLog, Qgis, QgsFeatureRequest, QgsExpression
from qgis.PyQt.QtWidgets import QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView
from qgis.PyQt.QtCore import Qt


class PortalSearchDock(QDockWidget):
    TAG = "PortalCrafterSearch"
    def __init__(self, parent=None, registry=None, config=None):
        super().__init__("Portal Custom Search", parent)
        self.registry = registry
        self.config = config
        self.current_search: Optional[object] = None
        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QVBoxLayout(container)

        # Search selector
        selector = QHBoxLayout()
        selector.addWidget(QLabel("Search:"))
        self.combo = QComboBox()
        self.combo.currentIndexChanged.connect(self._on_search_changed)
        selector.addWidget(self.combo)
        layout.addLayout(selector)

        # Value input
        value_row = QHBoxLayout()
        value_row.addWidget(QLabel("Value:"))
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Enter search value")
        self.value_input.textChanged.connect(self._on_value_changed)
        value_row.addWidget(self.value_input)
        layout.addLayout(value_row)

        self.hint_label = QLabel("Select a search definition.")
        self.hint_label.setWordWrap(True)
        layout.addWidget(self.hint_label)

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
        self._log("init config=%s" % type(self.config).__name__)
        self._load_definitions()

    def _log(self, message: str, level: str = "info") -> None:
        QgsMessageLog.logMessage(
            "%s: %s" % (self.TAG, message),
            self.TAG,
            level=getattr(Qgis.MessageLevel, level.capitalize(), Qgis.MessageLevel.Info),
        )

    def _load_definitions(self) -> None:
        searches = getattr(self.config, "custom_searches", None) or []
        self._log("load_definitions config=%s searches=%d" % (type(self.config).__name__, len(searches)))
        self.combo.blockSignals(True)
        self.combo.clear()
        for search in searches:
            self.combo.addItem(search.search_name, search)
        self.combo.blockSignals(False)
        if self.combo.count() > 0:
            self.combo.setCurrentIndex(0)
        else:
            self.hint_label.setText("No custom searches configured.")

    def _current_value(self) -> str:
        return (self.value_input.text() or "").strip()

    def _sql_literal(self, text: str) -> str:
        safe = text.replace("'", "''")
        return "'%s'" % safe

    def _build_filter_expression(self) -> Optional[QgsExpression]:
        search = self.current_search
        if not search:
            return None
        attribute = getattr(search, "search_attribute", None)
        operator = (getattr(search, "comparison_operator", None) or "Equals").strip().lower()
        val = self._current_value()
        if not attribute:
            return None
        if not val:
            return QgsExpression("%s IS NOT NULL" % attribute)
        lit = self._sql_literal(val)
        mapping = {
            "equals": "%s = %s",
            "=": "%s = %s",
            "notequals": "%s <> %s",
            "!=": "%s <> %s",
            "<>": "%s <> %s",
            "greaterthan": "%s > %s",
            "greaterthanorequals": "%s >= %s",
            "lessthan": "%s < %s",
            "lessthanorequals": "%s <= %s",
            "contains": "%s LIKE '%%' || %s || '%%'",
            "like": "%s LIKE '%%' || %s || '%%'",
        }
        pattern = mapping.get(operator, "%s = %s")
        expr_str = pattern % (attribute, lit)
        expr = QgsExpression(expr_str)
        expr.setGeomName("geom")
        if expr.hasParserError():
            self.hint_label.setText("Expression error: %s" % expr.parserErrorString())
            return None
        return expr

    def _run_search(self) -> None:
        search = self.current_search
        if not search:
            return
        target_name = getattr(search, "target_layer_name", None)
        if not target_name:
            self.hint_label.setText("Search definition missing target_layer_name.")
            self.table.clear()
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return
        if self.registry is None:
            self.hint_label.setText("Layer registry is unavailable.")
            return
        item_map = self.registry.item_by_layer_name(target_name)
        if item_map is None:
            self.hint_label.setText("Target layer '%s' not found in registry." % target_name)
            self.table.clear()
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return
        layer = self.registry.create_vector_layer(item_map) or self.registry.create_raster_layer(item_map)
        if layer is None:
            self.hint_label.setText("Target layer '%s' could not be loaded." % target_name)
            self.table.clear()
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return

        expression = self._build_filter_expression()
        if expression is None:
            self.table.clear()
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return

        columns = getattr(search, "results_display_columns", None) or []
        req = QgsFeatureRequest().setFilterExpression(expression)
        features = []
        try:
            for f in layer.getFeatures(req):
                features.append(f)
        except Exception as exc:
            self.hint_label.setText("Search failed: %s" % exc)
            self.table.clear()
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return

        self._render_results(features, columns, target_name)

    def _render_results(self, features: list, columns: List[str], source_name: str) -> None:
        self.table.clear()
        if not features:
            self.table.setColumnCount(1)
            self.table.setRowCount(1)
            self.table.setHorizontalHeaderLabels(["Result"])
            self.table.setItem(0, 0, QTableWidgetItem("No results for '%s'." % source_name))
            self.hint_label.setText("0 matching features.")
            return
        cols = [c for c in columns if c]
        if not cols:
            cols = list(features[0].fields().names())[:8]
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(features))
        self.table.setHorizontalHeaderLabels(cols)
        field_names = list(features[0].fields().names())
        for r, f in enumerate(features):
            for c, name in enumerate(cols):
                val = f[name] if name in field_names else None
                self.table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
        self.hint_label.setText("%d matching features." % len(features))

    def _on_search_changed(self, index: int) -> None:
        data = self.combo.currentData()
        if not data:
            self.current_search = None
            self.hint_label.setText("Select a search definition.")
            self.table.clear()
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return
        self.current_search = data
        hint = getattr(data, "ui_hint", None) or "Enter a value and run the search."
        self.hint_label.setText(hint)
        self.table.clear()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self._run_search()

    def _on_value_changed(self, _text: str) -> None:
        self._run_search()

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        if self.registry is None or self.current_search is None:
            return
        target_name = getattr(self.current_search, "target_layer_name", None)
        if not target_name:
            return
        item_map = self.registry.item_by_layer_name(target_name)
        if item_map is None:
            return
        layer = self.registry.create_vector_layer(item_map) or self.registry.create_raster_layer(item_map)
        if layer is None:
            return
        row = item.row()
        if row < 0 or row >= layer.featureCount():
            return
        feature = None
        for idx, f in enumerate(layer.getFeatures()):
            if idx == row:
                feature = f
                break
        if not feature or not feature.geometry():
            return
        canvas = self.parent().iface.mapCanvas() if hasattr(self.parent(), 'iface') else None
        if canvas is None:
            return
        canvas.setExtent(feature.geometry().boundingBox())
        canvas.refresh()

    def refresh(self, config=None) -> None:
        if config is not None:
            self.config = config
        self.table.clear()
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self._load_definitions()
