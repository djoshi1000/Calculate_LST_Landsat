# landsat_utils.py

import os
import numpy as np
from osgeo import gdal, osr

def getLandsatL2_SST(pathfolder):
    # List files in directory
    filename = os.path.basename(pathfolder)
    foo = [os.path.join(pathfolder, name) for name in os.listdir(pathfolder) if "_L2" in name]
    
    # Read MTL file
    MTLfile = None
    for f in foo:
        if "_MTL.txt" in f:
            with open(f, 'r') as file:
                MTLfile = file.read()
                break
    if MTLfile is None:
        raise ValueError("MTL file not found in the specified folder")
    
    # Get variables from MTL files
    spacecraft = parseMTL(MTLfile, 'SPACECRAFT_ID =')
    
    # Set thermal band by spacecraft
    if spacecraft in ['LANDSAT_4', 'LANDSAT_5', 'LANDSAT_7']:
        STBAND = '6'
    elif spacecraft in ['LANDSAT_8', 'LANDSAT_9']:
        STBAND = '10'
    else:
        raise ValueError("Spacecraft {} not known".format(spacecraft))
    
    # Get calibration slope and intercept
    slope = parseMTL(MTLfile, 'TEMPERATURE_MULT_BAND_ST_B' + STBAND + ' =')
    intercept = parseMTL(MTLfile, 'TEMPERATURE_ADD_BAND_ST_B' + STBAND + ' =')
    
    # Extract date time
    date = parseMTL(MTLfile, 'DATE_ACQUIRED =')
    time = parseMTL(MTLfile, 'SCENE_CENTER_TIME =')
#     dt = datetime.strptime(date + ' ' + time, '%Y-%m-%d %H:%M:%S.%fZ')
    dt = datetime.strptime(date + ' ' + time.split('.')[0], '%Y-%m-%d %H:%M:%S')

    
    # Get thermal band data
    print('Loading thermal band from {} ... '.format(filename), end='')
    sst_band = [f for f in foo if '_ST_B' + STBAND + '.TIF' in f][0]
    temp_ds = gdal.Open(sst_band)
    temp = temp_ds.ReadAsArray().astype(float)
    temperature = temp * slope + intercept - 273.15
    print('Done')
    
    # Get image lat/lon
    print('Recovering latitude and longitude from {} ... '.format(filename), end='')
    geo_info = temp_ds.GetGeoTransform()
    img_width = temp_ds.RasterXSize
    img_height = temp_ds.RasterYSize
    x, y = np.meshgrid(np.arange(0, img_width), np.arange(0, img_height))
    lon = geo_info[0] + geo_info[1] * x + geo_info[2] * y
    lat = geo_info[3] + geo_info[4] * x + geo_info[5] * y
    print('Done')
       
    # Remove aberrant data
    temperature[temperature < -60] = np.nan
    
    # Remove data out of predefined percentiles
    # prct = np.percentile(temperature[~np.isnan(temperature)], prc_lim)
    # print('{:.2f}% pixel deleted from {}: out of [{:.1f} {:.1f}] percentiles'.format(
    #     np.sum(np.isnan(temperature)) / np.prod(temperature.shape) * 100, filename, prc_lim[0], prc_lim[1]))
    # temperature[(temperature < prct[0]) | (temperature > prct[1])] = np.nan
    # Get spatial reference system
    
    srs = osr.SpatialReference()
    srs.ImportFromWkt(temp_ds.GetProjection())
    
    return dt, lat, lon, temperature, srs, geo_info

def parseMTL(MTLfile, toparse):
    # Parse MTL file
    parsed_parameters = []
    lines = MTLfile.split('\n')
    for line in lines:
        if toparse in line:
            parsed_parameters.append(line.split('=')[1].strip().replace('"', ''))
            try:
                foo = float(parsed_parameters[-1])
                parsed_parameters[-1] = foo
            except ValueError:
                pass
    if len(parsed_parameters) == 1:
        return parsed_parameters[0]
    else:
        return parsed_parameters
    
