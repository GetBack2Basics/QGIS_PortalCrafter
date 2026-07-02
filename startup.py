from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis.PyQt.QtWidgets import QMenu, QAction
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface
import os
from pathlib import Path

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry
from src.services.deployment_cleanup import DeploymentCleanup
from src.components.menu_factory import PortalMenuFactory


class PortalCrafterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.parser = PortalConfigParser(
            "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/portal_config.yaml"
        )
        self.registry = LayerRegistry()
        self.menu_factory: PortalMenuFactory | None = None
        self._root_menu: QMenu | None = None

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
        self._clean_deployed()
        iface = self.iface

        self._root_menu = QMenu("PortalCrafter", iface.mainWindow())
        menubar = iface.mainWindow().menuBar()
        menubar.addMenu(self._root_menu)

        full = self._root_menu.addAction("Full QGIS")
        full.triggered.connect(lambda: self._bootstrap("FullQGIS"))

        cultural = self._root_menu.addAction("Cultural")
        cultural.triggered.connect(lambda: self._bootstrap("Cultural"))

        bio = self._root_menu.addAction("Biodiversity")
        bio.triggered.connect(lambda: self._bootstrap("Biodiversity"))

    def _bootstrap(self, profile: str) -> None:
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
        self.menu_factory.build()
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

    def unload(self):
        if getattr(self, "_root_menu", None):
            self.iface.mainWindow().menuBar().removeAction(self._root_menu.menuAction())
