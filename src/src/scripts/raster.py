import numpy as _np
import osr as _osr
import gdal as _gdal

def array2raster(newRasterfn, rasterOrigin, pixelWidth, pixelHeight, array, EPSG = 4326):

    cols = array.shape[1]
    rows = array.shape[0]
    originX = rasterOrigin[0] - pixelWidth / 2.
    originY = rasterOrigin[1] + pixelHeight / 2.

    driver = _gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, _gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, -pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.SetNoDataValue(-9999)
    outband.WriteArray(array)
    outRasterSRS = _osr.SpatialReference()
    outRasterSRS.ImportFromEPSG(EPSG)
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

