set -euo pipefail

cd /media/george-corea/GIS/Projects/QGIS_PortalCrafter/input

mkdir -p ./environmental/biodiversity_value
mkdir -p ./environmental/growth_centres
mkdir -p ./environmental/wetlands
mkdir -p ./environmental/koala_habitat
mkdir -p ./administrative/native_title
mkdir -p ./administrative/local_gov
mkdir -p ./infrastructure/power

# GROUP A

# 1
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/BVMap/BVMap_Current/MapServer/0/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/bv_map.geojson
ogr2ogr -f "GPKG" ./environmental/bv_map.gpkg ./environmental/bv_map.geojson
rm -f ./environmental/bv_map.geojson

# 2
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/GrowthCentres/MapServer/0/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/growth_centres.geojson
ogr2ogr -f "SQLite" -dsco SPATIALITE=YES ./environmental/growth_centres.sqlite ./environmental/growth_centres.geojson
rm -f ./environmental/growth_centres.geojson

# 3
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/Protection/MapServer/1/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/coastal_wetlands.geojson
ogr2ogr -f "ESRI Shapefile" ./environmental/wetlands/coastal_wetlands.shp ./environmental/coastal_wetlands.geojson
rm -f ./environmental/coastal_wetlands.geojson

# 4
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/Protection/MapServer/2/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/littoral_rainforests.geojson
ogr2ogr -f "KML" ./environmental/littoral_rainforests.kml ./environmental/littoral_rainforests.geojson
rm -f ./environmental/littoral_rainforests.geojson

# 5
curl -s "https://mapprod3.environment.nsw.gov.au/arcgis/rest/services/Planning/Protection/MapServer/11/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./environmental/koala_habitat.geojson
ogr2ogr -f "ESRI Shapefile" ./environmental/koala_habitat/koala_habitat.shp ./environmental/koala_habitat.geojson
rm -f ./environmental/koala_habitat.geojson

# GROUP B

# 6
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer/2/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./administrative/native_title_claims.geojson
ogr2ogr -f "GPKG" ./administrative/native_title_claims.gpkg ./administrative/native_title_claims.geojson
rm -f ./administrative/native_title_claims.geojson

# 7
curl -s "https://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Administrative_Boundaries/MapServer/3/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./administrative/lga_boundaries.geojson
ogr2ogr -f "SQLite" -dsco SPATIALITE=YES ./administrative/local_gov/lga_boundaries.sqlite ./administrative/lga_boundaries.geojson
rm -f ./administrative/lga_boundaries.geojson

# 8
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Administrative_Boundaries_Theme/FeatureServer/4/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./administrative/state_forests.geojson

# GROUP C

# 9
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Utilities_Theme/FeatureServer/1/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./infrastructure/transmission_lines.geojson
ogr2ogr -f "ESRI Shapefile" ./infrastructure/power/transmission_lines.shp ./infrastructure/transmission_lines.geojson
rm -f ./infrastructure/transmission_lines.geojson

# 10
curl -s "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Transport_Theme/FeatureServer/2/query?where=1%3D1&geometry=151.7,-32.9,151.8,-32.8&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&returnGeometry=true&f=geojson" -o ./infrastructure/railways.geojson
ogr2ogr -f "KML" ./infrastructure/railways.kml ./infrastructure/railways.geojson
rm -f ./infrastructure/railways.geojson

echo "=== Staging Phase 2 Data Footprint Audit ==="
find . -maxdepth 4 -type f -printf '%p\t%s bytes\n' | sort
echo "=== DONE ==="
