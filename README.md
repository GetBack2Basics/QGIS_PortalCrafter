# QGIS PortalCrafter CPO
QGIS 4.x plugin for Conservation Planning & Offsets portal staging.

## Layout
- `input/` — static datasets (GeoPackage, SpatiaLite, GeoJSON, Shapefile, KML, GeoTIFF)
- `src/data/config_schema.py` — frozen dataclass schema for `portal_config.yaml`
- `src/services/config_parser.py` — PyYAML read/validate engine
- `src/services/layer_registry.py` — layer existence/schema verification
- `startup.py` — QGIS plugin entry point

## Data inputs
Cadastre: `input/cadastre/nsw_parcels_staging.gpkg`
Roads: `input/roads/nsw_roads_staging.sqlite`
Heritage: `input/heritage/state_heritage_register.geojson`
Biodiversity: `input/heritage/epi_terrestrial_biodiversity/*.shp`
Corridors: `input/heritage/regional_biodiversity_corridors.kml`
Rasters: `input/raster/*.tif`

## Usage
Load the plugin in QGIS 4.x. It reads `portal_config.yaml`, validates paths,
and registers configured layers through the OGR/GDAL provider abstractions.

## Notes
- `input/` is gitignored by design.
- Qt 6 qualified enums are used throughout.
- Version targeting: `qgisMaximumVersion=4.99`.
