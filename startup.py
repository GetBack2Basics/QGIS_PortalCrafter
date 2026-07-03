# DeployUTCMarker=202607020620
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface
import os

# Deploy version marker for identifying deployed build.
PLUGIN_VERSION = datetime.now().strftime("%Y%m%d%H%M")

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry, purge_active_portal_layers
from src.services.deployment_cleanup import DeploymentCleanup
from src.components.menu_factory import PortalMenuFactory


class PortalCrafterPlugin:
    TP_TAG = "PortalCrafter|plugin"

    def _ep(self, message: str) -> None:
        QgsMessageLog.logMessage(message, self.TP_TAG, level=Qgis.MessageLevel.Warning)

    def __init__(self, iface):
        self.iface = iface
        self.parser = PortalConfigParser(
            "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/portal_config.yaml"
        )
        self.registry = LayerRegistry()
        self.menu_factory: Optional[PortalMenuFactory] = None
        self._root_menu: Optional[QMenu] = None
        self._active_profile: str = "PortalCrafter"

    def _clean_deployed(self) -> None:
        active_dir = Path(__file__).resolve().parent
        plugin_dir = active_dir.parent
        results = DeploymentCleanup.clean_deployed(plugin_root=plugin_dir, active_dir=active_dir)
        removed = sum(1 for _, ok, _ in results if ok)
        if removed:
            QgsMessageLog.logMessage(
                "PortalCrafter: cleaned %d deployed module artifacts before bootstrap."
                % removed,
                level=Qgis.MessageLevel.Info,
            )

    def _available_profile_names(self) -> "list[str]":
        discovered: "list[str]" = []
        try:
            base = Path("/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/projects")
            if base.exists():
                for path in sorted(base.glob("*.qgz")):
                    discovered.append(path.stem)
        except Exception as exc:
            self._ep("profile discovery failed: %s" % exc)
            QgsMessageLog.logMessage(
                "PortalCrafter: profile discovery failed: %s" % exc,
                "PortalCrafter",
                level=Qgis.MessageLevel.Warning,
            )
        if not discovered:
            discovered = ["Cultural", "Environment"]
        QgsMessageLog.logMessage(
            "PortalCrafter: discovered profiles=%s" % ",".join(discovered),
            "PortalCrafter",
            level=Qgis.MessageLevel.Info,
        )
        return discovered

    def initGui(self):
        QgsMessageLog.logMessage(
            "PortalCrafter: initGui STAGE=init version=%s build=%s"
            % (PLUGIN_VERSION, Path(__file__).resolve()),
            level=Qgis.MessageLevel.Info,
        )
        self._ep("initGui enter")
        self._clean_deployed()
        iface = self.iface

        available = self._available_profile_names()
        initial_profile = available[0] if available else "Cultural"
        QgsMessageLog.logMessage(
            "PortalCrafter: initGui initial_profile=%s" % initial_profile,
            level=Qgis.MessageLevel.Info,
        )
        self.transition_portal_profile(initial_profile)
        self._ep("initGui exit")

    def transition_portal_profile(self, target_profile_name: str) -> None:
        QgsMessageLog.logMessage(
            "PortalCrafter: transition_portal_profile start target=%s" % target_profile_name,
            level=Qgis.MessageLevel.Info,
        )
        self._ep("transition enter target=%s" % target_profile_name)
        try:
            purge_active_portal_layers()
            self._load_profile_project(target_profile_name)
            if not self.parser.load():
                QgsMessageLog.logMessage(
                    "PortalCrafter: config loader returned False.",
                    level=Qgis.MessageLevel.Warning,
                )
                return
            config = self.parser.validate()
            if config is None:
                QgsMessageLog.logMessage(
                    "PortalCrafter: config schema validation failed.",
                    level=Qgis.MessageLevel.Warning,
                )
                return
            QgsMessageLog.logMessage(
                "PortalCrafter: config loaded menus=%d custom_searches=%d"
                % (len(config.menus), len(config.custom_searches)),
                level=Qgis.MessageLevel.Info,
            )
            self.registry.register_config(config)
            self.menu_factory = PortalMenuFactory(self.iface, self.registry, config)
            self.menu_factory.build(
                active_profile_name=target_profile_name,
                profile_click_callback=self.transition_portal_profile,
            )
            self._active_profile = target_profile_name
            QgsMessageLog.logMessage(
                "PortalCrafter CPO ready (%s)." % target_profile_name,
                level=Qgis.MessageLevel.Info,
            )
        except Exception as exc:
            QgsMessageLog.logMessage(
                "PortalCrafter: profile transition failed: %s" % exc,
                "PortalCrafter",
                level=Qgis.MessageLevel.Critical,
            )
            self._ep("transition failed: %s" % exc)

    def _load_profile_project(self, target_profile_name: str) -> None:
        project_path = "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/projects/%s.qgz" % target_profile_name
        if project_path and os.path.exists(project_path):
            self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
            ok = QgsProject.instance().read(project_path)
            self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
            if not ok:
                QgsMessageLog.logMessage(
                    "QgsProject.read failed: %s" % project_path,
                    "PortalCrafter",
                    level=Qgis.MessageLevel.Critical,
                )
        else:
            QgsMessageLog.logMessage(
                "PortalCrafter: missing profile project file '%s'; continuing with current project."
                % project_path,
                level=Qgis.MessageLevel.Warning,
            )

    def reset_loaded_keys(self) -> None:
        if self.menu_factory is not None:
            self.menu_factory.loaded_keys.clear()
        if self._root_menu is not None:
            for action in self._root_menu.actions():
                action.setEnabled(True)

    def unload(self):
        menubar = self.iface.mainWindow().menuBar()
        for action in list(menubar.actions()):
            menu = action.menu()
            if menu is not None and menu.title() == "PortalCrafter":
                menubar.removeAction(action)
        QgsMessageLog.logMessage(
            "PortalCrafter: unloaded",
            level=Qgis.MessageLevel.Info,
        )
