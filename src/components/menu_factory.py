from __future__ import annotations

from typing import List

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import QCoreApplication

from src.data.config_schema import PortalConfig
from src.services.layer_registry import LayerRegistry


class PortalMenuFactory:
    def __init__(self, iface, registry: LayerRegistry, config: PortalConfig):
        self.iface = iface
        self.registry = registry
        self.config = config
        self.created_menus: List[QMenu] = []
        self.created_actions: List[QAction] = []

    def build(self) -> None:
        self._clear_existing()
        menubar = self.iface.mainWindow().menuBar()
        for menu in self.config.menus:
            qmenu = QMenu(menu.name, menubar)
            for submenu in menu.submenus:
                qsub = qmenu.addMenu(submenu.name)
                for item in submenu.items:
                    action = QAction(item.name, self.iface.mainWindow())
                    action.triggered.connect(lambda checked=False, it=item: self._on_item_triggered(it))
                    qsub.addAction(action)
                    self.created_actions.append(action)
            menubar.addMenu(qmenu)
            self.created_menus.append(qmenu)

    def _on_item_triggered(self, item) -> None:
        tr = QCoreApplication.translate
        if not self.registry.verify_item(item):
            QgsMessageLog.logMessage(
                tr("PortalMenuFactory", "Cannot load layer: %s") % item.name,
                level=Qgis.MessageLevel.Warning,
            )
            return
        if item.provider.lower() == "gdal":
            layer = self.registry.create_raster_layer(item)
            if layer is None or not layer.isValid():
                QgsMessageLog.logMessage(
                    tr("PortalMenuFactory", "Invalid raster layer: %s") % item.name,
                    level=Qgis.MessageLevel.Warning,
                )
                return
            self.iface.addRasterLayer(item.connection_info.path, item.layer_name)
        else:
            layer = self.registry.create_vector_layer(item)
            if layer is None or not layer.isValid():
                QgsMessageLog.logMessage(
                    tr("PortalMenuFactory", "Invalid vector layer: %s") % item.name,
                    level=Qgis.MessageLevel.Warning,
                )
                return
            self.iface.addVectorLayer(item.connection_info.path, item.layer_name, item.provider)

    def _clear_existing(self) -> None:
        # Attempt to remove previously injected PortalCrafter menus.
        for action in self.created_actions:
            self.iface.mainWindow().menuBar().removeAction(action)
        for menu in self.created_menus:
            self.iface.mainWindow().menuBar().removeAction(menu.menuAction())
        self.created_menus.clear()
        self.created_actions.clear()
