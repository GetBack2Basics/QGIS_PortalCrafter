from __future__ import annotations

from typing import Dict, List

from qgis.core import QgsMapLayer, QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import QCoreApplication

from src.data.config_schema import Menu, MenuItem, MenuItemCluster, MenuItemLayer, PortalConfig
from src.services.layer_registry import LayerRegistry


class PortalMenuFactory:
    def __init__(self, iface, registry: LayerRegistry, config: PortalConfig):
        self.iface = iface
        self.registry = registry
        self.config = config
        self.created_menus: List[QMenu] = []
        self.created_actions: List[QAction] = []
        self.loaded_keys: Dict[str, bool] = {}

    def _item_key(self, item: MenuItem | MenuItemCluster) -> str:
        if isinstance(item, MenuItemCluster):
            return "cluster::%s" % item.name
        return "%s::%s" % (item.name, item.layer_name)

    def build(self) -> None:
        self._clear_existing()
        menubar = self.iface.mainWindow().menuBar()
        root_title = (
            self.config.metadata.get("root_menu_name", "PortalCrafter")
            if isinstance(getattr(self.config, "metadata", None), dict)
            else "PortalCrafter"
        )
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

    def _on_item_triggered(self, item: MenuItem | MenuItemCluster, action: QAction, key: str) -> None:
        if key in self.loaded_keys:
            return
        tr = QCoreApplication.translate
        if isinstance(item, MenuItemCluster):
            for layer in item.layers:
                self._load_cluster_layer(item.name, layer)
        else:
            self._load_menu_item(item)
        self.loaded_keys[key] = True
        action.setEnabled(False)

    def _load_menu_item(self, item: MenuItem) -> None:
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
        self._finalize_loaded_layer(layer, item)

    def _load_cluster_layer(self, cluster_name: str, layer: MenuItemLayer) -> None:
        tr = QCoreApplication.translate
        if not self.registry.verify_layer(layer):
            QgsMessageLog.logMessage(
                tr("PortalMenuFactory", "Cannot load layer in batch: %s") % layer.name,
                level=Qgis.MessageLevel.Warning,
            )
            return
        if layer.provider.lower() == "gdal":
            qgs_layer = self.registry.build_single_raster_layer(layer)
            if not qgs_layer or not qgs_layer.isValid():
                QgsMessageLog.logMessage(
                    tr("PortalMenuFactory", "Invalid raster layer in batch: %s") % layer.name,
                    level=Qgis.MessageLevel.Warning,
                )
                return
            self.iface.addRasterLayer(layer.connection_info.path, layer.connection_info.layer_name or layer.name)
            self._finalize_loaded_layer(qgs_layer, layer)
            return
        qgs_layer = self.registry.build_single_vector_layer(layer)
        if not qgs_layer or not qgs_layer.isValid():
            QgsMessageLog.logMessage(
                tr("PortalMenuFactory", "Invalid vector layer in batch: %s") % layer.name,
                level=Qgis.MessageLevel.Warning,
            )
            return
        registry_key = "cluster::%s::%s" % (cluster_name, layer.connection_info.path)
        if not self.registry.register_loaded(registry_key):
            QgsMessageLog.logMessage(
                tr("PortalMenuFactory", "Duplicate batch layer skipped: %s") % registry_key,
                level=Qgis.MessageLevel.Warning,
            )
            return
        self.iface.addVectorLayer(layer.connection_info.path, layer.connection_info.layer_name or layer.name, layer.provider)
        self._apply_scale_visibility_if_any(qgs_layer, layer)
        try:
            self.iface.mapCanvas().refresh()
        except Exception:
            pass

    def _apply_scale_visibility_if_any(self, layer, meta) -> None:
        if hasattr(self.registry, 'apply_scale_visibility'):
            self.registry.apply_scale_visibility(layer, meta)

    def _finalize_loaded_layer(self, layer, item) -> None:
        if isinstance(layer, QgsMapLayer):
            self._apply_scale_visibility_if_any(layer, item)
            try:
                self.iface.mapCanvas().refresh()
            except Exception:
                pass

    def _clear_existing(self) -> None:
        for action in self.created_actions:
            self.iface.mainWindow().menuBar().removeAction(action)
        for menu in list(self.created_menus):
            action = menu.menuAction()
            self.created_menus.remove(menu)
            self.iface.mainWindow().menuBar().removeAction(action)
        self.created_actions.clear()
        self.loaded_keys.clear()
