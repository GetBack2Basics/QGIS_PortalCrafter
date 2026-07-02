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
PLUGIN_VERSION = datetime.utcnow().strftime("%Y%m%d%H%M")

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry, purge_active_portal_layers
from src.services.deployment_cleanup import DeploymentCleanup
from src.components.menu_factory import PortalMenuFactory


class PortalCrafterPlugin:
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

    def initGui(self):
        QgsMessageLog.logMessage(
            "PortalCrafter: initGui STAGE=init version=%s build=%s"
            % (PLUGIN_VERSION, Path(__file__).resolve()),
            level=Qgis.MessageLevel.Info,
        )
        self._clean_deployed()
        iface = self.iface

        self._root_menu = QMenu("PortalCrafter", iface.mainWindow())
        menubar = iface.mainWindow().menuBar()
        menubar.addMenu(self._root_menu)

        bootstrap_action = self._root_menu.addAction("Load Workspace")
        bootstrap_action.triggered.connect(lambda: self._bootstrap(self._active_profile))

    def _bootstrap(self, profile: str) -> None:
        QgsMessageLog.logMessage(
            "PortalCrafter: bootstrap profile=%s" % profile,
            level=Qgis.MessageLevel.Info,
        )

        if profile == "Cultural":
            self._load_cultural_project()

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

        self.registry.register_config(config)
        self.menu_factory = PortalMenuFactory(self.iface, self.registry, config)
        self.menu_factory.build(
            active_profile_name=profile,
            profile_switcher_callback=self.transition_portal_profile,
        )
        self._active_profile = profile
        QgsMessageLog.logMessage(
            "PortalCrafter CPO ready (%s)." % profile,
            level=Qgis.MessageLevel.Info,
        )

    def _load_cultural_project(self) -> None:
        project_path = "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/projects/cultural.qgz"
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

    def transition_portal_profile(self, target_profile_name: str) -> None:
        QgsMessageLog.logMessage(
            "PortalCrafter: transition_portal_profile start target=%s" % target_profile_name,
            level=Qgis.MessageLevel.Info,
        )
        try:
            purge_active_portal_layers()
            self._remove_root_menu_actions(["PortalCrafter", self._active_profile])
            self._load_profile_project(target_profile_name)
            if self.menu_factory is not None:
                self.menu_factory.loaded_keys.clear()
                for action in self.menu_factory.created_actions:
                    action.setEnabled(True)
            self._bootstrap(target_profile_name)
        except Exception as exc:
            QgsMessageLog.logMessage(
                "PortalCrafter: profile transition failed: %s" % exc,
                "PortalCrafter",
                level=Qgis.MessageLevel.Critical,
            )

    def _remove_root_menu_actions(self, titles) -> None:
        menubar = self.iface.mainWindow().menuBar()
        for action in list(menubar.actions()):
            menu = action.menu()
            if menu and menu.title() in titles:
                menubar.removeAction(action)

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
        if getattr(self, "_root_menu", None):
            self.iface.mainWindow().menuBar().removeAction(self._root_menu.menuAction())
        QgsMessageLog.logMessage(
            "PortalCrafter: unloaded",
            level=Qgis.MessageLevel.Info,
        )
