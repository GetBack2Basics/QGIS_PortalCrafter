from __future__ import annotations

from typing import Dict, List

from qgis.core import QgsMapLayer, QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import QCoreApplication

from src.data.config_schema import Menu, MenuItem, PortalConfig
from src.services.layer_registry import LayerRegistry


class PortalMenuFactory:
    def __init__(self, iface, registry: LayerRegistry, config: PortalConfig):
        self.iface = iface
        self.registry = registry
        self.config = config
        self.created_menus: List[QMenu] = []
        self.created_actions: List[QAction] = []
        self.loaded_keys: Dict[str, bool] = {}

    def _item_key(self, item: MenuItem) -> str:
        return "%s::%s" % (item.name, item.layer_name)

    def build(self) -> None:
        self._clear_existing()
        menubar = self.iface.mainWindow().menuBar()
        root_title = self.config.metadata.get("root_menu_name", "PortalCrafter") if hasattr(self.config, "metadata") else "PortalCrafter"
        if not root_title:
            root_title = "PortalCrafter"

        root = QMenu(root_title, menubar)
        menubar.addMenu(root)
        self.created_menus.append(root)

        for group in self.config.menus:
            branch = root.addMenu(group.name)
            for submenu in group.submenus:
                sub = branch.addMenu(submenu.name)
                for item in submenu.items:
                    action = QAction(item.name, self.iface.mainWindow())
                    key = self._item_key(item)
                    action.setEnabled(not bool(self.loaded_keys.get(key)))
                    action.triggered.connect(
                        lambda checked=False, it=item, act=action, k=key: self._on_item_triggered(it, act, k)
                    )
                    sub.addAction(action)
                    self.created_actions.append(action)

        QgsMessageLog.logMessage(
            "PortalCrafter: rendered %d groups with configured root_menu_name '%s'"
            % (len(self.config.menus), root_title),
            level=Qgis.MessageLevel.Info,
        )

    def _on_item_triggered(self, item: MenuItem, action: QAction, key: str) -> None:
        if key in self.loaded_keys:
            return
        tr = QCoreApplication.translate
        if not self.registry.verify_item(item):
            QgsMessageLog.logMessage(
                tr("PortalMenuFactory", "Cannot load layer: %s") % item.name,
                level=Qgis.MessageLevel.Warning,
            )
            return
        if item.provider.lower() == "gdal":
            layer = self.registry.create_raster_layer(item)
            if not layer or not layer.isValid():
                QgsMessageLog.logMessage(
                    tr("PortalMenuFactory", "Invalid raster layer: %s") % item.name,
                    level=Qgis.MessageLevel.Warning,
                )
                return
            self.iface.addRasterLayer(item.connection_info.path, item.layer_name)
        else:
            layer = self.registry.create_vector_layer(item)
            if not layer or not layer.isValid():
                QgsMessageLog.logMessage(
                    tr("PortalMenuFactory", "Invalid vector layer: %s") % item.name,
                    level=Qgis.MessageLevel.Warning,
                )
                return
            self.iface.addVectorLayer(item.connection_info.path, item.layer_name, item.provider)
        if isinstance(layer, QgsMapLayer):
            if hasattr(self.registry, 'apply_scale_visibility'):
                self.registry.apply_scale_visibility(layer, item)
            try:
                self.iface.mapCanvas().refresh()
            except Exception:
                pass
        self.loaded_keys[key] = True
        action.setEnabled(False)

    def _clear_existing(self) -> None:
        for action in self.created_actions:
            self.iface.mainWindow().menuBar().removeAction(action)
        for menu in list(self.created_menus):
            action = menu.menuAction()
            self.created_menus.remove(menu)
            self.iface.mainWindow().menuBar().removeAction(action)
        self.created_actions.clear()
        self.loaded_keys.clear()
