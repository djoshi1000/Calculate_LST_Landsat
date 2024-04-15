import os
from datetime import datetime
import numpy as np
from osgeo import gdal, osr

def write_temperature_raster(output_path, temperature, lat, lon, geo_transform, srs):
    # Create the output GeoTIFF file
    driver = gdal.GetDriverByName('GTiff')
    output_ds = driver.Create(output_path, temperature.shape[1], temperature.shape[0], 1, gdal.GDT_Float32)
    
    # Set the spatial reference system
    output_ds.SetProjection(srs.ExportToWkt())
    
    # Set the geotransform
    output_ds.SetGeoTransform(geo_transform)
    
    # Write the temperature data to the raster band
    output_band = output_ds.GetRasterBand(1)
    output_band.WriteArray(temperature)
    
    # Close the dataset
    output_ds = None

def getLandsatL2_SST(pathfolder): #, prc_lim=[2.5, 99]):
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
    

# Define the path to the folder containing Landsat data
pathfolder = r"C:\Users\dpj20001\OneDrive - University of Connecticut\Susanna\LC09_L2SP_013031_20240312_20240313_02_T1"
# retrieve_land = True  # Set to True if you want to retrieve land temperatures
# prc_lim = [2.5, 99]  # Set your desired percentile limits

# Retrieve temperature data, date, latitude, longitude, spatial reference system, and geotransform
dt, lat, lon, temperature, srs, geo_transform = getLandsatL2_SST(pathfolder)#, prc_lim)



# List all files in the directory
files = [name for name in os.listdir(pathfolder) if "_L2" in name]

# Get the base filename of the first Landsat image
if files:
    # Remove the "_ANG" suffix from the filename
    filename_with_suffix = os.path.basename(files[0]).split('.')[0]
    filename_without_suffix = filename_with_suffix.rsplit("_ANG", 1)[0]
    print("Base filename:", filename_without_suffix)
else:
    print("No Landsat images found in the directory.")
# Define the output path for the temperature raster
output_path = f"C:/Users/dpj20001/OneDrive - University of Connecticut/Susanna/output/{filename_without_suffix}_LST.tif"

# Write temperature raster with all coordinate systems preserved
write_temperature_raster(output_path, temperature, lat, lon, geo_transform, srs)

# Input raster file path
input_raster_path = output_path  # Replace "your_input_raster.tif" with the path to your input raster

# Output raster file path
output_raster_path = f"C:/Users/dpj20001/OneDrive - University of Connecticut/Susanna/output/{filename_without_suffix}_LST_clipped1.tif"

# Polygon shapefile path for clipping
shapefile_path = r"C:\Users\dpj20001\OneDrive - University of Connecticut\Susanna\County_new_haven\New_haven.shp"

# Open the input raster dataset
input_raster_dataset = gdal.Open(input_raster_path, gdalconst.GA_ReadOnly)
feature_id = 1
# Open the shapefile dataset
shapefile_dataset = gdal.OpenEx(shapefile_path, gdal.OF_VECTOR)
# Get the nodata value of the input raster
nodata_value = input_raster_dataset.GetRasterBand(1).GetNoDataValue()

# Set the warp options
warp_options = gdal.WarpOptions(cutlineDSName=shapefile_path, 
                                # cutlineLayer='polygon',
                                 #cutlineWhere=f"FID={feature_id}",  # Specify the feature ID for clipping
                                 cropToCutline=True, 
                                 srcNodata=True,
                                 setColorInterpretation= True,
                                 dstAlpha=True, 
                                 format='GTiff',
                                 dstNodata=0)  # Set the nodata value for the output raster

# Perform the warp operation (clip the raster)
gdal.Warp(output_raster_path, input_raster_dataset, options=warp_options)

# Close the dataset
input_raster_dataset = None
