from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable, List, Tuple


class DeploymentCleanup:
    """Remove runtime artifacts left after plugin updates.

    Strict scope:
    - targets only known-stale sibling plugin dirs named ``portalcrafter_*``
      under the QGIS plugins root, never the active ``QGIS_PortalCrafter`` dir.
    - only removes ``__pycache__`` directories that are not the active module's
      own cache folder during bootstrap.
    """

    STALE_PREFIX = "portalcrafter_"
    ACTIVE_DIR_NAME = "QGIS_PortalCrafter"

    @staticmethod
    def _remove_paths(paths: Iterable[Path]) -> List[Tuple[Path, bool, str]]:
        results: List[Tuple[Path, bool, str]] = []
        for path in paths:
            try:
                if path.exists():
                    shutil.rmtree(path)
                    results.append((path, True, ""))
                    continue
            except Exception as exc:  # noqa: BLE001
                results.append((path, False, str(exc)))
                continue
            results.append((path, False, "missing"))
        return results

    @classmethod
    def _collect_pycache(cls, root: Path, active_dir: Path) -> List[Path]:
        matches: List[Path] = []
        try:
            active_pycache = (active_dir / "__pycache__").resolve()
        except OSError:
            active_pycache = None
        for parent, dir_names, _files in os.walk(root):
            for directory in dir_names:
                if directory != "__pycache__":
                    continue
                path = Path(parent, directory)
                try:
                    path_resolved = path.resolve()
                except OSError:
                    continue
                if active_pycache and path_resolved == active_pycache:
                    continue
                matches.append(path)
        return matches

    @classmethod
    def _collect_stale_dirs(cls, root: Path, active_dir: Path) -> List[Path]:
        matches: List[Path] = []
        active_resolved = None
        try:
            active_resolved = active_dir.resolve()
        except OSError:
            pass
        for child in root.iterdir():
            if not child.is_dir() or child.is_symlink():
                continue
            if child.name == cls.ACTIVE_DIR_NAME:
                continue
            if not child.name.startswith(cls.STALE_PREFIX):
                continue
            try:
                child_resolved = child.resolve()
            except OSError:
                child_resolved = None
            if active_resolved and child_resolved == active_resolved:
                continue
            matches.append(child)
        return matches

    @classmethod
    def clean_deployed(cls, plugin_root: Path | str, active_dir: Path | str | None = None) -> List[Tuple[str, bool, str]]:
        plugin_root = Path(plugin_root)
        active_dir = Path(active_dir) if active_dir is not None else plugin_root
        targets: List[Path] = cls._collect_pycache(plugin_root, active_dir) + cls._collect_stale_dirs(plugin_root, active_dir)
        return [
            (str(path), success, message)
            for path, success, message in cls._remove_paths(targets)
        ]
