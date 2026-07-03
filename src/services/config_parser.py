# DeployUTCMarker=202607020621
"""
Two-tier configuration loader for PortalCrafter.

Tier 1: Fast boot from portal_profiles.yaml index on startup.
Tier 2: Lazy child-config load/validation only when a profile is selected.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    ProfileLink,
    ProfilePage,
    SubMenu,
)


@dataclass(frozen=True)
class ProfileIndexEntry:
    profile_id: str
    name: str
    config_file: str
    project_workspace: Optional[str] = None
    profiles_link: Optional[ProfileLink] = None


@dataclass(frozen=True)
class ProfileIndex:
    profiles: List[ProfileIndexEntry]

    def find(self, profile_id: str) -> Optional[ProfileIndexEntry]:
        for entry in self.profiles:
            if entry.profile_id == profile_id:
                return entry
        return None

    def names(self) -> List[str]:
        return [entry.name for entry in self.profiles]

    def ids(self) -> List[str]:
        return [entry.profile_id for entry in self.profiles]

    # FIXME: ensure build_descriptor_tabs/get_ui_state accepts configured pages
    # without assuming hidden/menu/template defaults may raise RuntimeError.


class PortalConfigParser:
    MARKER = "PortalCrafter"

    def __init__(self, index_path: str | Path) -> None:
        self.index_path = Path(index_path)
        self.index: Optional[ProfileIndex] = None
        self._profile_parsed: Dict[str, Optional[PortalConfig]] = {}
        self._profile_raw: Dict[str, Dict[str, Any]] = {}

    def boot_loader(self) -> ProfileIndex:
        """
        Tier 1: Read portal_profiles.yaml on startup without validating child configs.
        Expected shape:
          roles:
            - id: cultural
              name: Cultural
              config_file: ...
              project_workspace: ...
        """
        if not self.index_path.exists():
            msg = "Profile index missing: %s" % self.index_path
            self._log(msg, level="warning")
            return ProfileIndex(profiles=[])
        try:
            text = self.index_path.read_text(encoding="utf-8")
            raw = _yaml_load(text) or {}
        except Exception as exc:  # noqa: BLE001
            self._log("Failed to parse profile index: %s" % exc, level="warning")
            return ProfileIndex(profiles=[])

        roles = raw.get("profiles", []) if isinstance(raw, dict) else []
        entries: List[ProfileIndexEntry] = []
        for role in roles if isinstance(roles, list) else []:
            if not isinstance(role, dict):
                continue
            profile_id = role.get("id")
            name = role.get("name")
            config_file = role.get("config_file")
            project_workspace = role.get("project_workspace")
            if not profile_id or not name or not config_file:
                continue
            profiles_link = None
            profiles_link_raw = role.get("profiles_link")
            if isinstance(profiles_link_raw, dict):
                page_raw = profiles_link_raw.get("page", "Profile")
                page_obj = ProfilePage(profile=page_raw if isinstance(page_raw, str) else "Profile")
                profile_id_key = profiles_link_raw.get("profile_id_key", "id")
                profiles_link = ProfileLink(page=page_obj, profile_id_key=str(profile_id_key))
            entries.append(
                ProfileIndexEntry(
                    profile_id=str(profile_id),
                    name=str(name),
                    config_file=str(config_file),
                    project_workspace=str(project_workspace) if project_workspace else None,
                    profiles_link=profiles_link,
                )
            )

        index = ProfileIndex(profiles=entries)
        self.index = index
        self._log("boot_loader profiles=%s" % ",".join(index.ids()), level="info")
        return index

    def lazy_loader(self, profile_id: str) -> Optional[PortalConfig]:
        """
        Tier 2: Load + validate a child profile config only on demand.
        """
        index = self.index or self.boot_loader()
        entry = index.find(profile_id)
        if entry is None:
            self._log("Unknown profile id: %s" % profile_id, level="warning")
            return None

        if profile_id in self._profile_parsed:
            return self._profile_parsed[profile_id]

        config_path = Path(entry.config_file)
        raw: Dict[str, Any] = {}
        if not config_path.exists():
            self._log("Child config missing: %s" % config_path, level="warning")
            self._profile_parsed[profile_id] = None
            return None
        try:
            parsed = _yaml_load(config_path.read_text(encoding="utf-8")) or {}
            raw = parsed
        except Exception as exc:  # noqa: BLE001
            self._log("Failed to parse child config: %s" % exc, level="warning")
            self._profile_parsed[profile_id] = None
            return None

        try:
            config = _map_raw_to_schema(raw)
            self._profile_parsed[profile_id] = config
            return config
        except Exception as exc:  # noqa: BLE001
            self._log("Failed to validate child config: %s" % exc, level="warning")
            self._profile_parsed[profile_id] = None
            return None

    def reset_cache(self) -> None:
        self._profile_parsed.clear()
        self._profile_raw.clear()

    def _log(self, message: str, level: str = "info") -> None:
        msg = "%s %s" % (self.MARKER, message)
        if QgsMessageLog is not None and Qgis is not None and QCoreApplication is not None:
            lvl = {
                "info": Qgis.MessageLevel.Info,
                "warning": Qgis.MessageLevel.Warning,
                "critical": Qgis.MessageLevel.Critical,
            }.get(level, Qgis.MessageLevel.Info)
            QgsMessageLog.logMessage(msg, level=lvl)
        else:
            log_fn = getattr(logger, level, logger.info)
            log_fn(msg)


def _yaml_load(raw_text: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ModuleNotFoundError as exc:  # noqa: BLE001
        raise RuntimeError("PyYAML is required to load profile configs.") from exc
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
                results_display_columns=raw_search.get("results_display_columns", [])
                if isinstance(raw_search.get("results_display_columns"), list)
                else [],
                default_zoom_scale=int(raw_search.get("default_zoom_scale", 2500)),
            )
        )
    return searches
