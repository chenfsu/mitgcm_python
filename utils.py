#######################################################
# Miscellaneous useful tools
#######################################################

import numpy as np
import sys

from constants import rho_fw, sec_per_year, fris_bounds, fris_bounds_pster, deg2rad, rEarth


# Given an array containing longitude, make sure it's in the range (max_lon-360, max_lon). Default is (-180, 180). If max_lon is None, nothing will be done to the array.
def fix_lon_range (lon, max_lon=180):

    if max_lon is not None:
        index = lon >= max_lon
        lon[index] = lon[index] - 360
        index = lon < max_lon-360
        lon[index] = lon[index] + 360
    return lon


# Convert freshwater flux into the ice shelf (diagnostic SHIfwFlx) (kg/m^2/s, positive means freezing) to ice shelf melt rate (m/y, positive means melting).
def convert_ismr (shifwflx):

    return -shifwflx/rho_fw*sec_per_year


# Tile a 2D (lat x lon) array in depth so it is 3D (depth x lat x lon).
# grid can either be a Grid object or an array of grid dimensions [nx, ny, nz].
def xy_to_xyz (data, grid):

    if isinstance(grid, list):
        nz = grid[2]
    else:
        nz = grid.nz

    return np.tile(data, (nz, 1, 1))


# Tile a 1D depth array in lat and lon so it is 3D (depth x lat x lon).
def z_to_xyz (data, grid):

    if isinstance(grid, list):
        nx = grid[0]
        ny = grid[1]
    else:
        nx = grid.nx
        ny = grid.ny

    return np.tile(np.expand_dims(np.expand_dims(np.copy(data),1),2), (1, ny, nx))


# Tile any array (of any dimension) in time, with num_time records. Time will be the first dimension in the new array.
def add_time_dim (data, num_time):

    shape = [num_time]
    for i in range(len(data.shape)):
        shape += [1]
    return np.tile(data, shape)


# Helper function for select_top and select_bottom
def select_level (option, data, masked=True, grid=None, gtype='t', time_dependent=False, return_masked=None):

    if not masked:
        if grid is None:
            print 'Error (select_level): need to supply grid if masked=False'
            sys.exit()
        data_masked = mask_3d(np.copy(data), grid, gtype=gtype, time_dependent=time_dependent)
    else:
        data_masked = data
    if return_masked is None:
        return_masked = masked

    # Figure out the dimensions of the data when the vertical dimension is removed
    collapsed_shape = data_masked.shape[:-3] + data_masked.shape[-2:]
    # Array which will hold values at the given level, initialised to NaN
    data_lev = np.zeros(collapsed_shape)
    data_lev[:] = np.nan
    if option == 'top':
        # Loop from surface to bottom
        k_vals = range(data_masked.shape[-3])
    elif option == 'bottom':
        # Loop from bottom to top
        k_vals = range(data.shape[-3]-1, -1, -1)
    else:
        print 'Error (select_level): invalid option ' + option
        sys.exit()
    for k in k_vals:
        curr_data = data_masked[...,k,:,:]
        # Find points which are unmasked at this vertical level, and which
        # haven't already been assigned a top level
        index = np.nonzero(np.invert(curr_data.mask)*np.isnan(data_lev))
        data_lev[index] = curr_data[index]
    # Anything still NaN is land; mask it out
    data_lev = np.ma.masked_where(np.isnan(data_lev), data_lev)

    if not return_masked:
        # Fill the mask with zeros
        data_lev[data_lev.mask] = 0
        data_lev = data_lev.data

    return data_lev


# Select the top layer from the given array of data. This is useful to see conditions immediately beneath ice shelves.
# If masked=True (default), the input array is already masked with hfac (see mask_3d below). If masked=False, you need to supply the keyword arguments grid, gtype, and time_dependent (as in mask_3d). You can also control whether or not the output array is a masked array using return_masked (default the same value as masked).
# The only assumption about the input array dimensions is that the third last dimension is the vertical dimension. So it can be depth x lat x lon, or time x depth x lat x lon, or even something like experiment x time x depth x lat x lon.
def select_top (data, masked=True, grid=None, gtype='t', time_dependent=False, return_masked=None):
    return select_level('top', data, masked=masked, grid=grid, gtype=gtype, time_dependent=time_dependent, return_masked=return_masked)

    
