# `eeasm_icesat.dda.steps`

This library is for the individual steps performed during the course of the DDA-atmos algorithm, and will include the additional steps required for the detection of liquid-bearing, attenuating clouds.

## Data format

For the data format, all of the steps will operate on numpy ndarray objects, that have the following properties:

`axis=0`: temporal evolution, each vertical profile i

`axis=1`: vertical profile information, height bin j

i.e. `data[i,j]` represents the *i*th vertical profile, and the *j*th height bin.

Otherwise, single-axis vectors should be queezed and will then be utilised against their corresponding axis in the code.