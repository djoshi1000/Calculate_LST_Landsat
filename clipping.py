# clipping.py

import os
from osgeo import gdal, gdalconst

def clip_raster(input_raster_path, output_raster_path, shapefile_path):
    try:
        input_raster_dataset = gdal.Open(input_raster_path, gdalconst.GA_ReadOnly)
        if input_raster_dataset is None:
            raise RuntimeError("Unable to open input raster dataset")

        # Get the nodata value of the input raster
        nodata_value = input_raster_dataset.GetRasterBand(1).GetNoDataValue()
        
        # Open the shapefile dataset
        shapefile_dataset = gdal.OpenEx(shapefile_path, gdal.OF_VECTOR)
        if shapefile_dataset is None:
            raise RuntimeError("Unable to open shapefile dataset")

        # Set the warp options
        warp_options = gdal.WarpOptions(cutlineDSName=shapefile_path, 
                                         cropToCutline=True, 
                                         srcNodata=nodata_value,
                                         setColorInterpretation=True,
                                         dstAlpha=True, 
                                         format='GTiff',
                                         dstNodata=0)  # Set the nodata value for the output raster
        
        # Perform the warp operation (clip the raster)
        gdal.Warp(output_raster_path, input_raster_dataset, options=warp_options)

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        # Close datasets to release resources
        if input_raster_dataset:
            input_raster_dataset = None
        if shapefile_dataset:
            shapefile_dataset = None
