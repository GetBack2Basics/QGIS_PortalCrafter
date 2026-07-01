from qgis.core import QgsMessageLog, Qgis, QgsProject
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.utils import iface
import os

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry
from src.services.ui_cleaner import PortalUICleaner
from src.components.menu_factory import PortalMenuFactory
from src.components.search_dock import PortalSearchDock
from src.components.startup_selector import PortalStartupSelector


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

    def initGui(self):
        QTimer.singleShot(0, self._show_startup_selector)

    def _show_startup_selector(self) -> None:
        selector = PortalStartupSelector(self.iface.mainWindow())
        result = selector.exec()
        if result != QDialog.DialogCode.Accepted:
            return
        profile = selector.selected_profile()
        if profile == "FullQGIS":
            return
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
        project_path = "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/projects/cultural.qgz"
        if project_path and os.path.exists(project_path):
            QgsProject.instance().read(project_path)
        else:
            QgsMessageLog.logMessage(
                "Target workspace file not found at: %s" % project_path,
                "PortalCrafter",
                Qgis.MessageLevel.Critical,
            )
        self.registry.register_config(config)
        self.cleaner = PortalUICleaner(self.iface, config)
        self.cleaner.apply()
        self.menu_factory = PortalMenuFactory(self.iface, self.registry, config)
        self.menu_factory.build()
        self.search_dock = PortalSearchDock(self.iface.mainWindow(), registry=self.registry, config=config)
        self.search_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.iface.mainWindow().addDockWidget(
            Qt.DockWidgetArea.RightDockWidgetArea,
            self.search_dock,
        )
        QgsMessageLog.logMessage(
            "PortalCrafter CPO ready.",
            level=Qgis.MessageLevel.Info,
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
