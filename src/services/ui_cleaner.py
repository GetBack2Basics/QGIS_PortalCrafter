from __future__ import annotations

from typing import Dict, List

try:
    from qgis.core import QgsMessageLog, Qgis  # type: ignore
except ModuleNotFoundError:
    QgsMessageLog = None  # type: ignore
    Qgis = None  # type: ignore

try:
    from qgis.PyQt.QtWidgets import QToolBar, QDockWidget  # type: ignore
except ModuleNotFoundError:  # headless
    QToolBar = object  # type: ignore
    QDockWidget = object  # type: ignore

from qgis.PyQt.QtCore import QCoreApplication  # type: ignore

from src.data.config_schema import PortalConfig  # noqa: E402


class PortalUICleaner:
    def __init__(self, iface, config: PortalConfig) -> None:
        self.iface = iface
        self.config = config
        self.hidden_toolbars: List = []
        self.hidden_docks: List = []

    def apply(self) -> None:
        targets = (self.config.interface_customization or {}).get("hidden_toolbars", [])
        docks = (self.config.interface_customization or {}).get("hidden_docks", [])
        main = self.iface.mainWindow() if self.iface is not None else None
        if main is not None:
            for toolbar in main.findChildren(QToolBar):
                if hasattr(toolbar, "objectName") and toolbar.objectName() in targets:
                    toolbar.setVisible(False)
                    self.hidden_toolbars.append(toolbar)
            for dock in main.findChildren(QDockWidget):
                name = dock.windowTitle() if hasattr(dock, "windowTitle") else ""
                obj_name = dock.objectName() if hasattr(dock, "objectName") else ""
                if name in docks or obj_name in docks:
                    dock.setVisible(False)
                    self.hidden_docks.append(dock)
        self._log(
            "Interface cleaned for profile: %s"
            % (self.config.interface_customization or {}).get("profile_name", "default"),
            level="info",
        )

    def restore(self) -> None:
        for toolbar in self.hidden_toolbars:
            toolbar.setVisible(True)
        for dock in self.hidden_docks:
            dock.setVisible(True)
        self._log("Default interface restored.", level="info")
        self.hidden_toolbars.clear()
        self.hidden_docks.clear()

    def _log(self, message: str, level: str = "info") -> None:
        if QgsMessageLog is not None and Qgis is not None and QCoreApplication is not None:
            lvl = {
                "info": Qgis.MessageLevel.Info,
                "warning": Qgis.MessageLevel.Warning,
                "critical": Qgis.MessageLevel.Critical,
            }.get(level, Qgis.MessageLevel.Info)
            QgsMessageLog.logMessage(message, level=lvl)
        else:
            print("[%s] %s" % (level.upper(), message))
