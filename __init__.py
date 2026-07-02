"""
QGIS PortalCrafter Initialization Engine
Version UTCMarker=202607020631
"""

import sys
from pathlib import Path

# QGIS adds the plugin directory to sys.path.
# Make sibling 'src/' importable too.
PLUGIN_DIR = Path(__file__).resolve().parent
SRC_DIR = PLUGIN_DIR / "src"
for candidate in (str(SRC_DIR), str(PLUGIN_DIR)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)


def classFactory(iface):
    from startup import PortalCrafterPlugin
    return PortalCrafterPlugin(iface)
