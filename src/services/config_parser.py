from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from qgis.core import QgsMessageLog, Qgis  # type: ignore
    from qgis.PyQt.QtCore import QCoreApplication  # type: ignore
except ModuleNotFoundError:  # headless / test contexts
    QgsMessageLog = None  # type: ignore
    Qgis = None  # type: ignore
    QCoreApplication = None  # type: ignore

from src.data.config_schema import (  # noqa: E402
    ConnectionInfo,
    CustomSearch,
    Menu,
    MenuItem,
    MenuItemCluster,
    MenuItemLayer,
    PortalConfig,
    SubMenu,
)


class PortalConfigParser:
    def __init__(self, config_path: str | Path) -> None:
        self.config_path = Path(config_path)
        self.raw: Dict[str, Any] = {}
        self.parsed: Optional[PortalConfig] = None

    def load(self) -> bool:
        if not self.config_path.exists():
            self._log("Configuration file missing: %s" % self.config_path, level="warning")
            return False
        try:
            raw_text = self.config_path.read_text(encoding="utf-8")
            self.raw = _yaml_load(raw_text) or {}
            return True
        except Exception as exc:  # noqa: BLE001
            self._log("Failed to parse portal_config.yaml: %s" % exc, level="warning")
            return False

    def validate(self) -> Optional[PortalConfig]:
        if not self.raw:
            self._log("Empty configuration payload after parsing.", level="warning")
            return None
        try:
            self.parsed = _map_raw_to_schema(self.raw)
            return self.parsed
        except Exception as exc:  # noqa: BLE001
            self._log("Schema validation failed: %s" % exc, level="warning")
            return None

    @property
    def driver_tracks(self) -> Dict[str, List[MenuItem]]:
        if self.parsed is None:
            return {}
        tracks: Dict[str, List[MenuItem]] = {}
        for menu in self.parsed.menus:
            for submenu in menu.submenus:
                for item in submenu.items:
                    key = item.provider.lower()
                    tracks.setdefault(key, []).append(item)
        return tracks

    def _log(self, message: str, level: str = "info") -> None:
        if QgsMessageLog is not None and Qgis is not None and QCoreApplication is not None:
            lvl = {
                "info": Qgis.MessageLevel.Info,
                "warning": Qgis.MessageLevel.Warning,
                "critical": Qgis.MessageLevel.Critical,
            }.get(level, Qgis.MessageLevel.Info)
            QgsMessageLog.logMessage(message, level=lvl)
        else:
            log_fn = getattr(logger, level, logger.info)
            log_fn(message)


def _yaml_load(raw_text: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:  # noqa: BLE001
        raise RuntimeError("PyYAML is required to load portal_config.yaml") from exc
    return yaml.safe_load(raw_text) or {}


def _map_raw_to_schema(raw: Dict[str, Any]) -> PortalConfig:
    metadata = raw.get("metadata", {})
    interface_customization = raw.get("interface_customization", {})
    menus = _parse_menus(raw.get("menus", []))
    custom_searches = _parse_custom_searches(raw.get("custom_searches", []))
    return PortalConfig(
        metadata=metadata,
        interface_customization=interface_customization,
        menus=menus,
        custom_searches=custom_searches,
    )


def _parse_menus(raw_menus: List[Dict[str, Any]]) -> List[Menu]:
    menus: List[Menu] = []
    for raw_menu in raw_menus:
        submenus: List[SubMenu] = []
        for raw_sub in raw_menu.get("submenus", []):
            items: List[Union[MenuItem, MenuItemCluster]] = []
            for raw_item in raw_sub.get("items", []):
                layers = raw_item.get("layers")
                if layers is None:
                    items.append(MenuItem.from_dict(raw_item))
                    continue
                items.append(MenuItemCluster.from_dict(raw_item))
            submenus.append(
                SubMenu(
                    name=raw_sub.get("name", ""),
                    items=items,
                )
            )
        menus.append(
            Menu(
                name=raw_menu.get("name", ""),
                submenus=submenus,
            )
        )
    return menus


def _parse_custom_searches(raw_searches: List[Dict[str, Any]]) -> List[CustomSearch]:
    searches: List[CustomSearch] = []
    for raw_search in raw_searches:
        searches.append(
            CustomSearch(
                search_name=raw_search.get("search_name", ""),
                target_layer_name=raw_search.get("target_layer_name", ""),
                search_attribute=raw_search.get("search_attribute", ""),
                comparison_operator=raw_search.get("comparison_operator", "Equals"),
                ui_hint=raw_search.get("ui_hint", ""),
                results_display_columns=raw_search.get("results_display_columns", []),
                default_zoom_scale=int(
                    raw_search.get("default_zoom_scale", 2500)
                ),
            )
        )
    return searches
