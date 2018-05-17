#######################################################
# Lat-lon shaded plots
#######################################################

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import sys
import numpy as np

from io import Grid, read_netcdf, find_variable
from utils import convert_ismr, mask_except_zice, mask_3d, mask_land_zice, mask_land, select_bottom
from plot_utils import finished_plot, cell_boundaries, latlon_axes, set_colours, shade_land, shade_land_zice, contour_iceshelf_front
from diagnostics import t_minus_tf


# Basic lat-lon plot of any variable.

# Arguments:
# var: 2D (lat x lon) array of data to plot, already masked as desired
# grid: Grid object

# Optional keyword arguments:
# gtype: as in function cell_boundaries
# include_shelf: if True (default), plot the values beneath the ice shelf and contour the ice shelf front. If False, shade the ice shelf in grey like land.
# ctype: as in function set_colours
# vmin, vmax: as in function set_colours
# return_fig: if True, return the figure and axis variables so that more work can be done on the plot (eg adding titles). Default False.
# fig_name: as in function finished_plot
# change_points: only matters if ctype='ismr'. As in function set_colours.

def latlon_plot (var, grid, gtype='t', include_shelf=True, ctype='basic', vmin=None, vmax=None, return_fig=False, fig_name=None, change_points=None):

    # Prepare quadrilateral patches
    lon, lat, var_plot = cell_boundaries(var, grid, gtype=gtype)
    # Get colourmap
    cmap, vmin, vmax = set_colours(var, ctype=ctype, vmin=vmin, vmax=vmax, change_points=change_points)

    fig, ax = plt.subplots()
    if include_shelf:
        # Shade land in grey
        shade_land(ax, grid)
    else:
        # Shade land and ice shelves in grey
        shade_land_zice(ax, grid)
    # Plot the data    
    img = ax.pcolormesh(lon, lat, var_plot, cmap=cmap, vmin=vmin, vmax=vmax)
    if include_shelf:
        # Contour ice shelf front
        contour_iceshelf_front(ax, grid)
    # Choose what the endpoints of the colourbar should do
    if vmin is None and vmax is None:
        extend='neither'
    elif vmin is not None and vmax is None:
        extend='min'
    elif vmin is None and vmax is not None:
        extend='max'
    elif vmin is not None and vmax is not None:
        extend='both'
    plt.colorbar(img, extend=extend)
    latlon_axes(ax)

    if return_fig:
        return fig, ax
    else:
        finished_plot(fig, fig_name=fig_name)


# Plot ice shelf melt rate field.

# Arguments:
# ismr: 2D (lat x lon) array of ice shelf melt rate in m/y, already masked
# grid: Grid object

# Optional keyword arguments:
# vmin, vmax: as in function set_colours
# change_points: as in function set_colours
# fig_name: as in function finished_plot

def plot_ismr (ismr, grid, vmin=None, vmax=None, change_points=None, fig_name=None):

    fig, ax = latlon_plot(ismr, grid, ctype='ismr', vmin=vmin, vmax=vmax, change_points=change_points, return_fig=True)
    ax.set_title('Ice shelf melt rate (m/y)', fontsize=18)
    finished_plot(fig, fig_name=fig_name)


# Plot bottom water temperature or salinity.

# Arguments:
# var: 'temp' or 'salt'
# data: 3D (depth x lat x lon) array of temperature in degC or salinity in psu, already masked with hfac
# grid: Grid object

# Optional keyword arguments:
# vmin, vmax: as in function set_colours
# fig_name: as in function finished_plot

def plot_bw (var, data, grid, vmin=None, vmax=None, fig_name=None):

    fig, ax = latlon_plot(select_bottom(data), grid, vmin=vmin, vmax=vmax, return_fig=True)
    if var == 'temp':
        ax.set_title(r'Bottom water temperature ($^{\circ}$C)', fontsize=18)
    elif var == 'salt':
        ax.set_title('Bottom water salinity (psu)', fontsize=18)
    finished_plot(fig, fig_name=fig_name)


# Plot surface temperature or salinity.

# Arguments:
# var: 'temp' or 'salt'
# data: 3D (depth x lat x lon) array of temperature in degC or salinity in psu, already masked with hfac
# grid: Grid object

# Optional keyword arguments:
# vmin, vmax: as in function set_colours
# fig_name: as in function finished_plot

