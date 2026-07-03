# DeployUTCMarker=202607030447
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, List, Optional

from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import QCoreApplication

from src.data.config_schema import Menu, MenuItem, MenuItemCluster, MenuItemLayer, PortalConfig
from src.services.config_parser import ProfileIndex, ProfileIndexEntry, PortalConfigParser
from src.services.layer_registry import LayerRegistry, purge_active_portal_layers


class PortalMenuFactory:
    TP_TAG = "PortalCrafter"
    _boot_titles_seen = set()

    def __init__(self, iface, registry: LayerRegistry, parser: PortalConfigParser):
        self.iface = iface
        self.registry = registry
        self.parser = parser
        self.index: Optional[ProfileIndex] = None
        self.config: Optional[PortalConfig] = None
        self.created_actions: List[QAction] = []
        self.loaded_keys: Dict[str, bool] = {}
        self._active_profile_id: Optional[str] = None
        self._profile_selected_callback: Optional[Callable[[str, str], None]] = None
        self.profile_menus: Dict[str, QMenu] = {}
        self._boot_root_title = "PortalCrafter"

    def _ep(self, message: str) -> None:
        QgsMessageLog.logMessage(message, self.TP_TAG, level=Qgis.MessageLevel.Warning)

    def purge_existing_menus(self) -> None:
        menubar = self.iface.mainWindow().menuBar()
        for action in list(menubar.actions()):
            menu = action.menu()
            if menu is not None and menu.title() == self._boot_root_title:
                menubar.removeAction(action)
        self.profile_menus.clear()
        self.created_actions.clear()
        type(self)._boot_titles_seen.discard(self._boot_root_title)

    def build_boot_anchors(self, index: ProfileIndex, profile_click_callback: Optional[Callable[[str, str], None]] = None) -> Dict[str, QMenu]:
        self.purge_existing_menus()
        menubar = self.iface.mainWindow().menuBar()

        root_menu = QMenu(self._boot_root_title, menubar)
        menubar.addMenu(root_menu)

        created: Dict[str, QMenu] = {}
        for entry in index.profiles:
            profile_menu = root_menu.addMenu(entry.name)
            action = QAction("Load %s Workspace" % entry.name, self.iface.mainWindow())
            action.triggered.connect(
                lambda checked=False, entry=entry: self._on_profile_clicked(entry)
            )
            profile_menu.addAction(action)
            self.profile_menus[entry.profile_id] = profile_menu
            created[entry.profile_id] = profile_menu
            self._ep("boot_anchor profile=%s" % entry.profile_id)

        self.index = index
        self._profile_selected_callback = profile_click_callback
        self._active_profile_id = index.profiles[0].profile_id if index.profiles else None
        self._ep("build_boot_anchors profiles=%s" % ",".join(index.ids()))
        return created

    def build_submenus_for_profile(self, profile_id: str, overwrite: bool = True) -> None:
        self._ep("lazy submenu build profile=%s" % profile_id)
        root_menu = self.profile_menus.get(profile_id)
        if root_menu is None:
            self._ep("lazy submenu missing top-level menu for profile=%s" % profile_id)
            return
        if overwrite:
            while root_menu.actions():
                root_menu.removeAction(root_menu.actions()[0])
        entry = None
        if self.index:
            entry = self.index.find(profile_id)
        if entry is None:
            self._ep("lazy submenu missing profile index for=%s" % profile_id)
            return

        config = self.parser.lazy_loader(profile_id)
        if config is None:
            self._ep("lazy submenu missing config for=%s" % profile_id)
            missing_action = QAction("Configuration unavailable for '%s'" % entry.name, self.iface.mainWindow())
            missing_action.setEnabled(False)
            root_menu.addAction(missing_action)
            self.created_actions.append(missing_action)
            return

        self.config = config
        for group in config.menus:
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

        switcher_action = QAction("Switch Workspace", self.iface.mainWindow())
        menubar = self.iface.mainWindow().menuBar()
        switcher_menu = QMenu("Switch Workspace", menubar)
        for index_entry in self.index.profiles if self.index else []:
            if index_entry.profile_id == profile_id:
                continue
            action = QAction("Switch to %s Workspace" % index_entry.name, self.iface.mainWindow())
            action.triggered.connect(
                lambda checked=False, target=index_entry.profile_id, path=index_entry.config_file: self._on_profile_switch_requested(target, path)
            )
            switcher_menu.addAction(action)
            self.created_actions.append(action)
        switcher_action.setMenu(switcher_menu)
        root_menu.addAction(switcher_action)
        self.created_actions.append(switcher_action)

        self._active_profile_id = profile_id
        self._ep("lazy submenu complete profile=%s menus=%d" % (profile_id, len(config.menus)))

    def _item_key(self, item: "MenuItem | MenuItemCluster") -> str:
        if isinstance(item, MenuItemCluster):
            return "cluster::%s" % item.name
        return "%s::%s" % (item.name, item.layer_name)

    def _on_profile_clicked(self, entry: ProfileIndexEntry) -> None:
        self._ep("profile clicked=%s" % entry.profile_id)
        if callable(self._profile_selected_callback):
            self._profile_selected_callback(entry.profile_id, entry.config_file)

    def _on_profile_switch_requested(self, target_profile_id: str, config_file: str) -> None:
        self._ep("switch requested id=%s" % target_profile_id)
        if callable(self._profile_selected_callback):
            self._profile_selected_callback(target_profile_id, config_file)

    def _on_batch_triggered(self, layers_block: list, action: QAction, key: str) -> None:
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
        if hasattr(layer, '__class__') and layer.__class__.__name__ == "QgsMapLayer":
            self._apply_scale_visibility_if_any(layer, item)
            try:
                self.iface.mapCanvas().refresh()
            except Exception:
                pass
