#!/usr/bin/env python3
"""
Robust regional data fetcher for Newcastle/Hunter envelope.

Features:
- Service health probe before heavy download
- Alternate layer/catalog fallback within same NSW Spatial services
- Retry with exponential backoff for transient HTTP 503/404
- Chunked pagination to avoid server memory throttles
- Writes GeoJSON stage files under input/, compatible with scripts/diversify_formats.py

Usage:
  python3 scripts/fetch_data_robust.py
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path

BASE = Path("/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input")
NEWCASTLE_BBOX = [149.8, -33.2, 152.2, -31.5]
SPATIAL_REF = "4326"
REQUEST_TIMEOUT = 180
MAX_RETRIES = 3
BACKOFF_BASE = 10  # seconds


# --------- HTTP helpers ---------
def request_json(url, timeout=REQUEST_TIMEOUT):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def probe_service(service_url):
    try:
        data = request_json(f"{service_url}?f=json", timeout=60)
        return bool(data.get("name") or data.get("layers"))
    except Exception:
        return False


def fetch_with_backoff(url):
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return request_json(url)
        except Exception as e:
            last_err = e
            wait = BACKOFF_BASE * (2 ** (attempt - 1))
            time.sleep(wait)
    raise last_err


# --------- FeatureServer downloader ---------
def feature_server_download(service_url, output_file, bbox, spatial_ref=SPATIAL_REF):
    minx, miny, maxx, maxy = bbox
    bbox_str = f"{minx},{miny},{maxx},{maxy}"

    # 1. objectIds
    id_url = (
        f"{service_url}/query?"
        f"where=1%3D1&geometry={urllib.parse.quote(bbox_str)}"
        f"&geometryType=esriGeometryEnvelope&inSR={spatial_ref}"
        f"&spatialRel=esriSpatialRelIntersects&returnIdsOnly=true&f=json"
    )
    try:
        id_data = fetch_with_backoff(id_url)
    except Exception as e:
        raise RuntimeError(f"ID query failed for {service_url}: {e}")

    object_ids = id_data.get("objectIds") or []
    if not object_ids:
        print(f"  ⚠️ No features intersect bbox for {output_file}")
        return 0

    # 2. chunked feature download
    chunk_size = 500
    features = []
    for start in range(0, len(object_ids), chunk_size):
        chunk = object_ids[start : start + chunk_size]
        chunk_str = ",".join(map(str, chunk))
        feat_url = (
            f"{service_url}/query?"
            f"objectIds={urllib.parse.quote(chunk_str)}"
            f"&outFields=*&returnGeometry=true&outSR={spatial_ref}&f=geojson"
        )
        try:
            feat_data = fetch_with_backoff(feat_url)
        except Exception as e:
            raise RuntimeError(f"Feature query failed for {service_url}: {e}")
        features.extend(feat_data.get("features") or [])
        print(f"  Loaded {len(features)} / {len(object_ids)} ...")

    out_dir = Path(output_file).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, ensure_ascii=False, indent=2)
    print(f"  ✅ Created {output_file} ({len(features)} features)")
    return len(features)


def safe_download(label, candidates, output_file):
    print(f"\n🚀 {label} -> {output_file}")
    for url in candidates:
        print(f"  Trying {url}")
        try:
            if not probe_service(url):
                print("  ❌ Service probe failed")
                continue
            feature_server_download(url, output_file, NEWCASTLE_BBOX)
            return True
        except Exception as e:
            print(f"  ❌ Source failure: {e}")
            continue
    print(f"  ⛔ All candidates failed for {label}")
    return False


def main():
    # Format: label -> ordered candidate service URLs
    TARGETS = {
        "cadastre": {
            "candidates": [
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Parcel_Property_Theme/FeatureServer/8",
            ],
            "output": BASE / "cadastre" / "nsw_parcels_staging.geojson",
        },
        "roads": {
            "candidates": [
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme/FeatureServer/6",
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme/FeatureServer/5",
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme/FeatureServer/0",
            ],
            "output": BASE / "roads" / "nsw_roads_staging.geojson",
        },
        "watercourse": {
            "candidates": [
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Water_Theme/FeatureServer/3",
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Water_Theme/FeatureServer/0",
            ],
            "output": BASE / "hydrography" / "nsw_hydro_watercourses.geojson",
        },
        "npws": {
            "candidates": [
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer/6",
            ],
            "output": BASE / "biodiversity" / "npws_estate_reserves.geojson",
        },
        "mine_subsidence": {
            "candidates": [
                "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer/7",
            ],
            "output": BASE / "environmental_hazards" / "mine_subsidence_districts.geojson",
        },
    }

    results = {}
    for label, info in TARGETS.items():
        success = safe_download(label, info["candidates"], info["output"])
        results[label] = "ok" if success else "failed"

    print("\n=== Fetch Summary ===")
    for label, status in results.items():
        print(f"- {label}: {status}")
    if any(s == "failed" for s in results.values()):
        print("\nTip: rerun this script later; transient service errors often clear on retry.")
    print("\nNext: python3 scripts/diversify_formats.py")


if __name__ == "__main__":
    main()
