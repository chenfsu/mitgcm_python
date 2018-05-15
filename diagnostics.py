import numpy as np
import sys
import constants as const

# Helper function for t_minus_tf
# Assumes temp, salt, z are all the same size
def tfreeze (temp, salt, z):

    a0 = -0.0575
    b = -7.61e-4
    c0 = 0.0901

    return a0*salt + b*abs(z) + c0


# Calculate the difference from the in-situ freezing point.
# Arguments:
# temp, salt: arrays of temperature and salinity. They can be 3D (depth x lat x lon) or 4D (time x depth x lat x lon), in which case you need time_dependent=True.
# grid = Grid object (see io.py)
# Optional keyword arguments:
# time_dependent: boolean indicating that temp and salt are 4D, with a time dimension. Default False.
def t_minus_tf (temp, salt, grid, time_dependent=False):

    # Tile the z coordinates to be the same size as temp and salt
    if time_dependent:
        # 4D arrays
        num_time = temp.shape[0]
        z = np.tile(np.expand_dims(np.expand_dims(grid.z,1),2), (num_time, 1, grid.ny, grid.nx))
    else:
        # 3D arrays
        z = np.tile(np.expand_dims(np.expand_dims(grid.z,1),2), (1, grid.ny, grid.nx))

    return temp - tfreeze(temp, salt, z)


# Calculate the total mass loss (result='massloss', default) or area-averaged melt rate (result='meltrate').
def total_melt (ismr, dA, mask, result='massloss'):

    if result == 'meltrate':
        # Area-averaged melt rate
        return sum(ismr*dA*mask)/sum(dA*mask)
    elif result == 'massloss':
        # Total mass loss
        return sum(ismr*dA*mask)*const.rho_ice*1e-12


