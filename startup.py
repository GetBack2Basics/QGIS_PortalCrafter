from qgis.core import QgsMessageLog, Qgis
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.utils import iface

from src.services.config_parser import PortalConfigParser
from src.services.layer_registry import LayerRegistry
from src.services.ui_cleaner import PortalUICleaner
from src.components.menu_factory import PortalMenuFactory
from src.components.search_dock import PortalSearchDock


class PortalCrafterPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.actions = []
        self.parser = PortalConfigParser(
            "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/portal_config.yaml"
        )
        self.registry = LayerRegistry()
        self.cleaner: PortalUICleaner | None = None
        self.menu_factory: PortalMenuFactory | None = None
        self.search_dock: PortalSearchDock | None = None

    def initGui(self):
        action = QAction("PortalCrafter CPO", self.iface.mainWindow())
        action.triggered.connect(self._on_open)
        self.iface.addPluginToMenu("&PortalCrafter CPO", action)
        self.actions.append(action)

        self._bootstrap()

    def _bootstrap(self) -> None:
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
        self.cleaner = PortalUICleaner(self.iface, config)
        self.cleaner.apply()
        self.menu_factory = PortalMenuFactory(self.iface, self.registry, config)
        self.menu_factory.build()
        # Qt6-qualified dock placement flags
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

    def _on_open(self):
        QMessageBox.information(
            self.iface.mainWindow(),
            "PortalCrafter CPO",
            "PortalCrafter CPO initialized.",
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
        self.actions = []


def run():
    bootstrap = PortalBootstrap(iface)
    bootstrap.initGui()
    return bootstrap