def plot_ss (var, data, grid, vmin=None, vmax=None, fig_name=None):

    fig, ax = latlon_plot(data[0,:], grid, include_shelf=False, vmin=vmin, vmax=vmax, return_fig=True)
    if var == 'temp':
        ax.set_title(r'Sea surface temperature ($^{\circ}$C)', fontsize=18)
    elif var == 'salt':
        ax.set_title('Sea surface salinity (psu)', fontsize=18)
    finished_plot(fig, fig_name=fig_name)


# Plot miscellaneous 2D variables that do not include the ice shelf: sea ice concentration or thickness, mixed layer depth, free surface.

# Arguments:
# var: 'aice', 'hice', 'mld', or 'eta'
# data: 2D (lat x lon) array of sea ice concentration (fraction), sea ice thickness, mixed layer depth, or free surface (all m), already masked with the land and ice shelf
# grid: Grid object

# Optional keyword arguments:
# ctype: as in function set_colours
# vmin, vmax: as in function set_colours
# fig_name: as in function finished_plot

def plot_2d_noshelf (var, data, grid, ctype='basic', vmin=None, vmax=None, fig_name=None):

    fig, ax = latlon_plot(data, grid, include_shelf=False, ctype=ctype, vmin=vmin, vmax=vmax, fig_name=fig_name, return_fig=True)
    if var == 'aice':
        ax.set_title('Sea ice concentration (fraction)', fontsize=18)
    elif var == 'hice':
        ax.set_title('Sea ice effective thickness (m)', fontsize=18)
    elif var == 'mld':
        ax.set_title('Mixed layer depth (m)', fontsize=18)
    elif var == 'eta':
        ax.set_title('Free surface (m)', fontsize=18)
    finished_plot(fig, fig_name=fig_name)


# Plot surface salt flux, including in the ice shelf cavities.

# Arguments:
# saltflx: 2D (lat x lon) array of surface salt flux in kg/m^2/s, already masked with land
# grid: Grid object

# Optional keyword arguments:
# vmin, vmax: as in function set_colours
# fig_name: as in function finished_plot

def plot_saltflx (saltflx, grid, vmin=None, vmax=None, fig_name=None):

    fig, ax = latlon_plot(saltflx, grid, ctype='plusminus', vmin=vmin, vmax=vmax, fig_name=fig_name, return_fig=True)
    ax.set_title(r'Surface salt flux (kg/m$^2$/s)', fontsize=18)
    finished_plot(fig, fig_name=fig_name)


# Plot the difference from the in-situ freezing point.

# Arguments:
# tminustf: 3D (depth x lat x lon) array of difference from the freezing point in degC, already masked with hfac
# grid: Grid object

# Optional keyword arguments:
# tf_option: 'bottom' (to plot difference from in-situ freezing point in the bottom layer, default), 'max' (to plot maximum at each point in the water column), 'min' (to plot minimum).
# vmin, vmax: as in function set_colours
# fig_name: as in function finished_plot
def plot_tminustf(tminustf, grid, tf_option='bottom', vmin=None, vmax=None, fig_name=None):

    if tf_option == 'bottom':
        tmtf_plot = select_bottom(tminustf)
        title_end = '(bottom layer)'
    elif tf_option == 'max':
        tmtf_plot = np.amax(tminustf, axis=0)
        title_end = '(maximum over depth)'
    elif tf_option == 'min':
        tmtf_plot = np.amin(tminustf, axis=0)
        title_end = '(minimum over depth)'
    fig, ax = latlon_plot(tmtf_plot, grid, ctype='plusminus', vmin=vmin, vmax=vmax, fig_name=fig_name, return_fig=True)
    ax.set_title(r'Difference from in-situ freezing point ($^{\circ}$C)' + '\n' + title_end, fontsize=18)
    finished_plot(fig, fig_name=fig_name)


# NetCDF interface. Call this function with a specific variable key and information about the necessary NetCDF file, to get a nice lat-lon plot.

