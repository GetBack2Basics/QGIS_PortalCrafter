#!/usr/bin/env python3
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
DEPLOY = Path.home() / ".local/share/QGIS/QGIS4/profiles/default/python/plugins/QGIS_PortalCrafter"

if not (REPO / "startup.py").exists() or not (REPO / "src").exists():
    print("Repo not found:", REPO, file=sys.stderr)
    sys.exit(1)

print("Deleting deployed plugin contents:", DEPLOY)
if DEPLOY.exists():
    for child in DEPLOY.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
else:
    DEPLOY.mkdir(parents=True)

print("Copying repo -> deploy...")
for item in REPO.iterdir():
    if item.name == ".git":
        continue
    dst = DEPLOY / item.name
    if item.is_dir() and not item.is_symlink():
        shutil.copytree(item, dst)
    else:
        shutil.copy2(item, dst)

print("Done.")
