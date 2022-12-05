'''Script to go through a .h5 file and show the available variable fields'''

import h5py

#fname = input('filename: ')
fname = '/home/users/eeasm/ICESAT_data/ATL09_20210320224042_13281001_005_01.h5'

f = h5py.File(fname,'r')


indentChar = '|    ' # character by which each subsequent layer of groups should be indented
connectionChar = '|-- '

def iterateThroughKeys(obj,indStr):
    '''Function to itterate through the keys of the given object obj'''
    indentStr = indentChar + indStr
    for k in obj.keys():
        print(indStr + k)
        if isinstance(obj[k],h5py._hl.group.Group): # TODO: check this comparisson is the correct format
            iterateThroughKeys(obj[k],indentStr)


print(fname)
iterateThroughKeys(f,connectionChar)

# seeing the keys for the profile data
#pd1 = f['profile_1']
#print(pd1.keys())
#for l in pd1.keys():
#    print(l, type(pd1[l]))
#    for k in pd1[l].keys():
#        print(l,k, type(pd1[l][k]))