# Arguments:
# var: keyword indicating which special variable to plot. The options are:
#      'ismr': ice shelf melt rate
#      'bwtemp': bottom water temperature
#      'bwsalt': bottom water salinity
#      'sst': surface temperature
#      'sss': surface salinity
#      'aice': sea ice concentration
#      'hice': sea ice thickness
#      'mld': mixed layer depth
#      'eta': free surface
#      'saltflx': surface salt flux
#      'tminustf': difference from in-situ freezing point
# file_path: path to NetCDF file containing the necessary variable:
#            'ismr': SHIfwFlx
#            'bwtemp': THETA
#            'bwsalt': SALT
#            'sst': THETA
#            'sss': SALT
#            'aice': SIarea
#            'hice': SIheff
#            'mld': MXLDEPTH
#            'eta': ETAN
#            'saltflx': SIempmr
#            'tminustf': THETA and SALT
#            If there are two variables needed (eg THETA and SALT for 'tminustf') and they are stored in separate files, you can put the other file in second_file_path (see below).
# grid: either a Grid object, or the path to the NetCDF grid file

# Optional keyword arguments:
# time_index, t_start, t_end, time_average: as in function read_netcdf. You must either define time_index or set time_average=True, so it collapses to a single record.
# vmin, vmax: as in function set_colours
# fig_name: as in function finished_plot
# second_file_path: path to NetCDF file containing a second variable which is necessary and not contained in file_path. It doesn't matter which is which.
# change_points: only matters for 'ismr'. As in function set_colours.
# tf_option: only matters for 'tminustf'. As in function plot_tminustf.

def read_plot_latlon (var, file_path, grid, time_index=None, t_start=None, t_end=None, time_average=False, vmin=None, vmax=None, fig_name=None, second_file_path=None, change_points=None, tf_option='bottom'):

    # Make sure we'll end up with a single record in time
    if time_index is None and not time_average:
        print 'Error (read_plot_latlon): either specify time_index or set time_average=True.'
        sys.exit()

    if not isinstance(grid, Grid):
        # This is the path to the NetCDF grid file, not a Grid object
        # Make a grid object from it
        grid = Grid(grid)

    # Read necessary variables from NetCDF file(s), and mask appropriately
    if var == 'ismr':
        # Convert melting to m/y
        ismr = mask_except_zice(convert_ismr(read_netcdf(file_path, 'SHIfwFlx', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average)), grid)
    if var in ['bwtemp', 'sst', 'tminustf']:
        # Read temperature. Some of these variables need more than temperature and so second_file_path might be set.
        if second_file_path is not None:
            file_path_use = find_variable(file_path, second_file_path, 'THETA')
        else:
            file_path_use = file_path        
        temp = mask_3d(read_netcdf(file_path_use, 'THETA', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)
    if var in ['bwsalt', 'sss', 'tminustf']:
        if second_file_path is not None:
            file_path_use = find_variable(file_path, second_file_path, 'SALT')
        else:
            file_path_use = file_path
        salt = mask_3d(read_netcdf(file_path_use, 'SALT', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)
    if var == 'aice':
        aice = mask_land_zice(read_netcdf(file_path, 'SIarea', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)
    if var == 'hice':
        hice = mask_land_zice(read_netcdf(file_path, 'SIheff', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)
    if var == 'mld':
        mld = mask_land_zice(read_netcdf(file_path, 'MXLDEPTH', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)
    if var == 'eta':
        eta = mask_land_zice(read_netcdf(file_path, 'ETAN', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)
    if var == 'saltflx':
        saltflx = mask_land(read_netcdf(file_path, 'SIempmr', time_index=time_index, t_start=t_start, t_end=t_end, time_average=time_average), grid)

    # Any additional calculations
    if var == 'tminustf':
        tminustf = t_minus_tf(temp, salt, grid)

    # Plot
    if var == 'ismr':
        plot_ismr(ismr, grid, vmin=vmin, vmax=vmax, change_points=change_points, fig_name=fig_name)
    elif var == 'bwtemp':
        plot_bw('temp', temp, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'bwsalt':
        plot_bw('salt', salt, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'sst':
        plot_ss('temp', temp, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'sss':
        plot_ss('salt', salt, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'aice':
        plot_2d_noshelf('aice', aice, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'hice':
        plot_2d_noshelf('hice', hice, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'mld':
        plot_2d_noshelf('mld', mld, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'eta':
        plot_2d_noshelf('eta', eta, grid, ctype='plusminus', vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'saltflx':
        plot_saltflx(saltflx, grid, vmin=vmin, vmax=vmax, fig_name=fig_name)
    elif var == 'tminustf':
        plot_tminustf(tminustf, grid, vmin=vmin, vmax=vmax, tf_option=tf_option, fig_name=fig_name)
    else:
        print 'Error (read_plot_latlon): variable key ' + str(var) + ' does not exist'
    

    
