"""
QGIS PortalCrafter Initialization Engine
"""

import sys
from pathlib import Path

# QGIS adds the immediate plugin directory to sys.path.
# We need the sibling 'src/' package inside the plugin tree to be importable too.
PLUGIN_DIR = Path(__file__).resolve().parent
SRC_DIR = PLUGIN_DIR / "src"
for candidate in (str(SRC_DIR), str(PLUGIN_DIR)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def classFactory(iface):
    from .startup import PortalCrafterPlugin
    return PortalCrafterPlugin(iface)
