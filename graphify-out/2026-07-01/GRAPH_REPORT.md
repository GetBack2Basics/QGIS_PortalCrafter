# Graph Report - /media/george-corea/GIS/Projects/QGIS_PortalCrafter  (2026-07-01)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 102 nodes · 215 edges · 14 communities (12 shown, 2 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.57)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5353c6b4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]

## God Nodes (most connected - your core abstractions)
1. `PortalConfig` - 22 edges
2. `LayerRegistry` - 20 edges
3. `PortalConfigParser` - 17 edges
4. `MenuItem` - 15 edges
5. `PortalCrafterPlugin` - 13 edges
6. `PortalSearchDock` - 11 edges
7. `PortalMenuFactory` - 10 edges
8. `PortalUICleaner` - 9 edges
9. `main()` - 9 edges
10. `_parse_menus()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Layer Registry Verifier` --references--> `NSW Parcels Staging (GPKG)`  [INFERRED]
  src/services/layer_registry.py → input/cadastre/nsw_parcels_staging.gpkg
- `PortalCrafterPlugin` --uses--> `PortalMenuFactory`  [INFERRED]
  startup.py → src/components/menu_factory.py
- `PortalCrafterPlugin` --uses--> `PortalSearchDock`  [INFERRED]
  startup.py → src/components/search_dock.py
- `PortalCrafterPlugin` --uses--> `PortalConfigParser`  [INFERRED]
  startup.py → src/services/config_parser.py
- `PortalCrafterPlugin` --uses--> `LayerRegistry`  [INFERRED]
  startup.py → src/services/layer_registry.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Configuration-Driven Layer Loading** — portal_config, src_services_config_parser_engine, src_services_layer_registry_verifier, startup_plugin_entry [EXTRACTED 0.90]
- **Staging Data Inputs** — input_cadastre_gpkg, input_roads_sqlite, input_heritage_geojson, input_heritage_shp, input_heritage_kml, input_raster_tif [EXTRACTED 1.00]

## Communities (14 total, 2 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.18
Nodes (5): classFactory(), QGIS PortalCrafter Initialization Engine, PortalUICleaner, PortalCrafterPlugin, run()

### Community 1 - "Community 1"
Cohesion: 0.24
Nodes (3): Path, MenuItem, LayerRegistry

### Community 2 - "Community 2"
Cohesion: 0.30
Nodes (10): Any, ConnectionInfo, CustomSearch, Menu, SubMenu, _map_raw_to_schema(), _parse_custom_searches(), _parse_menus() (+2 more)

### Community 3 - "Community 3"
Cohesion: 0.20
Nodes (10): NSW Parcels Staging (GPKG), State Heritage Register (GeoJSON), Regional Biodiversity Corridors (KML), Terrestrial Biodiversity (SHP), NSW Regional 10m Terrain (GeoTIFF), NSW Roads Staging (SpatiaLite), Config Schema Dataclass, Config Parser Engine (+2 more)

### Community 4 - "Community 4"
Cohesion: 0.47
Nodes (11): PortalConfig, _build_registry_summary(), _clear_report(), _iter_items(), _log(), main(), validate_config_parsing(), validate_file_completeness() (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (3): QDockWidget, QTableWidgetItem, PortalSearchDock

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (5): LANG, LANGUAGE, LC_ALL, QT_TRANSLATE_NOOP, launch-qgis-portal.sh script

## Knowledge Gaps
- **10 isolated node(s):** `launch-qgis-portal.sh script`, `LANGUAGE`, `LC_ALL`, `LANG`, `QT_TRANSLATE_NOOP` (+5 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PortalConfig` connect `Community 4` to `Community 0`, `Community 1`, `Community 2`, `Community 7`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Why does `PortalSearchDock` connect `Community 5` to `Community 0`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Why does `PortalCrafterPlugin` connect `Community 0` to `Community 1`, `Community 2`, `Community 5`, `Community 7`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `PortalConfig` (e.g. with `PortalMenuFactory` and `PortalConfigParser`) actually correct?**
  _`PortalConfig` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `LayerRegistry` (e.g. with `PortalMenuFactory` and `MenuItem`) actually correct?**
  _`LayerRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PortalConfigParser` (e.g. with `ConnectionInfo` and `CustomSearch`) actually correct?**
  _`PortalConfigParser` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `MenuItem` (e.g. with `PortalConfigParser` and `LayerRegistry`) actually correct?**
  _`MenuItem` has 2 INFERRED edges - model-reasoned connections that need verification._