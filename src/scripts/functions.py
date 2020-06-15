from rasterio import features as _features
from affine import Affine as _Affine
import numpy as _np
import xarray as _xr
import geopandas as _gpd

def transform_from_latlon(lat, lon):
    """ input 1D array of lat / lon and output an _Affine transformation
    """
    lat = _np.asarray(lat)
    lon = _np.asarray(lon)
    trans = _Affine.translation(lon[0], lat[0])
    scale = _Affine.scale(lon[1] - lon[0], lat[1] - lat[0])
    return trans * scale



def rasterize(shapes, coords, latitude='latitude', longitude='longitude',
              fill=_np.nan, **kwargs):
    """Rasterize a list of (geometry, fill_value) tuples onto the given
    xray coordinates. This only works for 1d latitude and longitude
    arrays.

    usage:
    -----
    1. read shapefile to geopandas.GeoDataFrame
          `states = gpd.read_file(shp_dir+shp_file)`
    2. encode the different shapefiles that capture those lat-lons as different
        numbers i.e. 0.0, 1.0 ... and otherwise _np.nan
          `shapes = (zip(states.geometry, range(len(states))))`
    3. Assign this to a new coord in your original xarray.DataArray
          `ds['states'] = rasterize(shapes, ds.coords, longitude='X', latitude='Y')`

    arguments:
    ---------
    : **kwargs (dict): passed to `rasterio.rasterize` function

    attrs:
    -----
    :transform (_Affine._Affine): how to translate from latlon to ...?
    :raster (numpy.ndarray): use rasterio._features.rasterize fill the values
      outside the .shp file with _np.nan
    :spatial_coords (dict): dictionary of {"X":_xr.DataArray, "Y":_xr.DataArray()}
      with "X", "Y" as keys, and _xr.DataArray as values

    returns:
    -------
    :(_xr.DataArray): DataArray with `values` of nan for points outside shapefile
      and coords `Y` = latitude, 'X' = longitude.


    """
    transform = transform_from_latlon(coords[latitude], coords[longitude])
    out_shape = (len(coords[latitude]), len(coords[longitude]))
    raster = _features.rasterize(shapes, out_shape=out_shape,
                                fill=fill, transform=transform,
                                dtype=float, **kwargs)
    spatial_coords = {latitude: coords[latitude], longitude: coords[longitude]}
    return _xr.DataArray(raster, coords=spatial_coords, dims=(latitude, longitude))

def add_shape_coord_from_data_array(xr_da, shp_path, coord_name):
    """ Create a new coord for the xr_da indicating whether or not it 
         is inside the shapefile

        Creates a new coord - "coord_name" which will have integer values
         used to subset xr_da for plotting / analysis/

        Usage:
        -----
        precip_da = add_shape_coord_from_data_array(precip_da, "awash.shp", "awash")
        awash_da = precip_da.where(precip_da.awash==0, other=_np.nan) 
    """
    # 1. read in shapefile
    shp_gpd = _gpd.read_file(shp_path)

    # 2. create a list of tuples (shapely.geometry, id)
    #    this allows for many different polygons within a .shp file (e.g. States of US)
    shapes = [(shape, n) for n, shape in enumerate(shp_gpd.geometry)]

    # 3. create a new coord in the xr_da which will be set to the id in `shapes`
    xr_da[coord_name] = rasterize(shapes, xr_da.coords, 
                               longitude='longitude', latitude='latitude')

    return xr_da