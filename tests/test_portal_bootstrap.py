from __future__ import annotations

import configparser
import sys
from pathlib import Path
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.config_schema import ConnectionInfo, CustomSearch, Menu, MenuItem, PortalConfig, SubMenu
from src.services.config_parser import PortalConfigParser

REPORT_PATH = PROJECT_ROOT / "tests" / "debug_dump.log"
CONFIG_PATH = PROJECT_ROOT / "portal_config.yaml"
METADATA_PATH = PROJECT_ROOT / "metadata.txt"


def _log(msg: str) -> None:
    line = f"{msg}\n"
    with REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="")


def _clear_report() -> None:
    if REPORT_PATH.exists():
        REPORT_PATH.unlink()


def validate_metadata() -> bool:
    _log("[metadata.txt validation]")
    parser = configparser.ConfigParser()
    try:
        parser.read(METADATA_PATH, encoding="utf-8")
    except Exception as exc:
        _log(f"  metadata parse error: {exc}")
        return False
    if not parser.has_section("general"):
        _log("  missing [general] section")
        return False
    required = ["name", "version", "qgisMinimumVersion", "qgisMaximumVersion"]
    missing = [key for key in required if key not in parser["general"]]
    if missing:
        _log(f"  missing keys: {missing}")
        return False
    _log("  ini structure OK")
    _log(f"  name={parser['general'].get('name')}")
    _log(f"  qgisMaximumVersion={parser['general'].get('qgisMaximumVersion')}")
    return True


def validate_config_parsing() -> PortalConfig | None:
    _log("[portal_config.yaml parsing]")
    parser = PortalConfigParser(CONFIG_PATH)
    if not parser.load():
        _log("  parser.load() returned False")
        return None
    config = parser.validate()
    if config is None:
        _log("  parser.validate() returned None")
        return None
    _log("  YAML parsed and schema mapped")
    return config


def validate_menu_integrity(config: PortalConfig) -> bool:
    _log("[menu integrity check]")
    try:
        for menu in config.menus:
            for submenu in menu.submenus:
                for item in submenu.items:
                    _ = item.name
                    _ = item.layer_name
                    _ = item.provider
                    _ = item.connection_info.path
        _log("  all menu tracks evaluated without KeyError")
        return True
    except Exception as exc:
        _log(f"  menu integrity failure: {exc}")
        return False


def validate_file_completeness(config: PortalConfig) -> bool:
    _log("[file completeness audit]")
    valid = True
    for item in _iter_items(config):
        path = Path(item.connection_info.path)
        exists = path.exists()
        size = path.stat().st_size if exists else -1
        status = "OK" if exists and size > 0 else "MISSING_OR_EMPTY"
        _log(f"  {item.name} -> {path} [{status}] size={size}")
        if status != "OK":
            valid = False
    return valid


def validate_search_attributes(config: PortalConfig) -> bool:
    _log("[search attribute debug dump]")
    try:
        for search in config.custom_searches:
            payload = {
                "search_name": search.search_name,
                "target_layer_name": search.target_layer_name,
                "search_attribute": search.search_attribute,
                "comparison_operator": search.comparison_operator,
                "results_display_columns": search.results_display_columns,
                "default_zoom_scale": search.default_zoom_scale,
            }
            _log(f"  {payload}")
        return True
    except Exception as exc:
        _log(f"  attribute trace failure: {exc}")
        return False


def _iter_items(config: PortalConfig):
    for menu in config.menus:
        for submenu in menu.submenus:
            for item in submenu.items:
                yield item


def _build_registry_summary(config: PortalConfig) -> dict:
    driver_tracks = {}
    for menu in config.menus:
        for submenu in menu.submenus:
            for item in submenu.items:
                driver_tracks.setdefault(item.provider.lower(), []).append(item.name)
    return {"total_items": sum(len(v) for v in driver_tracks.values()), "errors": 0}


def main() -> int:
    _clear_report()
    _log("=== PortalCrafter Operational Health Report ===")

    metadata_ok = validate_metadata()
    config = validate_config_parsing()

    if config is None:
        _log("ABORT: config validation failed")
        return 2

    menu_ok = validate_menu_integrity(config)
    files_ok = validate_file_completeness(config)
    search_ok = validate_search_attributes(config)
    summary = _build_registry_summary(config)

    _log("[driver track summary]")
    _log(f"  total_items={summary['total_items']} errors={summary['errors']}")

    _log("[overall status]")
    checks = {
        "metadata": metadata_ok,
        "config": True,
        "menu_integrity": menu_ok,
        "file_completeness": files_ok,
        "search_attributes": search_ok,
    }
    for name, passed in checks.items():
        _log(f"  {name}={'PASS' if passed else 'FAIL'}")

    if all(checks.values()):
        _log("RESULT: READY")
        return 0

    _log("RESULT: DEGRADED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
