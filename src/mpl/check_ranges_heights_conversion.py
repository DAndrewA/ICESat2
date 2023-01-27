'''Author: Andrew Martin
Creation date: 27/1/23

Script to generate data for the linear relation between the ranges_ and height variables from the ingested and mpl2nc data.

+ The script should go through each ingested file systematically, and access the mpl files associated with it.
+ It should read the mpl files and the ingested files, calculate the ranges_ variable, and then the c and m values for the linear relation.
+ It should then store the datetime64 (start of day), c and m values calculated to a binary file. This file can be read out later to analyse whether the ranges_ and heights relation has changed with time.
'''

import numpy as np
import xarray as xr
import datetime
import struct
import os

from get_mpl_from_archive import get_mpl_from_archive

# main process

def write_to_binary(fname, dto, m, c, sdm, sdc):
    '''Function to write the datetime, m and c values to a binary file.
    
    INPUTS:
        fname : string
            The full filename of the binary file to be written to
            
        dto : numpy.datetime64
            The datetime64 object for the start of the day. Can be written in as a 64-bit object to the buffer

        m : float64
            The daily mean slope of the height~ranges_ relation.

        c : float64
            The daily mean offset for the linear height~ranges_ relation.

        sdm : float64
            The standard deviation for the m values over the day

        sdc: The standard deviation for the c values of the day
    '''
    with open(fname, 'ab') as f:
        # format for the binary writing.
        # little endian, three 8-byte segments for "double"s
        fmt = '<ddddd'
        size = struct.calcsize(fmt)
        bts = struct.pack(fmt,dto,m,c,sdm,sdc)
        f.write(bts)


def read_from_binary(fname):
    '''Function to read the binary output file and return the values.
    
    INPUTS:
        fname : string
            The full filename of the binary file to read
            
    OUTPUTS:
        times : np.ndarray : dtype=np.datetime64
            array containing the days that the values were calculated for

        m : np.ndarray : dtype=float64
            array containing the slope values for the height~ranges_ relation

        c : np.ndarray : dtype=float64
            array containing the offset values for the linear height~ranges_ relation

        sdm : np.ndarray : dtype=float64
            array containing the standard devaition on m values each day

        sdc : np.ndarray : dtype=float64
            array containing the standard deviation on c values.
    '''
    times = np.array([], dtype=np.datetime64)
    m = np.array([], dtype=np.float64)
    c = np.array([], dtype=np.float64)
    sdm = np.array([], dtype=np.float64)
    sdc = np.array([], dtype=np.float64)

    with open(fname, 'rb'):
        jksgfuhsbfeiuvf