#######################################################
# Everything to do with the grid
#######################################################

import numpy as np

from io import read_netcdf
from utils import fix_lon_range
import constants as const


# Given a 3D hfac array on any grid, create the land mask.
def build_land_mask (hfac):

    return np.sum(hfac, axis=0)==0


# Given a 3D hfac array on any grid, create the ice shelf mask.
def build_zice_mask (hfac):

    return (np.sum(hfac, axis=0)!=0)*(hfac[0,:]==0)


# Create a mask just containing FRIS ice shelf points.
# Arguments:
# zice_mask, lon, lat: 2D arrays of the ice shelf mask, longitude, and latitude on any grid
def build_fris_mask (zice_mask, lon, lat):

    fris_mask = np.zeros(zice_mask.shape, dtype='bool')
    # Identify FRIS in two parts, split along the line 45W
    # Each set of 4 bounds is in form [lon_min, lon_max, lat_min, lat_max]
    regions = [[const.fris_bounds[0], -45, const.fris_bounds[2], -74.7], [-45, const.fris_bounds[1], const.fris_bounds[2], -77.85]]
    for bounds in regions:
        # Select the ice shelf points within these bounds
        index = np.nonzero(zice_mask*(lon >= bounds[0])*(lon <= bounds[1])*(lat >= bounds[2])*(lat <= bounds[3]))
        fris_mask[index] = True
    return fris_mask


