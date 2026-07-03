# DeployUTCMarker=202607020620
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from qgis.core import QgsMapLayer, QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import QCoreApplication

from src.data.config_schema import Menu, MenuItem, MenuItemCluster, MenuItemLayer, PortalConfig
from src.services.layer_registry import LayerRegistry


class PortalMenuFactory:
    TP_TAG = "PortalCrafter|menu_factory"

    def __init__(self, iface, registry: LayerRegistry, config: PortalConfig):
        self.iface = iface
        self.registry = registry
        self.config = config
        self.created_actions: List[QAction] = []
        self.loaded_keys: Dict[str, bool] = {}
        self._active_profile_name = "PortalCrafter"
        self._profile_click_callback: Optional[Callable[[str], None]] = None

    def _ep(self, message: str) -> None:
        QgsMessageLog.logMessage(message, self.TP_TAG, level=Qgis.MessageLevel.Warning)

    def _item_key(self, item: "MenuItem | MenuItemCluster") -> str:
        if isinstance(item, MenuItemCluster):
            return "cluster::%s" % item.name
        return "%s::%s" % (item.name, item.layer_name)

    def build(self, active_profile_name: str = "PortalCrafter", profile_click_callback=None) -> None:
        self.created_actions.clear()
        self.loaded_keys.clear()
        self._active_profile_name = active_profile_name or "PortalCrafter"
        self._profile_click_callback = profile_click_callback
        menubar = self.iface.mainWindow().menuBar()
        root_title = "PortalCrafter"

        self._ep("build start active=%s" % self._active_profile_name)

        # Remove any existing PortalCrafter root menu entirely to avoid duplicates.
        for action in list(menubar.actions()):
            menu = action.menu()
            if menu is None:
                continue
            try:
                title = menu.title()
            except Exception:
                continue
            if title == root_title:
                self._ep("removing existing root menu '%s'" % root_title)
                menubar.removeAction(action)
                QMenu(action.parent() if action.parent() is not None else self.iface.mainWindow()).removeAction(action)  # type: ignore[]

        root = QMenu(root_title, menubar)
        menubar.addMenu(root)

        available = self._available_profile_names()
        self._ep("available profiles=%s" % ",".join(available))
        for profile_name in available:
            profile_menu = root.addMenu(profile_name)
            if callable(self._profile_click_callback):
                profile_menu.menuAction().triggered.connect(
                    lambda checked=False, p=profile_name: self._on_profile_menu_clicked(p)
                )
            if profile_name == self._active_profile_name:
                self._ep("building functional items for=%s" % profile_name)
                self._build_functional_items(profile_menu)
                self._attach_switchers(profile_menu)

        QgsMessageLog.logMessage(
            "PortalCrafter: rendered profiles under '%s' active='%s'"
            % (root_title, self._active_profile_name),
            level=Qgis.MessageLevel.Info,
        )

    def _build_functional_items(self, root_menu: "QMenu") -> None:
        if not self.config.menus:
            self._ep("no menus in config")
            return
        for group in self.config.menus:
            if group.name == "Full QGIS":
                continue
            branch = root_menu.addMenu(group.name)
            for submenu in group.submenus:
                sub = branch.addMenu(submenu.name)
                for item in submenu.items:
                    layers_block = (
                        list(item.layers)
                        if isinstance(item, MenuItemCluster)
                        else [item]
                    )
                    action = QAction(item.name, self.iface.mainWindow())
                    key = self._item_key(item)
                    action.setEnabled(not bool(self.loaded_keys.get(key)))
                    action.triggered.connect(
                        lambda checked=False, blk=layers_block, act=action, k=key: self._on_batch_triggered(blk, act, k)
                    )
                    sub.addAction(action)
                    self.created_actions.append(action)

    def _attach_switchers(self, root_menu: "QMenu") -> None:
        for profile_name in self._available_profile_names():
            if profile_name == self._active_profile_name:
                continue
            action = QAction("Switch to %s Workspace" % profile_name, self.iface.mainWindow())
            action.triggered.connect(
                lambda checked=False, target=profile_name: self._on_profile_switch_requested(target)
            )
            root_menu.addAction(action)
            self.created_actions.append(action)

    def _available_profile_names(self) -> List[str]:
        discovered: List[str] = []
        try:
            base = Path("/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/projects")
            if base.exists():
                for path in sorted(base.glob("*.qgz")):
                    discovered.append(path.stem)
        except Exception as exc:
            self._ep("profile discovery failed: %s" % exc)
        if not discovered:
            self._ep("no qgz profiles found; falling back to defaults")
            discovered = ["Cultural", "Environment"]
        else:
            self._ep("discovered profiles from qgz: %s" % ",".join(discovered))
        return discovered

    def _on_profile_menu_clicked(self, profile_name: str) -> None:
        if callable(self._profile_click_callback):
            self._ep("profile menu clicked=%s" % profile_name)
            self._profile_click_callback(profile_name)

    def _on_profile_switch_requested(self, target_profile_name: str) -> None:
        if callable(self._profile_click_callback):
            self._ep("switch requested=%s" % target_profile_name)
            self._profile_click_callback(target_profile_name)

    def _on_item_triggered(self, item: "MenuItem | MenuItemCluster", action: "QAction", key: str) -> None:
        self._on_batch_triggered([item], action, key)

    def _on_batch_triggered(self, layers_block: list, action: "QAction", key: str) -> None:
        if key in self.loaded_keys:
            return
        tr = QCoreApplication.translate
        for layer in layers_block:
            if isinstance(layer, MenuItemCluster):
                for inner in layer.layers:
                    self._load_cluster_layer(layer.name, inner)
            elif isinstance(layer, MenuItemLayer):
                self._load_cluster_layer("batch", layer)
            elif isinstance(layer, MenuItem):
                self._load_menu_item(layer)
            else:
                QgsMessageLog.logMessage(
                    tr("PortalMenuFactory", "Unsupported menu item type: %s") % type(layer).__name__,
                    level=Qgis.MessageLevel.Warning,
                )
        self.loaded_keys[key] = True
        action.setEnabled(False)

    def _load_menu_item(self, item: "MenuItem") -> None:
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

    def _load_cluster_layer(self, cluster_name: str, layer: "MenuItemLayer") -> None:
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
                tr("PortalCrafter", "Invalid vector layer in batch: %s") % layer.name,
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