# Select the bottom layer from the given array of data. See select_top for more documentation.
def select_bottom (data, masked=True, grid=None, gtype='t', time_dependent=False, return_masked=None):
    return select_level('bottom', data, masked=masked, grid=grid, gtype=gtype, time_dependent=time_dependent, return_masked=return_masked)


# Helper function for masking functions below
# depth_dependent only has an effect if the mask is 2D.
def apply_mask (data, mask, time_dependent=False, depth_dependent=False):

    if depth_dependent and len(mask.shape)==2:
        # Tile a 2D mask in the depth dimension
        grid_dim = [data.shape[-1], data.shape[-2], data.shape[-3]]
        mask = xy_to_xyz(mask, grid_dim)
    if time_dependent:
        # Tile the mask in the time dimension
        mask = add_time_dim(mask, data.shape[0])

    if len(mask.shape) != len(data.shape):
        print 'Error (apply_mask): invalid dimensions of data'
        sys.exit()

    data = np.ma.masked_where(mask, data)
    return data


# Mask land out of an array.

# Arguments:
# data: array of data to mask, assumed to be 2D unless time_dependent or depth_dependent say otherwise
# grid: Grid object

# Optional keyword arguments:
# gtype: as in function Grid.get_hfac
# time_dependent: as in function apply_mask
# depth_dependent: as in function apply_mask

def mask_land (data, grid, gtype='t', time_dependent=False, depth_dependent=False):

    return apply_mask(data, grid.get_land_mask(gtype=gtype), time_dependent=time_dependent, depth_dependent=depth_dependent)


# Mask land and ice shelves out of an array, just leaving the open ocean.
def mask_land_ice (data, grid, gtype='t', time_dependent=False, depth_dependent=False):

    return apply_mask(data, grid.get_land_mask(gtype=gtype)+grid.get_ice_mask(gtype=gtype), time_dependent=time_dependent, depth_dependent=depth_dependent)


# Mask land and open ocean out of an array, just leaving the ice shelves.
def mask_except_ice (data, grid, gtype='t', time_dependent=False, depth_dependent=False):

    return apply_mask(data, np.invert(grid.get_ice_mask(gtype=gtype)), time_dependent=time_dependent, depth_dependent=depth_dependent)


# Mask everything except FRIS out of an array.
def mask_except_fris (data, grid, gtype='t', time_dependent=False, depth_dependent=False):

    return apply_mask(data, np.invert(grid.get_fris_mask(gtype=gtype)), time_dependent=time_dependent, depth_dependent=depth_dependent)


# Apply the 3D hfac mask. Dry cells are masked out; partial cells are untouched.

# Arguments:
# data: array of data to mask, assumed to be 3D unless time_dependent=True
# grid: Grid object

# Optional keyword arguments:
# gtype: as in function Grid.get_hfac
# time_dependent: as in function apply_mask

def mask_3d (data, grid, gtype='t', time_dependent=False):

    return apply_mask(data, grid.get_hfac(gtype=gtype)==0, time_dependent=time_dependent)


# Find the indices bounding the given year in the given time array. This script doesn't check that the entire year is within the array! Partial years are supported.

# Arguments:
# time: array of Datetime objects (can be created by the function netcdf_time)
# year: integer containing the year we care about

# Output: two integers containing the first index of year in time, and the first index of the next year (i.e. the last index of the year plus one, following python convention).

def select_year (time, year):

    t_start = -1
    for t in range(time.size):
        if time[t].year == year:
            t_start = t
            break
    if t_start == -1:
        print 'Error (trim_year): this array contains no instances of the year ' + str(year)
        sys.exit()
    t_end = time.size
    for t in range(t_start+1, time.size):
        if time[t].year == year+1:
            t_end = t
            break
    return t_start, t_end


