#!/usr/bin/env python3
"""
Diversified flat-file format staging.

Converts a set of GeoJSON sources into:
- GeoPackage (.gpkg)
- SpatiaLite (.sqlite)
- ESRI Shapefile (.shp)
- KML (.kml)
- GeoJSON retention for heritage

Only performs cleanup when conversion succeeds.
"""

import shutil
import subprocess
from pathlib import Path

BASE = Path("/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input")

JOBS = [
    {
        "label": "cadastre",
        "src": BASE / "cadastre" / "nsw_parcels_staging.geojson",
        "out": BASE / "cadastre" / "nsw_parcels_staging.gpkg",
        "fmt": "GPKG",
        "extra": [],
        "delete_src": True,
    },
    {
        "label": "roads",
        "src": BASE / "roads" / "nsw_roads_staging.geojson",
        "out": BASE / "roads" / "nsw_roads_staging.sqlite",
        "fmt": "SQLite",
        "extra": ["-dsco", "SPATIALITE=YES"],
        "delete_src": True,
    },
    {
        "label": "state_heritage",
        "src": BASE / "heritage" / "state_heritage_register.geojson",
        "out": BASE / "heritage" / "state_heritage_register.geojson",
        "fmt": "GeoJSON",
        "delete_src": False,
    },
    {
        "label": "epi_terrestrial_biodiversity",
        "src": BASE / "heritage" / "epi_terrestrial_biodiversity.geojson",
        "out": BASE / "heritage" / "epi_terrestrial_biodiversity" / "epi_terrestrial_biodiversity.shp",
        "fmt": "ESRI Shapefile",
        "extra": [],
        "mkdir": True,
        "delete_src": True,
    },
    {
        "label": "regional_biodiversity_corridors",
        "src": BASE / "heritage" / "regional_biodiversity_corridors.geojson",
        "out": BASE / "heritage" / "regional_biodiversity_corridors.kml",
        "fmt": "KML",
        "extra": [],
        "delete_src": True,
    },
]


def convert_job(job):
    label = job["label"]
    src = job["src"]
    out = job["out"]

    print(("\n[{label}] source: {src}").format(label=label, src=src))
    if not src.exists():
        print(("[{label}] SKIP: missing source").format(label=label))
        return

    if job.get("mkdir"):
        parent = out.parent
        if not parent.exists():
            parent.mkdir(parents=True, exist_ok=True)

    cmd = ["ogr2ogr", "-f", job["fmt"], str(out), str(src)] + job.get("extra", [])
    print(("[{label}] RUN: {cmd}").format(label=label, cmd=" ".join(cmd)))
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
    if proc.returncode != 0:
        print(("[{label}] FAIL (exit={code})\n{out}").format(label=label, code=proc.returncode, out=proc.stdout))
        return

    delete_src = job.get("delete_src", False)
    if out.exists() and (out.stat().st_size > 0 or not delete_src):
        if delete_src:
            src.unlink()
            print(("[{label}] OK: converted -> {out}").format(label=label, out=out))
        else:
            print(("[{label}] OK: preserved source -> {src}").format(label=label, src=src))
    else:
        print(("[{label}] FAIL: output missing or empty").format(label=label))


def audit():
    print("\n=== Diversified Flat-File Schema Audit ===")
    for p in sorted(BASE.rglob("*")):
        if p.is_file():
            print("{rel}\t{size} bytes".format(rel=p.relative_to(BASE), size=p.stat().st_size))


def main():
    for job in JOBS:
        convert_job(job)
    audit()


if __name__ == "__main__":
    main()
