#!/usr/bin/env bash
# ==============================================================================
# Phase 2 - Dataset Expansion & Diversification
# Version: 1.3.0 | Author: George Corea
# ==============================================================================

set -euo pipefail

cd /media/george-corea/GIS/Projects/QGIS_PortalCrafter/input

# Define bounding box for extraction (Sydney/Newcastle region)
BBOX="151.7,-32.9,151.8,-32.8"

# Existing directories
mkdir -p ./environmental/biodiversity_values/current
mkdir -p ./environmental/biodiversity_values/offset_scheme
mkdir -p ./environmental/growth_centres
mkdir -p ./environmental/wetlands
mkdir -p ./environmental/koala_habitat
mkdir -p ./administrative/native_title
mkdir -p ./administrative/local_gov
mkdir -p ./administrative/state_forests
mkdir -p ./administrative/land_districts
mkdir -p ./administrative/parishes
mkdir -p ./administrative/counties
mkdir -p ./infrastructure/power
mkdir -p ./infrastructure/transport/railways
mkdir -p ./infrastructure/transport/roads
mkdir -p ./infrastructure/transport/facilities
mkdir -p ./environmental/biodiversity_value

# Data.gov dataset catalogue prefetch
DATA_GOV_CATALOG="https://data.gov.au/data/dataset/nsw-biodiversity-values-map"
curl -sS "$DATA_GOV_CATALOG" -o ./environmental/.datagov_biodiversity.html
echo "BV map catalogue prefetch: $DATA_GOV_CATALOG"
rm -f ./environmental/.datagov_biodiversity.html

# ==============================================================================
# GROUP A: STATUTORY BIODIVERSITY & LANDUSE (CPO CORE WORKFLOWS)
# ==============================================================================

# 1. Biodiversity Values Map (BV Map - Highlights high ecological sensitivity)
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/BVMap/BVMap_Current/MapServer/0/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/.bv_map_raw.geojson
ogr2ogr -f "GPKG" ./environmental/biodiversity_value/bv_map_current.gpkg ./environmental/.bv_map_raw.geojson
rm -f ./environmental/.bv_map_raw.geojson

# 2. State Environmental Planning Policy (SEPP) Strategic Growth Centres
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/GrowthCentres/MapServer/0/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/.growth_centres_raw.geojson
ogr2ogr -f "SQLite" -dsco SPATIALITE=YES ./environmental/growth_centres/growth_centres.sqlite ./environmental/.growth_centres_raw.geojson
rm -f ./environmental/.growth_centres_raw.geojson

# 3. Coastal Wetlands Boundaries (SEPP Resilience and Hazards mapping)
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/Protection/MapServer/1/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/.coastal_wetlands_raw.geojson
ogr2ogr -f "ESRI Shapefile" ./environmental/wetlands/coastal_wetlands.shp ./environmental/.coastal_wetlands_raw.geojson
rm -f ./environmental/.coastal_wetlands_raw.geojson

# 4. Littoral Rainforests Protective Limits
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/Protection/MapServer/2/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/.littoral_rainforests_raw.geojson
ogr2ogr -f "KML" ./environmental/littoral_rainforests.kml ./environmental/.littoral_rainforests_raw.geojson
rm -f ./environmental/.littoral_rainforests_raw.geojson

# 5. Core Koala Habitat Protection Zones
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/Protection/MapServer/11/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/.koala_habitat_raw.geojson
ogr2ogr -f "ESRI Shapefile" ./environmental/koala_habitat/koala_habitat_habitat.shp ./environmental/.koala_habitat_raw.geojson
rm -f ./environmental/.koala_habitat_raw.geojson

# ==============================================================================
# GROUP B: ADMINISTRATIVE BOUNDARIES & CONSTRAINTS
# ==============================================================================

# 6. Native Title Claims (Statutory legal boundary constraint check)
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/FeatureServer/6/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./administrative/.native_title_raw.geojson
ogr2ogr -f "GPKG" ./administrative/native_title/native_title.gpkg ./administrative/.native_title_raw.geojson
rm -f ./administrative/.native_title_raw.geojson

# 7. Local Government Areas (LGA Boundaries - Essential for local planning advice)
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer/8/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./administrative/.lga_boundaries_raw.geojson
ogr2ogr -f "SQLite" -dsco SPATIALITE=YES ./administrative/local_gov/lga_boundaries.sqlite ./administrative/.lga_boundaries_raw.geojson
rm -f ./administrative/.lga_boundaries_raw.geojson

# 8. State Forests Estate (Crown land usage boundaries)
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer/3/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./administrative/state_forests/state_forests.geojson
# Keep as plain GeoJSON format to satisfy multi-format testing variance

# ==============================================================================
# GROUP C: INFRASTRUCTURE & CRITICAL ASSETS
# ==============================================================================

# 9. Electricity Transmission Lines (Key overlay for renewable energy planning advice)
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Features_of_Interest_Category/FeatureServer/6/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./infrastructure/.transmission_lines_raw.geojson
ogr2ogr -f "ESRI Shapefile" ./infrastructure/power/transmission_lines.shp ./infrastructure/.transmission_lines_raw.geojson
rm -f ./infrastructure/.transmission_lines_raw.geojson

# 10. Railway Network Lines (Transport grid baseline verification)
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme/FeatureServer/6/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./infrastructure/.railways_raw.geojson
ogr2ogr -f "KML" ./infrastructure/railways.kml ./infrastructure/.railways_raw.geojson
rm -f ./infrastructure/.railways_raw.geojson

# ==============================================================================
# AUDIT VERIFICATION
# ==============================================================================
echo "=== Staging Phase 2 Data Footprint Audit ==="
find /media/george-corea/GIS/Projects/QGIS_PortalCrafter/input -maxdepth 4 -type f -printf '%p\t%s bytes\n' | sort
echo "=== DONE ==="
