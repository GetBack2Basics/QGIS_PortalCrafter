# DeployUTCMarker=202607030447
from __future__ import annotations

from pathlib import Path
from typing import Optional

from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis.PyQt.QtWidgets import QAction, QDockWidget
from qgis.PyQt.QtCore import Qt
from qgis.utils import iface
import os

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry, purge_active_portal_layers
from src.services.deployment_cleanup import DeploymentCleanup
from src.components.menu_factory import PortalMenuFactory
from src.components.search_dock import PortalSearchDock


class PortalCrafterPlugin:
    TP_TAG = "PortalCrafter"
    INDEX_PATH = str(Path("/media/george-corea/GIS/Projects/QGIS_PortalCrafter/portal_profiles.yaml"))

    def _ep(self, message: str) -> None:
        QgsMessageLog.logMessage(message, self.TP_TAG, level=Qgis.MessageLevel.Warning)

    def __init__(self, iface):
        self.iface = iface
        self.parser = PortalConfigParser(self.INDEX_PATH)
        self.registry = LayerRegistry()
        self.menu_factory: Optional[PortalMenuFactory] = None
        self.search_dock = None
        self.index = None

    def initGui(self):
        QgsMessageLog.logMessage(
            "PortalCrafter: initGui STAGE=init two-tier",
            level=Qgis.MessageLevel.Info,
        )
        self._ep("initGui enter")

        self.index = self.parser.boot_loader()
        if not self.index.profiles:
            QgsMessageLog.logMessage(
                "PortalCrafter: no profiles loaded from %s" % self.INDEX_PATH,
                level=Qgis.MessageLevel.Critical,
            )
            return
        QgsMessageLog.logMessage(
            "PortalCrafter: boot loaded profiles=%s" % ",".join(self.index.ids()),
            level=Qgis.MessageLevel.Info,
        )

        self.menu_factory = PortalMenuFactory(self.iface, self.registry, self.parser)
        self.menu_factory.purge_existing_menus()
        self.menu_factory.build_boot_anchors(
            self.index,
            profile_click_callback=self.transition_portal_profile,
        )

        first_config = None
        if self.index and self.index.profiles:
            first_config = self.parser.lazy_loader(self.index.profiles[0].profile_id)
            self._ep("initGui search config type=%s" % type(first_config).__name__)
        self.search_dock = PortalSearchDock(self.iface.mainWindow(), registry=self.registry, config=first_config)
        self.iface.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.search_dock)
        self._ep("initGui exit")

    def transition_portal_profile(self, target_profile_id: str, config_file: Optional[str] = None) -> None:
        self._ep("transition enter target=%s" % target_profile_id)
        try:
            purge_active_portal_layers()
            project_path = self._profile_project_path(target_profile_id)
            if project_path and os.path.exists(project_path):
                self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
                QgsProject.instance().read(project_path)
                self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
            self.menu_factory.build_submenus_for_profile(target_profile_id, overwrite=True)
            if getattr(self, 'search_dock', None):
                cfg = None
                if self.index:
                    cfg = self.parser.lazy_loader(target_profile_id)
                self.search_dock.refresh(config=cfg)
            QgsMessageLog.logMessage(
                "PortalCrafter: profile transition complete target=%s" % target_profile_id,
                level=Qgis.MessageLevel.Info,
            )
        except Exception as exc:
            QgsMessageLog.logMessage(
                "PortalCrafter: profile transition failed: %s" % exc,
                "PortalCrafter",
                level=Qgis.MessageLevel.Critical,
            )
            self._ep("transition failed: %s" % exc)

    def _profile_project_path(self, target_profile_id: str) -> Optional[str]:
        entry = None
        if self.index:
            entry = self.index.find(target_profile_id)
        if entry is None or not entry.project_workspace:
            base = Path("/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/projects")
            candidate = base / ("%s.qgz" % target_profile_id)
            return str(candidate) if candidate.exists() else None
        return entry.project_workspace

    def apply_profile_lazy(self, target_profile_id: str) -> None:
        if self.menu_factory is None:
            return
        if target_profile_id not in (self.index.profiles if self.index else []):
            return
        QgsMessageLog.logMessage(
            "PortalCrafter: lazy apply start profile=%s" % target_profile_id,
            level=Qgis.MessageLevel.Info,
        )
        purge_active_portal_layers()
        project_path = self._profile_project_path(target_profile_id)
        if project_path and os.path.exists(project_path):
            self.iface.mainWindow().setCursor(Qt.CursorShape.WaitCursor)
            QgsProject.instance().read(project_path)
            self.iface.mainWindow().setCursor(Qt.CursorShape.ArrowCursor)
        self.menu_factory.build_submenus_for_profile(target_profile_id, overwrite=False)

    def unload(self):
        if self.menu_factory is not None:
            self.menu_factory.purge_existing_menus()
        QgsMessageLog.logMessage(
            "PortalCrafter: unloaded",
            level=Qgis.MessageLevel.Info,
        )
