# DeployUTCMarker=202607020620
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

try:
    from qgis.core import (  # type: ignore
        QgsMessageLog,
        Qgis,
        QgsVectorLayer,
        QgsRasterLayer,
        QgsDataSourceUri,
    )
except ModuleNotFoundError:
    QgsMessageLog = None  # type: ignore
    Qgis = None  # type: ignore
    QgsVectorLayer = None  # type: ignore
    QgsRasterLayer = None  # type: ignore
    QgsDataSourceUri = None  # type: ignore

from qgis.PyQt.QtCore import QCoreApplication  # type: ignore

from src.data.config_schema import MenuItem, MenuItemCluster, MenuItemLayer, PortalConfig


class LayerRegistry:
    def __init__(self, config: Optional[PortalConfig] = None) -> None:
        self.config = config
        self.errors: List[str] = []
        self._load_seen: Dict[str, bool] = {}

    def register_config(self, config: PortalConfig) -> None:
        self.config = config
        self.errors.clear()
        self._load_seen.clear()

    def verify_item(self, item: MenuItem) -> bool:
        if not self._verify_path(item.connection_info.path):
            return False
        return True

    def verify_layer(self, item: MenuItemLayer) -> bool:
        if not self._verify_path(item.connection_info.path):
            return False
        return True

    def create_vector_layer(self, item: MenuItem):  # type: ignore
        if not self.verify_item(item):
            return None
        if QgsVectorLayer is None:
            return None
        layer = self._build_vector_layer(item)
        return layer if isinstance(layer, QgsVectorLayer) else None

    def create_raster_layer(self, item: MenuItem):  # type: ignore
        if not self.verify_item(item):
            return None
        if QgsRasterLayer is None:
            return None
        path = str(item.connection_info.path)
        layer_name = item.connection_info.layer_name or item.layer_name
        return QgsRasterLayer(path, layer_name, item.provider)

    def build_single_vector_layer(self, layer: MenuItemLayer):  # type: ignore
        if not self.verify_layer(layer):
            return None
        if QgsVectorLayer is None:
            return None
        item = MenuItem(
            name=layer.name,
            layer_name=layer.connection_info.layer_name or layer.name,
            provider=layer.provider,
            connection_info=layer.connection_info,
        )
        return self._build_vector_layer(item)

    def build_single_raster_layer(self, layer: MenuItemLayer):  # type: ignore
        if not self.verify_layer(layer):
            return None
        if QgsRasterLayer is None:
            return None
        path = str(layer.connection_info.path)
        layer_name = layer.connection_info.layer_name or layer.name
        return QgsRasterLayer(path, layer_name, layer.provider)

    def register_loaded(self, registry_key: str) -> bool:
        if registry_key in self._load_seen:
            return False
        self._load_seen[registry_key] = True
        return True

    def item_by_layer_name(self, layer_name: str) -> Optional[MenuItem]:
        for item in self.iter_menu_items():
            if item.layer_name == layer_name:
                return item
        return None

    def iter_menu_items(self) -> List[MenuItem]:
        if self.config is None:
            return []
        items: List[MenuItem] = []
        for menu in self.config.menus:
            for submenu in menu.submenus:
                for item in submenu.items:
                    if isinstance(item, MenuItem):
                        items.append(item)
                    elif isinstance(item, MenuItemCluster):
                        for layer in item.layers:
                            items.append(
                                MenuItem(
                                    name=item.name,
                                    layer_name=layer.name,
                                    provider=layer.provider,
                                    connection_info=layer.connection_info,
                                )
                            )
        return items

    def summary(self) -> Dict[str, int]:
        items = self.iter_menu_items()
        return {
            "total_items": len(items),
            "errors": len(self.errors),
        }

    def _build_vector_layer(self, item: MenuItem):  # type: ignore
        provider = item.provider.lower()
        if provider == "ogr":
            path = str(item.connection_info.path)
            layer_name = item.connection_info.layer_name or item.layer_name
            return QgsVectorLayer(path, layer_name, "ogr")
        if provider == "postgres":
            uri = self._build_postgres_uri(item)
            layer_name = item.connection_info.layer_name or item.layer_name
            return QgsVectorLayer(uri, layer_name, "postgres")
        if provider in ("wfs", "wms"):
            uri = self._build_web_uri(item)
            layer_name = item.connection_info.layer_name or item.layer_name
            return QgsVectorLayer(uri, layer_name, provider)
        return None

    def _build_postgres_uri(self, item: MenuItem) -> str:
        info = item.connection_info
        if QgsDataSourceUri is None:
            return "postgres://%s" % info.path
        uri = QgsDataSourceUri()
        uri.setConnection(
            info.path,
            "5432",
            info.layer_name or "",
            "",
            "",
        )
        return uri.uri()

    def _build_web_uri(self, item: MenuItem) -> str:
        info = item.connection_info
        return "%s://%s?layername=%s" % (item.provider, info.path, info.layer_name or "")

    def _verify_path(self, path: str) -> bool:
        if not path:
            msg = "Missing layer datasource: %s" % path
            self._log(msg, level="warning")
            return False
        try:
            if any(sep in path for sep in [".zip", ".qgz"]) and ("|" in path or path.lower().endswith((".zip", ".qgz"))):
                return True
            return Path(path).exists()
        except Exception as exc:
            msg = "Layer datasource check failed for %s: %s" % (path, exc)
            self._log(msg, level="warning")
            return False

    def _log(self, message: str, level: str = "info") -> None:
        if QgsMessageLog is not None and Qgis is not None and QCoreApplication is not None:
            lvl = {
                "info": Qgis.MessageLevel.Info,
                "warning": Qgis.MessageLevel.Warning,
                "critical": Qgis.MessageLevel.Critical,
            }.get(level, Qgis.MessageLevel.Info)
            QgsMessageLog.logMessage(message, level=lvl)
        else:
            print("[%s] %s" % (level.upper(), message))


def purge_active_portal_layers() -> None:
    """
    Safely removes all layers associated with the current profile 
    from the map registry before initializing a new workspace.
    """
    try:
        from qgis.core import QgsProject  # type: ignore
        project = QgsProject.instance()
        layer_ids = list(project.mapLayers().keys())
        if layer_ids:
            project.removeMapLayers(layer_ids)
    except Exception as exc:
        print("[WARN] purge_active_portal_layers failed: %s" % exc)
