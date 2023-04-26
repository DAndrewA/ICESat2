# ICESat2

This library of code will be the main location that I will try to write all my scripts to. The code will focus on obtaining and manipulating ICESat2 data, and any data I want to compare it to (i.e. Summit data).

This repository will primarily contain my `eeasm_icesat` package which I will be developing to handle the data I want to use during my PhD. At the time of writing (26/04/2023), this includes the ICESat-2 ATL09 data, MPL lidar data and MMCR radar data. This will be developed to standardise the data format accross my work in a way that will allow for easier comparisson between the data sources.

This also includes the subdirectory `neely_heather_code`, which contains code written by Ryan Neely, Heather Guy and Sarah Barr, from which I am at points taking heavy inspiration.

Notebooks testing my scripts can be found in the `tests` directory, to ensure that the installable package isn't cluttered.

## Installation

To install the `eeasm_icesat` package, download this repository and navigate to its root folder in your terminal. Then, in the desired python environment, enter the command
```python
pip install -e .
```

This will create an editable install of the package, allowing for the scripts to be tweaked to suit the user's needs, whilst still allowing the code to be imported into other scripts and notebooks.

## Usage

To use the package generally, all one has to do is install `eeasm_icesat` according to the instructions given above, and then add the line
```python
import eeasm_icesat
```
into their script/notebook.

### eeasm_icesat.atl09

This sub-package contains the functionality to download, load and manipulate the ICESat-2 ATL09 data. Downloading of the data is done through the `icepyx` package, and then I use `xarray` to load the data into a specified dataset format. The `add_coordinates` script allows for additional useful variables to be added to this dataset, such as the distance to a given point (i.e. Summit), the height above ground level and time.

### eeasm_icesat.mpl

This sub-package will contain the functionality to load in and manipulate the Summit MPL data. This will be loaded in via `xarray` from the ingested format files (see my other package `mplgz_to_ingested`).

### eeasm_icesat.mmcr

This sub-package will allow for the loading and manipulation of the Summit MMCR radar data. This isn't currently implemented, but future work will hopefully focus on using this data to get cloud-phase information from the combined lidar-radar retrievals.