# Convert longitude and latitude to polar stereographic projection used by BEDMAP2. Adapted from polarstereo_fwd.m in the MITgcm Matlab toolbox.
def polar_stereo (lon, lat, a=6378137., e=0.08181919, lat_c=-71, lon0=0):

    # Deep copies of arrays in case they are reused
    lon = np.copy(lon)
    lat = np.copy(lat)

    if lat_c < 0:
        # Southern hemisphere
        pm = -1
    else:
        # Northern hemisphere
        pm = 1

    # Prepare input
    lon = lon*pm*deg2rad
    lat = lat*pm*deg2rad
    lat_c = lat_c*pm*deg2rad
    lon0 = lon0*pm*deg2rad

    # Calculations
    t = np.tan(np.pi/4 - lat/2)/((1 - e*np.sin(lat))/(1 + e*np.sin(lat)))**(e/2)
    t_c = np.tan(np.pi/4 - lat_c/2)/((1 - e*np.sin(lat_c))/(1 + e*np.sin(lat_c)))**(e/2)
    m_c = np.cos(lat_c)/np.sqrt(1 - (e*np.sin(lat_c))**2)
    rho = a*m_c*t/t_c
    x = pm*rho*np.sin(lon - lon0)
    y = -pm*rho*np.cos(lon - lon0)

    return x, y    


# Determine the x and y coordinates based on whether the user wants polar stereographic or not.
def get_x_y (lon, lat, pster=False):
    if pster:
        x, y = polar_stereo(lon, lat)
    else:
        x = lon
        y = lat
    return x, y


# Find the minimum and maximum values of a 2D (lat x lon) array in the given region.
def var_min_max (data, grid, pster=False, zoom_fris=False, xmin=None, xmax=None, ymin=None, ymax=None, gtype='t', ua=False):

    if ua:
        # grid is a list with x and y wrapped up in it
        [x, y] = grid
    else:
        # Choose the correct longitude and latitude arrays
        lon, lat = grid.get_lon_lat(gtype=gtype)
        # Convert to polar stereographic if needed
        x, y = get_x_y(lon, lat, pster=pster)

    # Set limits on axes
    if zoom_fris:
        if pster:
            [xmin, xmax, ymin, ymax] = fris_bounds_pster
        else:
            [xmin, xmax, ymin, ymax] = fris_bounds
    if xmin is None:
        xmin = np.amin(x)
    if xmax is None:
        xmax = np.amax(x)
    if ymin is None:
        ymin = np.amin(y)
    if ymax is None:
        ymax = np.amax(y)

    # Select the correct indices
    loc = (x >= xmin)*(x <= xmax)*(y >= ymin)*(y <= ymax)
    # Find the min and max values
    return np.amin(data[loc]), np.amax(data[loc])


# As above, but for a time x depth array, where the depth axis may be zoomed.
# Assumes not on the w-grid.
def var_min_max_zt (data, grid, zmin=None, zmax=None):

    if zmin is None:
        zmin = grid.z[-1]
    if zmax is None:
        zmax = grid.z[0]
    # Make z 2D
    z = add_time_dim(grid.z, data.shape[0])
    loc = (z >= zmin)*(z <= zmax)
    return np.amin(data[loc]), np.amax(data[loc])


# Find all the factors of the integer n.
def factors (n):

    factors = []
    for i in range(1, n+1):
        if n % i == 0:
            factors.append(i)
    return factors


# Given a path to a directory, make sure it ends with /
def real_dir (dir_path):

    if not dir_path.endswith('/'):
        dir_path += '/'
    return dir_path


# Given an array representing a mask (as above) and 2D arrays of longitude and latitude, mask out the points between the given lat/lon bounds.
def mask_box (data, lon, lat, xmin=None, xmax=None, ymin=None, ymax=None, mask_val=0):

    # Set any bounds which aren't already set
    if xmin is None:
        xmin = np.amin(lon)
    if xmax is None:
        xmax = np.amax(lon)
    if ymin is None:
        ymin = np.amin(lat)
    if ymax is None:
        ymax = np.amax(lat)
    index = (lon >= xmin)*(lon <= xmax)*(lat >= ymin)*(lat <= ymax)
    data[index] = mask_val
    return data


# Mask out the points above or below the line segment bounded by the given points.
def mask_line (data, lon, lat, p_start, p_end, direction, mask_val=0):

    limit = (p_end[1] - p_start[1])/float(p_end[0] - p_start[0])*(lon - p_start[0]) + p_start[1]
    west_bound = min(p_start[0], p_end[0])
    east_bound = max(p_start[0], p_end[0])
    if direction == 'above':
        index = (lat >= limit)*(lon >= west_bound)*(lon <= east_bound)
    elif direction == 'below':
        index = (lat <= limit)*(lon >= west_bound)*(lon <= east_bound)
    else:
        print 'Error (mask_line): invalid direction ' + direction
        sys.exit()
    data[index] = mask_val
    return data


