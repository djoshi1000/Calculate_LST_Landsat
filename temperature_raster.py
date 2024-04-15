# temperature_raster.py

import os
from osgeo import gdal, osr

def write_temperature_raster(output_path, temperature, geo_transform, srs):
    driver = gdal.GetDriverByName('GTiff')
    output_ds = driver.Create(output_path, temperature.shape[1], temperature.shape[0], 1, gdal.GDT_Float32)
    output_ds.SetProjection(srs.ExportToWkt())
    output_ds.SetGeoTransform(geo_transform)
    output_band = output_ds.GetRasterBand(1)
    output_band.WriteArray(temperature)
    output_ds = None
