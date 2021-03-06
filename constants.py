#######################################################
# Scalar constants
#######################################################

import numpy as np

# Acceleration due to gravity (m/s^2)
gravity = 9.81
# Density of freshwater (kg/m^3)
rho_fw = 1e3
# Density of ice (kg/m^3)
rho_ice = 917.
# Seconds per day
sec_per_day = 24*60*60.
# Seconds per year
sec_per_year = 365.25*sec_per_day
# Months per year
months_per_year = 12
# Degrees to radians conversion factor
deg2rad = np.pi/180.0
# Radius of Earth
rEarth = 6.371e6
# Celsius to Kelvins intercept
temp_C2K = 273.15
# Latent heat of vapourisation (J/kg)
Lv = 2.5e6
# Ideal gas constant for water vapour (J/K/kg)
Rv = 461.5
# Reference saturation vapour pressure (Pa)
es0 = 611
# Coefficient for specific humidity calculation
sh_coeff = 0.62197
# Specific heat of seawater (J/K/kg)
Cp_sw = 4180.

# Degrees formatted nicely in a string
deg_string = r'$^{\circ}$'

# Bounds on FRIS (a few bits of Eastern Weddell ice shelves are included too - use Grid.fris_mask to get just FRIS. These bounds are for plotting.)
# lon_min, lon_max, lat_min, lat_max
fris_bounds = [-85., -29., -84., -74.]
# Polar stereographic version
fris_bounds_pster = [-1.6e6, -5e5, 1.2e5, 1.365e6]
# Bounds on Eastern Weddell ice shelves.
ewed_bounds = [-30., 40., -77., -65.]
# Bounds on Weddell Gyre.
wed_gyre_bounds = [-60., 30., -90., -50.]
# Bounds on continental shelf in front of FRIS.
sws_shelf_bounds = [-70., -30., -79., -72.]
# Threshold bathymetry delineating shelf
sws_shelf_h0 = -1250
# Endpoints of line dividing the inner and outer shelf (lon0, lon1, lat0, lat1)
sws_shelf_line = [-70., -15., -72., -80.]
# Bounds on location to search for grounded iceberg A-23A
a23a_bounds = [-47., -38., -77., -75.]
# Bounds on Berkner Island
berkner_island_bounds = [-55, -41, -81, -77]

# Resolution of SOSE grid in degrees
sose_res = 1/6.

# BEDMAP2 grid parameters
bedmap_dim = 6667    # Dimension
bedmap_bdry = 3333000    # Polar stereographic coordinate (m) on boundary
bedmap_res = 1000    # Resolution (m)
bedmap_missing_val = -9999    # Missing value for bathymetry north of 60S

# Bounds on boxes for Amundsen Sea regions
# In form lon_min, lon_max, lat_min, lat_max
# Pine Island Bay
bounds_PIB = [-105, -101, -75.2, -74.2]
# Dotson
bounds_Dot = [-114, -110.5, -74.1, -73.2]