# Interface to mask_line: mask points above line segment (to the north)
def mask_above_line (data, lon, lat, p_start, p_end, mask_val=0):

    return mask_line(data, lon, lat, p_start, p_end, 'above', mask_val=mask_val)


# Interface to mask_line: mask points below line segment (to the south)
def mask_below_line (data, lon, lat, p_start, p_end, mask_val=0):

    return mask_line(data, lon, lat, p_start, p_end, 'below', mask_val=mask_val)


# Like mask_box, but only mask out ice shelf points within the given box.
def mask_iceshelf_box (omask, imask, lon, lat, xmin=None, xmax=None, ymin=None, ymax=None, mask_val=0):

    # Set any bounds which aren't already set
    if xmin is None:
        xmin = np.amin(lon)
    if xmax is None:
        xmax = np.amax(lon)
    if ymin is None:
        ymin = np.amin(lat)
    if ymax is None:
        ymax = np.amax(lat)
    index = (lon >= xmin)*(lon <= xmax)*(lat >= ymin)*(lat <= ymax)*(imask == 1)
    omask[index] = mask_val
    return omask


# Split and rearrange the given array along the given index in the longitude axis (last axis). This is useful when converting from longitude ranges (0, 360) to (-180, 180) if the longitude array needs to be strictly increasing for later interpolation.
def split_longitude (array, split):

    return np.concatenate((array[...,split:], array[...,:split]), axis=-1)


# Return the root mean squared difference between the two arrays (assumed to be the same size), summed over all entries.
def rms (array1, array2):

    return np.sqrt(np.sum((array1 - array2)**2))


# Work out whether the given year is a leap year.
def is_leap_year (year):
    return year%4 == 0 and (year%100 != 0 or year%400 == 0)


# Return the number of days in the given month (indexed 1-12) of the given year.
def days_per_month (month, year):

    # Days per month in non-leap years
    days = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

    # Special case for February in leap years
    if month == 2 and is_leap_year(year):
        return days[month-1]+1
    else:
        return days[month-1]


# Make sure the given field isn't time-dependent, based on the expected number of dimensions.
def check_time_dependent (var, num_dim=3):

    if len(var.shape) == num_dim+1:
        print 'Error (check_time_dependent): variable cannot be time dependent.'
        sys.exit()


# Calculate hFacC, hFacW, or hFacS (depending on value of gtype) without knowing the full grid, i.e. just from the bathymetry and ice shelf draft on the tracer grid.
def calc_hfac (bathy, draft, z_edges, hFacMin=0.1, hFacMinDr=20., gtype='t'):

    if gtype == 'u':
        # Need to get bathy and draft on the western edge of each cell
        # Choose the shallowest bathymetry from the adjacent tracer cells
        bathy = np.concatenate((np.expand_dims(bathy[:,0],1), np.maximum(bathy[:,:-1], bathy[:,1:])), axis=1)
        # Choose the deepest ice shelf draft from the adjacent tracer cells
        draft = np.concatenate((np.expand_dims(draft[:,0],1), np.minimum(draft[:,:-1], draft[:,1:])), axis=1)
        # Now correct for negative wct
        draft = np.maximum(draft, bathy)
    elif gtype == 'v':
        # Need to get bathy and draft on the southern edge of each cell
        bathy = np.concatenate((np.expand_dims(bathy[0,:],0), np.maximum(bathy[:-1,:], bathy[1:,:])), axis=0)
        draft = np.concatenate((np.expand_dims(draft[0,:],0), np.minimum(draft[:-1,:], draft[1:,:])), axis=0)
        draft = np.maximum(draft, bathy)        

    # Calculate a few grid variables
    z_above = z_edges[:-1]
    z_below = z_edges[1:]
    dz = np.abs(z_edges[1:] - z_edges[:-1])
    nz = dz.size
    ny = bathy.shape[0]
    nx = bathy.shape[1]    
    
    # Tile all arrays to be 3D
    bathy = xy_to_xyz(bathy, [nx, ny, nz])
    draft = xy_to_xyz(draft, [nx, ny, nz])
    dz = z_to_xyz(dz, [nx, ny, ny])
    z_above = z_to_xyz(z_above, [nx, ny, nz])
    z_below = z_to_xyz(z_below, [nx, ny, nz])
    
    # Start out with all cells closed
    hfac = np.zeros([nz, ny, nx])
    # Find fully open cells
    index = (z_below >= bathy)*(z_above <= draft)
    hfac[index] = 1
    # Find partial cells due to bathymetry alone
    index = (z_below < bathy)*(z_above <= draft)
    hfac[index] = (z_above[index] - bathy[index])/dz[index]
    # Find partial cells due to ice shelf draft alone
    index = (z_below >= bathy)*(z_above > draft)
    hfac[index] = (draft[index] - z_below[index])/dz[index]
    # Find partial cells which are intersected by both
    index = (z_below < bathy)*(z_above > draft)
    hfac[index] = (draft[index] - bathy[index])/dz[index]

    # Now apply hFac limitations
    hfac_limit = np.maximum(hFacMin, np.minimum(hFacMinDr/dz, 1))    
    index = hfac < hfac_limit/2
    hfac[index] = 0
    index = (hfac >= hfac_limit/2)*(hfac < hfac_limit)
    hfac[index] = hfac_limit[index]

    return hfac


