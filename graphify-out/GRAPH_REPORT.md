# Graph Report - QGIS_PortalCrafter  (2026-07-02)

## Corpus Check
- 19 files · ~3,545 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 137 nodes · 312 edges · 16 communities (15 shown, 1 thin omitted)
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 87 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a95a6a3e`
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
- [[_COMMUNITY_Community 10|Community 10]]

## God Nodes (most connected - your core abstractions)
1. `PortalConfig` - 25 edges
2. `LayerRegistry` - 23 edges
3. `MenuItem` - 22 edges
4. `PortalCrafterPlugin` - 19 edges
5. `Menu` - 18 edges
6. `PortalConfigParser` - 18 edges
7. `PortalMenuFactory` - 13 edges
8. `PortalConfig` - 13 edges
9. `ConnectionInfo` - 12 edges
10. `SubMenu` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Layer Registry Verifier` --references--> `NSW Parcels Staging (GPKG)`  [INFERRED]
  src/services/layer_registry.py → input/cadastre/nsw_parcels_staging.gpkg
- `PortalCrafterPlugin` --uses--> `PortalMenuFactory`  [INFERRED]
  startup.py → src/components/menu_factory.py
- `PortalCrafterPlugin` --uses--> `PortalSearchDock`  [INFERRED]
  startup.py → src/components/search_dock.py
- `PortalConfig` --uses--> `ConnectionInfo`  [INFERRED]
  tests/test_portal_bootstrap.py → src/data/config_schema.py
- `PortalConfig` --uses--> `MenuItem`  [INFERRED]
  tests/test_portal_bootstrap.py → src/data/config_schema.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Configuration-Driven Layer Loading** — portal_config, src_services_config_parser_engine, src_services_layer_registry_verifier, startup_plugin_entry [EXTRACTED 0.90]
- **Staging Data Inputs** — input_cadastre_gpkg, input_roads_sqlite, input_heritage_geojson, input_heritage_shp, input_heritage_kml, input_raster_tif [EXTRACTED 1.00]

## Communities (16 total, 1 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.12
Nodes (8): PortalStartupSelector, classFactory(), QGIS PortalCrafter Initialization Engine, QDialog, PortalUICleaner, PortalConfig, PortalCrafterPlugin, run()

### Community 1 - "Community 1"
Cohesion: 0.30
Nodes (3): LayerRegistry, MenuItem, PortalConfig

### Community 2 - "Community 2"
Cohesion: 0.23
Nodes (19): Any, CustomSearch, ConnectionInfo, CustomSearch, Menu, MenuItem, PortalConfig, SubMenu (+11 more)

### Community 3 - "Community 3"
Cohesion: 0.13
Nodes (15): NSW Parcels Staging (GPKG), State Heritage Register (GeoJSON), Regional Biodiversity Corridors (KML), Terrestrial Biodiversity (SHP), NSW Regional 10m Terrain (GeoTIFF), NSW Roads Staging (SpatiaLite), Data inputs, Layout (+7 more)

### Community 4 - "Community 4"
Cohesion: 0.45
Nodes (11): _build_registry_summary(), _clear_report(), _iter_items(), _log(), main(), PortalConfig, validate_config_parsing(), validate_file_completeness() (+3 more)

### Community 5 - "Community 5"
Cohesion: 0.29
Nodes (3): PortalSearchDock, QDockWidget, QTableWidgetItem

### Community 6 - "Community 6"
Cohesion: 0.33
Nodes (5): LANG, LANGUAGE, LC_ALL, QT_TRANSLATE_NOOP, launch-qgis-portal.sh script

### Community 7 - "Community 7"
Cohesion: 0.46
Nodes (3): DeploymentCleanup, Remove runtime artifacts left after plugin updates.      Strict scope:     - tar, Path

### Community 10 - "Community 10"
Cohesion: 0.52
Nodes (3): PortalMenuFactory, QAction, MenuItem

## Knowledge Gaps
- **15 isolated node(s):** `launch-qgis-portal.sh script`, `LANGUAGE`, `LC_ALL`, `LANG`, `QT_TRANSLATE_NOOP` (+10 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PortalCrafterPlugin` connect `Community 0` to `Community 1`, `Community 2`, `Community 5`, `Community 7`, `Community 10`?**
  _High betweenness centrality (0.194) - this node is a cross-community bridge._
- **Why does `PortalConfigParser` connect `Community 2` to `Community 0`, `Community 4`?**
  _High betweenness centrality (0.147) - this node is a cross-community bridge._
- **Why does `LayerRegistry` connect `Community 1` to `Community 0`, `Community 2`, `Community 10`?**
  _High betweenness centrality (0.133) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `PortalConfig` (e.g. with `Any` and `PortalMenuFactory`) actually correct?**
  _`PortalConfig` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `LayerRegistry` (e.g. with `PortalMenuFactory` and `LayerRegistry`) actually correct?**
  _`LayerRegistry` has 8 INFERRED edges - model-reasoned connections that need verification._
- **Are the 16 inferred relationships involving `MenuItem` (e.g. with `Any` and `PortalMenuFactory`) actually correct?**
  _`MenuItem` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `PortalCrafterPlugin` (e.g. with `PortalMenuFactory` and `PortalSearchDock`) actually correct?**
  _`PortalCrafterPlugin` has 7 INFERRED edges - model-reasoned connections that need verification._