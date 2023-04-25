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
    # convert numpy datatypes to python data types
    dto = dto.astype('float').item()
    m = m.item()
    c = c.item()
    sdm = sdm.item()
    sdc = sdc.item()

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
    times = []
    m = []
    c = []
    sdm = []
    sdc = []

    with open(fname, 'rb') as f:
        fmt = '<ddddd'
        size = struct.calcsize(fmt)
        # keep reading the file when the buffer is the right size
        while (buff := f.read(size)):
            vals = struct.unpack(fmt,buff)
            times.append(
            np.datetime64(datetime.datetime.utcfromtimestamp(vals[0])))
            m.append(vals[1])
            c.append(vals[2])
            sdm.append(vals[3])
            sdc.append(vals[4])
    
    times = np.array(times, dtype=np.datetime64)
    m = np.array(m, dtype=np.float64)
    c = np.array(c, dtype=np.float64)
    sdm = np.array(sdm, dtype=np.float64)
    sdc = np.array(sdc, dtype=np.float64)
    return times, m, c, sdm, sdc








# FOR TESTING PURPOSES ONLY
def _test_read_write():
    def _synthetic_data():
        times = np.array([np.datetime64('2019-02-01T00:51'),
                np.datetime64('2019-02-01T14:16'),
                np.datetime64('2019-02-01T10:53:12'),
                np.datetime64('2022-04-03T21:47:36')],dtype=np.datetime64)
        m = np.array([2,3,4,5.863248758923],dtype=np.float64)
        c = np.array([123123,675657,3.543543,-234],dtype=np.float64)
        sdm = np.array([234,423,532,235],dtype=np.float64)
        sdc = np.array([1,1.01,1.0001,1.000001],dtype=np.float64)
        return times, m, c, sdm, sdc

    data = _synthetic_data()
    filename = '/home/users/eeasm/_scripts/ICESat2/src/mpl/range_height.bin'
    for t,m,c,sdm,sdc in zip(*data):
        write_to_binary(filename, t, m, c, sdm, sdc)
    print('Data written!!')

    data_out = read_from_binary(filename)

    print('=============================')
    print('data:')
    for d,n in zip(data, ['times', 'c', 'm', 'sdm', 'sdc']):
        print(f'{n:>6}: {d}')
    print('=============================')
    print('data_out:')
    for d,n in zip(data_out, ['times', 'c', 'm', 'sdm', 'sdc']):
        print(f'{n:>6}: {d}')