# Calculate bathymetry or ice shelf draft from hFacC.
def bdry_from_hfac (option, hfac, z_edges):

    nz = hfac.shape[0]
    ny = hfac.shape[1]
    nx = hfac.shape[2]
    dz = z_edges[:-1]-z_edges[1:]

    bdry = np.zeros([ny, nx])
    bdry[:,:] = np.nan
    if option == 'bathy':
        # Loop from bottom to top
        k_vals = range(nz-1, -1, -1)
    elif option == 'draft':
        # Loop from top to bottom
        k_vals = range(nz)
    else:
        print 'Error (bdry_from_hfac): invalid option ' + option
        sys.exit()
    for k in k_vals:
        hfac_tmp = hfac[k,:]
        # Identify wet cells with no boundary assigned yet
        index = (hfac_tmp!=0)*np.isnan(bdry)
        if option == 'bathy':
            bdry[index] = z_edges[k] - dz[k]*hfac_tmp[index]
        elif option == 'draft':
            bdry[index] = z_edges[k] - dz[k]*(1-hfac_tmp[index])
    # Anything still NaN is land mask and should be zero
    index = np.isnan(bdry)
    bdry[index] = 0

    return bdry


# Modify the given bathymetry or ice shelf draft to make it reflect what the model will actually see, based on hFac constraints.
def model_bdry (option, bathy, draft, z_edges, hFacMin=0.1, hFacMinDr=20.):

    # First calculate the hFacC
    hfac = calc_hfac(bathy, draft, z_edges, hFacMin=hFacMin, hFacMinDr=hFacMinDr)
    # Now calculate the new boundary
    return bdry_from_hfac(option, hfac, z_edges)


# Determine if a string is an integer.
def str_is_int (s):
    try:
        int(s)
        return True
    except ValueError:
        return False


# Find the Cartesian distance between two lon-lat points.
# This also works if one of point0, point1 is a 2D array of many points.
def dist_btw_points (point0, point1):
    [lon0, lat0] = point0
    [lon1, lat1] = point1
    dx = rEarth*np.cos((lat0+lat1)/2*deg2rad)*(lon1-lon0)*deg2rad
    dy = rEarth*(lat1-lat0)*deg2rad
    return np.sqrt(dx**2 + dy**2)


# Find all ice shelf front points and return them as a list.
# For a specific ice shelf, pass a special ice_mask (such as grid.fris_mask)
def ice_shelf_front_points (grid, ice_mask=None, gtype='t', xmin=None, xmax=None, ymin=None, ymax=None):

    from interpolation import neighbours

    # Build masks
    if ice_mask is None:
        ice_mask = grid.get_ice_mask(gtype=gtype)
    open_ocean = grid.get_open_ocean_mask(gtype=gtype)

    # Set any remaining bounds
    lon, lat = grid.get_lon_lat(gtype=gtype)
    if xmin is None:
        xmin = np.amin(lon)
    if xmax is None:
        xmax = np.amax(lon)
    if ymin is None:
        ymin = np.amin(lat)
    if ymax is None:
        ymax = np.amax(lat)

    # Find number of open-ocean neighbours for each point
    num_open_ocean_neighbours = neighbours(open_ocean, missing_val=0)[-1]
    # Find all ice shelf points within bounds that have at least 1 open-ocean neighbour
    return ice_mask*(lon >= xmin)*(lon <= xmax)*(lat >= ymin)*(lat <= ymax)*(num_open_ocean_neighbours > 0)


