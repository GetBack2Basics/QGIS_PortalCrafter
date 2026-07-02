from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QMessageBox, QDialog
from qgis.utils import iface
import os
from pathlib import Path

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry
from src.services.ui_cleaner import PortalUICleaner
from src.services.deployment_cleanup import DeploymentCleanup
from src.components.menu_factory import PortalMenuFactory
from src.components.search_dock import PortalSearchDock
from src.components.startup_selector import PortalStartupSelector


STAGE = "init"


class PortalCrafterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.parser = PortalConfigParser(
            "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/portal_config.yaml"
        )
        self.registry = LayerRegistry()
        self.cleaner: PortalUICleaner | None = None
        self.menu_factory: PortalMenuFactory | None = None
        self.search_dock: PortalSearchDock | None = None
        STAGE = "init_done"

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
            "PortalCrafter: initGui STAGE=%s" % STAGE,
            level=Qgis.MessageLevel.Info,
        )
        self._clean_deployed()
        self._bootstrap_delayed = True
        QTimer.singleShot(500, self._deferred_bootstrap)

    def _deferred_bootstrap(self) -> None:
        self._bootstrap_delayed = False
        self._show_startup_selector()

    def _show_startup_selector(self) -> None:
        selector = PortalStartupSelector(self.iface.mainWindow())
        result = selector.exec()
        if result != QDialog.DialogCode.Accepted:
            return
        profile = selector.selected_profile()
        if profile == "FullQGIS":
            return
        # TEMPORARY ISOLATION: disable cultural project load until segfault source is known
        if profile == "Cultural":
            QTimer.singleShot(0, self._load_cultural_project)
        self._bootstrap_cultural()

    def _bootstrap_cultural(self) -> None:
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
        # TEMPORARY ISOLATION: skip UI/profile cleanup until segfault source is known
        self.registry.register_config(config)
        self.menu_factory = PortalMenuFactory(self.iface, self.registry, config)
        self.menu_factory.build()
        QgsMessageLog.logMessage(
            "PortalCrafter CPO ready.",
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
        if self.cleaner:
            self.cleaner.restore()
        if getattr(self, 'menu_factory', None):
            self.menu_factory._clear_existing()
        if getattr(self, 'search_dock', None):
            try:
                self.iface.mainWindow().removeDockWidget(self.search_dock)
                self.search_dock.deleteLater()
            except Exception:
                pass
        menu_bar = self.iface.mainWindow().menuBar()
        for action in menu_bar.actions():
            menu = action.menu()
            if menu is not None and menu.title() == "PortalCrafter":
                menu_bar.removeAction(action)
                break


def run():
    bootstrap = PortalCrafterPlugin(iface)
    bootstrap.initGui()
    return bootstrap
