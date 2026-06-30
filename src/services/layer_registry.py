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

from src.data.config_schema import MenuItem, PortalConfig


class LayerRegistry:
    def __init__(self, config: Optional[PortalConfig] = None) -> None:
        self.config = config
        self.errors: List[str] = []

    def register_config(self, config: PortalConfig) -> None:
        self.config = config
        self.errors.clear()

    def verify_item(self, item: MenuItem) -> bool:
        path = Path(item.connection_info.path)
        if not path.exists():
            msg = "Layer path missing for %s: %s" % (item.name, path)
            self._log(msg, level="warning")
            self.errors.append(msg)
            return False
        return True

    def create_vector_layer(self, item: MenuItem):  # type: ignore
        if not self.verify_item(item):
            return None
        if QgsVectorLayer is None:
            return None
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

    def create_raster_layer(self, item: MenuItem):  # type: ignore
        if not self.verify_item(item):
            return None
        if QgsRasterLayer is None:
            return None
        path = str(item.connection_info.path)
        layer_name = item.connection_info.layer_name or item.layer_name
        return QgsRasterLayer(path, layer_name, item.provider)

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
                items.extend(submenu.items)
        return items

    def summary(self) -> Dict[str, int]:
        items = self.iter_menu_items()
        return {
            "total_items": len(items),
            "errors": len(self.errors),
        }

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