# Given an axis with values in the centre of each cell, find the locations of the boundaries of each cell (extrapolating for the outer boundaries).
def axis_edges (x):
    x_bound = 0.5*(x[:-1]+x[1:])
    x_bound = np.concatenate(([2*x_bound[0]-x_bound[1]], x_bound, [2*x_bound[-1]-x_bound[-2]]))
    return x_bound


# Given an array (or two), find the min and max value (unless these are already defined), and pad with the given percentage (default 2%) of the difference between them.
def choose_range (x1, x2=None, xmin=None, xmax=None, pad=0.02):

    xmin_set = xmin is not None
    xmax_set = xmax is not None

    if not xmin_set:
        xmin = np.amin(x1)
        if x2 is not None:
            xmin = min(xmin, np.amin(x2))
    if not xmax_set:
        xmax = np.amax(x1)
        if x2 is not None:
            xmax = max(xmax, np.amax(x2))
            
    delta = pad*(xmax-xmin)
    if not xmin_set:
        xmin -= delta
    if not xmax_set:
        xmax += delta
    return xmin, xmax


# Figure out if a field is depth-dependent, given the last two dimensions being lat and lon, and the possibility of time-dependency.
def is_depth_dependent (data, time_dependent=False):
    return (time_dependent and len(data.shape)==4) or (not time_dependent and len(data.shape)==3)


# Mask everything outside the given bounds. The array must include latitude and longitude dimensions; depth and time are optional.
def mask_outside_box (data, grid, gtype='t', xmin=None, xmax=None, ymin=None, ymax=None, time_dependent=False):
    depth_dependent = is_depth_dependent(data, time_dependent=time_dependent)
    lon, lat = grid.get_lon_lat(gtype=gtype)
    if depth_dependent:
        lon = xy_to_xyz(lon, grid)
        lat = xy_to_xyz(lat, grid)
    if time_dependent:
        lon = add_time_dim(lon, data.shape[0])
        lat = add_time_dim(lat, data.shape[0])
    if xmin is None:
        xmin = np.amin(lon)
    if xmax is None:
        xmax = np.amax(lon)
    if ymin is None:
        ymin = np.amin(lat)
    if ymax is None:
        ymax = np.amax(lat)
    index = np.invert((lon >= xmin)*(lon <= xmax)*(lat >= ymin)*(lat <= ymax))
    return np.ma.masked_where(index, data)


# Given a field with a periodic boundary (in longitude), wrap it on either end so we can interpolate with  no gaps in the middle. If is_lon, add/subtract 360 from these values so it is periodic.
def wrap_periodic (data, is_lon=False):

    # Add 1 column to the beginning and 1 to the end of the longitude dimension
    new_shape = list(data.shape[:-1]) + [data.shape[-1]+2]
    data_wrap = np.empty(new_shape)
    # Copy the middle
    data_wrap[...,1:-1] = data
    # Wrap the edges from either end
    data_wrap[...,0] = data[...,-1]
    data_wrap[...,-1] = data[...,0]
    if is_lon:
        # Add/subtract 360 so monotonic
        data_wrap[...,0] -= 360
        data_wrap[...,-1] += 360
    return data_wrap


# Given an array of one year of data where the first dimension is time, convert from daily averages to monthly averages.
# If you want to consider leap years, pass the year argument. The default is a year with no leap (1979).
# If there is more than one record per day, set the per_day argument.
def daily_to_monthly (data, year=1979, per_day=1):

    if data.shape[0]/per_day not in [365, 366]:
        print 'Error (daily_to_monthly): The first dimension is not time, or else this is not one year of data.'
        sys.exit()
    new_shape = [12] + list(data.shape[1:])
    if isinstance(data, np.ma.MaskedArray):
        data_monthly = np.ma.empty(new_shape)
    else:
        data_monthly = np.empty(new_shape)
    t = 0
    for month in range(12):
        nt = days_per_month(month+1, year)*per_day
        data_monthly[month,...] = np.mean(data[t:t+nt,...], axis=0)
        t += nt
    return data_monthly
    
    

    




    
    
