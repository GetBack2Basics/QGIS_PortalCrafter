from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# provider mapping stays our internal contract only.
# platform-specific wording comes from the config or a registry module.


@dataclass(frozen=True)
class ConnectionInfo:
    path: str
    layer_name: Optional[str] = None


@dataclass(frozen=True)
class MenuItem:
    name: str
    layer_name: str
    provider: str
    connection_info: ConnectionInfo


@dataclass(frozen=True)
class MenuItemLayer:
    name: str
    provider: str
    connection_info: ConnectionInfo


@dataclass(frozen=True)
class MenuItemCluster:
    name: str
    layers: List[MenuItemLayer]


@dataclass(frozen=True)
class SubMenu:
    name: str
    items: List[MenuItem | MenuItemCluster]


@dataclass(frozen=True)
class Menu:
    name: str
    submenus: List[SubMenu]


@dataclass(frozen=True)
class CustomSearch:
    search_name: str
    target_layer_name: str
    search_attribute: str
    comparison_operator: str
    ui_hint: str
    results_display_columns: List[str]
    default_zoom_scale: int


@dataclass(frozen=True)
class PortalConfig:
    metadata: Dict[str, str]
    interface_customization: Dict[str, object]
    menus: List[Menu]
    custom_searches: List[CustomSearch]
