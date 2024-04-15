# main.py

import os
from datetime import datetime
import numpy as np
from osgeo import gdal, osr
from temperature_raster import write_temperature_raster
from landsat_utils import getLandsatL2_SST, parseMTL
from clipping import clip_raster

def main():
    # Define input paths
    pathfolder = r"your_path_to_Landsat_data_folder"
    shapefile_path = r"your_path_to_shapefile"

    # Retrieve Landsat temperature data
    dt, lat, lon, temperature, srs, geo_transform = getLandsatL2_SST(pathfolder)

    # Define output paths
    output_path = "output_temperature_raster.tif"
    clipped_output_path = "clipped_output_temperature_raster.tif"

    # Write temperature raster
    write_temperature_raster(output_path, temperature, geo_transform, srs)

    # Clip raster
    clip_raster(output_path, clipped_output_path, shapefile_path)

if __name__ == "__main__":
    main()
