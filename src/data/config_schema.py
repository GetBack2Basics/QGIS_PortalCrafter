from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


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

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "MenuItem":
        connection = raw.get("connection_info", {})
        return cls(
            name=raw.get("name", ""),
            layer_name=raw.get("layer_name", ""),
            provider=raw.get("provider", "ogr"),
            connection_info=ConnectionInfo(
                path=connection.get("path", ""),
                layer_name=connection.get("layer_name"),
            ),
        )

    def to_layer(self) -> "MenuItemLayer":
        connection = self.connection_info
        return MenuItemLayer(
            name=self.name,
            provider=self.provider,
            connection_info=ConnectionInfo(
                path=connection.path,
                layer_name=connection.layer_name or self.layer_name,
            ),
        )


@dataclass(frozen=True)
class MenuItemLayer:
    name: str
    provider: str
    connection_info: ConnectionInfo


@dataclass(frozen=True)
class MenuItemCluster:
    name: str
    layers: List[MenuItemLayer]

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "MenuItemCluster":
        raw_layers = raw.get("layers", [])
        parsed: List[MenuItemLayer] = []
        for raw_layer in raw_layers:
            connection = raw_layer.get("connection_info", {})
            layer_name = connection.get("layer_name") or raw_layer.get("layer_name", "")
            parsed.append(
                MenuItemLayer(
                    name=raw_layer.get("layer_name", layer_name),
                    provider=raw_layer.get("provider", "ogr"),
                    connection_info=ConnectionInfo(
                        path=connection.get("path", ""),
                        layer_name=(layer_name or None),
                    ),
                )
            )
        return cls(name=raw.get("name", ""), layers=parsed)


@dataclass(frozen=True)
class SubMenu:
    name: str
    items: List[Union[MenuItem, MenuItemCluster]]


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

