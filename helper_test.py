import helper as hh
import move_data_files
import datetime
import os


path_root = '/home/users/eeasm'
path_root = '/gws/nopw/j04/ncas_radar_vol2/'
icecaps_loc = ['data','ICECAPSarchive']

path_icecaps = os.path.join(path_root,*icecaps_loc)
print(f'path_icecaps: {path_icecaps}')

mpl_loc = ['mpl','raw']
mmcr_loc = ['mmcr','mom']
path_mpl = os.path.join(path_icecaps,*mpl_loc)
path_mmcr = os.path.join(path_icecaps,*mmcr_loc)

mpl_format = '%Y%m%d*.mpl.gz'
mmcr_format = '%Y%j*.nc.zip' # uses the julian day

print(path_mpl, path_mmcr)


d0 = '2022 08 11'
d0_dt = datetime.datetime.strptime(d0, '%Y %m %d')
dt = datetime.timedelta(days=0.5)
dtrange = [d0_dt - dt, d0_dt + dt]
dt_printFomrat = '%Y-%m-%d-%H'

print(f'Given date range: {dtrange[0].strftime(dt_printFomrat)} to {dtrange[1].strftime(dt_printFomrat)}.')

print('')
print('Getting the MPL and MMCR files in the desired range:')

mpl_files = move_data_files.find_files_in_date_range(path_mpl,dtrange,mpl_format)
mmcr_files = move_data_files.find_files_in_date_range(path_mmcr,dtrange,mmcr_format)

def print_summary(obj,descriptor):
    print('______________________')
    print(descriptor)
    print(f'len: {len(obj)}')
    print(obj)

print_summary(mpl_files,'MPL files')
print_summary(mmcr_files, 'MMCR files')