# Grid object containing lots of grid variables.
class Grid:

    # Initialisation arguments:
    # file_path: path to NetCDF grid file    
    def __init__ (self, file_path):

        # 1D lon and lat axes on regular grids
        # Make sure longitude is between -180 and 180
        # Cell centres
        self.lon_1d = fix_lon_range(read_netcdf(file_path, 'X'))
        self.lat_1d = read_netcdf(file_path, 'Y')
        # Cell corners (southwest)
        self.lon_corners_1d = fix_lon_range(read_netcdf(file_path, 'Xp1'))
        self.lat_corners_1d = read_netcdf(file_path, 'Yp1')

        # 2D lon and lat fields on any grid
        # Cell centres
        self.lon_2d = fix_lon_range(read_netcdf(file_path, 'XC'))
        self.lat_2d = read_netcdf(file_path, 'YC')
        # Cell corners
        self.lon_corners_2d = fix_lon_range(read_netcdf(file_path, 'XG'))
        self.lat_corners_2d = read_netcdf(file_path, 'YG')

        # 2D integrands of distance
        # Across faces
        self.dx = read_netcdf(file_path, 'dxF')
        self.dy = read_netcdf(file_path, 'dyF')
        # Between centres
        self.dx_t = read_netcdf(file_path, 'dxC')
        self.dy_t = read_netcdf(file_path, 'dyC')
        # Between u-points
        self.dx_u = self.dx  # Equivalent to distance across face
        self.dy_u = read_netcdf(file_path, 'dyU')
        # Between v-points
        self.dx_v = read_netcdf(file_path, 'dxV')
        self.dy_v = self.dy  # Equivalent to distance across face
        # Between corners
        self.dx_psi = read_netcdf(file_path, 'dxG')
        self.dy_psi = read_netcdf(file_path, 'dyG')

        # 2D integrands of area
        # Area of faces
        self.dA = read_netcdf(file_path, 'rA')
        # Centered on u-points
        self.dA_u = read_netcdf(file_path, 'rAw')
        # Centered on v-points
        self.dA_v = read_netcdf(file_path, 'rAs')
        # Centered on corners
        self.dA_psi = read_netcdf(file_path, 'rAz')

        # Vertical grid
        # Assumes we're in the ocean so using z-levels - not sure how this
        # would handle atmospheric pressure levels.
        # Depth axis at centres of z-levels
        self.z = read_netcdf(file_path, 'Z')
        # Depth axis at edges of z-levels
        self.z_edges = read_netcdf(file_path, 'Zp1')
        # Depth axis at w-points
        self.z_w = read_netcdf(file_path, 'Zl')

        # Vertical integrands of distance
        # Across cells
        self.dz = read_netcdf(file_path, 'drF')
        # Between centres
        self.dz_t = read_netcdf(file_path, 'drC')

        # Dimension lengths (on tracer grid)
        self.nx = self.lon_1d.size
        self.ny = self.lat_1d.size
        self.nz = self.z.size

        # Partial cell fractions
        # At centres
        self.hfac = read_netcdf(file_path, 'HFacC')
        # At u-points
        self.hfac_u = read_netcdf(file_path, 'HFacW')
        # At v-points
        self.hfac_v = read_netcdf(file_path, 'HFacS')

        # Create masks on the t, u, and v grids
        # We can't do the psi grid because there is no hfac there
        # Land masks
        self.land_mask = build_land_mask(self.hfac)
        self.land_mask_u = build_land_mask(self.hfac_u)
        self.land_mask_v = build_land_mask(self.hfac_v)
        # Ice shelf masks
        self.zice_mask = build_zice_mask(self.hfac)
        self.zice_mask_u = build_zice_mask(self.hfac_u)
        self.zice_mask_v = build_zice_mask(self.hfac_v)
        # FRIS masks
        self.fris_mask = build_fris_mask(self.zice_mask, self.lon_2d, self.lat_2d)
        self.fris_mask_u = build_fris_mask(self.zice_mask_u, self.lon_corners_2d, self.lat_2d)
        self.fris_mask_v = build_fris_mask(self.zice_mask_v, self.lon_2d, self.lat_corners_2d)

        # Topography
        # Bathymetry (bottom depth)
        self.bathy = read_netcdf(file_path, 'R_low')
        # Ice shelf draft (surface depth, enforce 0 in land or open-ocean points)
        self.zice = read_netcdf(file_path, 'Ro_surf')
        self.zice[np.invert(self.zice_mask)] = 0
        # Water column thickness
        self.wct = read_netcdf(file_path, 'Depth')        

        # Apply land mask to the topography
        self.bathy = np.ma.masked_where(self.land_mask, self.bathy)
        self.zice = np.ma.masked_where(self.land_mask, self.zice)
        self.wct = np.ma.masked_where(self.land_mask, self.wct)

        
    # Return the longitude and latitude arrays for the given grid type.
    # 't' (default), 'u', 'v', 'psi', and 'w' are all supported.
    def get_lon_lat (self, gtype='t'):

        if gtype in ['t', 'w']:
            return self.lon_2d, self.lat_2d
        elif gtype == 'u':
            return self.lon_corners_2d, self.lat_2d
        elif gtype == 'v':
            return self.lon_2d, self.lat_corners_2d
        elif gtype == 'psi':
            return self.lon_corners_2d, self_lat_corners_2d
        else:
            print 'Error (get_lon_lat): invalid gtype ' + gtype


    # Return the hfac array for the given grid type.
    # 'psi' and 'w' have no hfac arrays so they are not supported
    def get_hfac (self, gtype='t'):

        if gtype == 't':
            return self.hfac
        elif gtype == 'u':
            return self.hfac_u
        elif gtype == 'v':
            return self.hfac_v
        else:
            print 'Error (get_hfac): no hfac exists for the ' + gtype + ' grid'


    # Return the land mask for the given grid type.
    def get_land_mask (self, gtype='t'):

        if gtype == 't':
            return self.land_mask
        elif gtype == 'u':
            return self.land_mask_u
        elif gtype == 'v':
            return self.land_mask_v
        else:
            print 'Error (get_land_mask): no mask exists for the ' + gtype + ' grid'

            
    # Return the ice shelf mask for the given grid type.
    def get_zice_mask (self, gtype='t'):

        if gtype == 't':
            return self.zice_mask
        elif gtype == 'u':
            return self.zice_mask_u
        elif gtype == 'v':
            return self.zice_mask_v
        else:
            print 'Error (get_zice_mask): no mask exists for the ' + gtype + ' grid'


    # Return the FRIS mask for the given grid type.
    def get_fris_mask (self, gtype='t'):

        if gtype == 't':
            return self.fris_mask
        elif gtype == 'u':
            return self.fris_mask_u
        elif gtype == 'v':
            return self.fris_mask_v
        else:
            print 'Error (get_fris_mask): no mask exists for the ' + gtype + ' grid'
