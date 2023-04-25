def download_rgt(rgt,cycles = None):
    '''Function to download ATL09 files for a given Reference Ground Track.
    
    INPUTS:
        rgt [int]: integer value for the desired RGT
        cycles [list or None]: None for all cycles; otherwise, limits the cycles that we take orbits from.
    '''