"""Staged NSW spatial acquisition targets.

Populate verified URLs and intent/scan results here.
This is a source-of-truth listing for the NSW statewide
spatial file staging task.
"""

OBJ = {
  "task": "Stage NSW statewide spatial files into local QGIS project input",
  "project": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter",
  "product": None,
  "root": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input",
  "mode": "cache-check-first",
  "intent": "directory",
  "verified_url": None,
  "write_path": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/retrieval_cache.dat-manager/products",

  "targets": {
    "cadastre": {
      "source": "NSW Spatial Services / Data.NSW",
      "dataset": "NSW Land Parcel and Property Theme - GDA2020",
      "dataset_page": "https://data.nsw.gov.au/data/dataset/1-079705a7798742e6b13b6da2171e5991",
      "service": "https://portal.spatial.nsw.gov.au/server/rest/services/NSW_Land_Parcel_Property_Theme_multiCRS/FeatureServer",
      "verified_url": None,
      "local_dir": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/cadastre",
      "status": "pending-verification"
    },
    "roads": {
      "source": "NSW Spatial Services / Data.NSW",
      "dataset": "NSW Road Centreline / Road network",
      "dataset_page": "https://data.nsw.gov.au/data/dataset/?tags=Cadastre",
      "verified_url": None,
      "local_dir": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/roads",
      "status": "pending-verification"
    },
    "raster": {
      "source": "OSGeo GeoTiff samples",
      "dataset": "Regional orthophoto sample",
      "verified_url": "https://download.osgeo.org/geotiff/samples/spot/otb_spotsam.tif",
      "local_dir": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/raster",
      "local_file": "/media/george-corea/GIS/Projects/QGIS_PortalCrafter/input/raster/regional_ortho.tif",
      "status": "pending-download"
    }
  },

  "next_steps": [
    "Resolve non-binary staging for NSW cadastre/roads URLs before applying 302 redirect rules.",
    "Keep created files in input. Do not delete until extraction succeeds."
  ]
}
