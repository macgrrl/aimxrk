'''
Outputs CSV as specified below from XRK metadata

Usage:
xrkcsv_session.py [-h, --help] [-o, --output filename.csv] [-d, --debug [-v, --verbose]] filename.xrk..

Output:
See README.md for XRK session log CSV file format

'''

# import modules
import os
import sys
import argparse
import csv
import datetime as dt
import re

import pyarrow.compute as pc

from libxrk import aim_xrk

import frc_debug as dbg
import xrk_common as common


# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a 'deep suppression' of stdout and stderr in
    Python, i.e. will suppress all print, even if the print originates in a
    compiled C/Fortran sub-function.
       This will not suppress raised exceptions, since exceptions are printed
    to stderr just before a script exits, and after the context manager has
    exited (at least, I think that is why it lets exceptions through).

    '''
    def __init__(self):
        # Open a pair of null files
        self.null_fds =  [os.open(os.devnull,os.O_RDWR) for x in range(2)]
        # Save the actual stdout (1) and stderr (2) file descriptors.
        self.save_fds = [os.dup(1), os.dup(2)]

    def __enter__(self):
        # Assign the null pointers to stdout and stderr.
        os.dup2(self.null_fds[0],1)
        os.dup2(self.null_fds[1],2)

    def __exit__(self, *_):
        # Re-assign the real stdout/stderr back to (1) and (2)
        os.dup2(self.save_fds[0],1)
        os.dup2(self.save_fds[1],2)
        # Close all file descriptors
        for fd in self.null_fds + self.save_fds:
            os.close(fd)


# constants

# app details
app_name = 'xrkcsv_session.py' # application name
app_version = '1.0' # application version
app_description = 'Extracts metadata from AIM XRK files and outputs CSV'

# conversions
km_to_mi = 0.6213712 # number of miles in a kilometre
ms_to_sec = 0.001 # milliseconds to seconds
min_in_hr = 60.0 # minutes in an hour
sec_in_hr = 3600.0 # seconds in an hour

# regular expression match group names
re_hours = 'hours'
re_minutes = 'minutes'
re_seconds = 'seconds'

# regular expression pattern for h:m:s (decimal hours, minutes, seconds)
re_hms_pattern = r'(?P<' + re_hours + r'>\d+):(?P<' + re_minutes + r'>\d+):(?P<' + re_seconds + r'>\d+)'


# functions


# main program

# parse options & arguments
parser = argparse.ArgumentParser(prog=app_name, description=app_description)

parser.add_argument('-d', '--debug', action='store_true',
                    help='turn on debugging')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='enable verbose mode')
parser.add_argument('-o', '--output', action='store', default='',
                    help='output CSV filepath')

parser.add_argument('--version', action='version', version='%(prog)s ' + app_version)

parser.add_argument('files', nargs=argparse.REMAINDER, help='Filenames')

arguments_namespace, passed_args = parser.parse_known_args()
arguments_dict = vars(arguments_namespace)

dbg.set_debug(arguments_dict['debug'])
verbose_flag = arguments_dict['verbose']
output_csv_filepath = arguments_dict['output']
xrk_filepaths = arguments_dict['files']

count_xrk_filepaths = len(xrk_filepaths)

dbg.debug_print(
    f'debug_flag: {dbg.debug_flag()}',
    f'output_csv_filepath: {output_csv_filepath}',
    f'xrk_filepaths (count:{count_xrk_filepaths}): {xrk_filepaths}',
)

if count_xrk_filepaths < 1:
    print('Please provide the paths to the file(s)')
else:

    if len(output_csv_filepath) == 0:
        # output file not specified - use stdout
        output_fd = sys.stdout
    else:
        # open the specified output CSV file
        output_fd = open(output_csv_filepath, mode='w', newline='')

    # Generate the CSV data list
    csv_data = []

    for f in xrk_filepaths:

        # process XRK file
        if dbg.debug_flag() and verbose_flag:
            # output any debugging information from aim_xrk parsing
            print(f'Generating log using aim_xrk from {f}')
            log = aim_xrk(f)

        else:
            # otherwise suppress stdout and stderr output
            with suppress_stdout_stderr():
                log = aim_xrk(f)

        if log == None:
            print(f'Unable to parse file {f}')
        else:
            system_distance_mi = log.metadata['Odo/System Distance (km)'] * km_to_mi
            log_date = log.metadata['Log Date']
            log_time = log.metadata['Log Time']
            system_odo_time_str = log.metadata['Odo/System Time']
            venue = log.metadata['Venue']

            # parse date/time input fields
            log_date_time = dt.datetime.strptime(log_date + ' ' + log_time, '%m/%d/%Y %H:%M:%S')

            # process lap data
            lap_times = pc.subtract(log.laps.column('end_time'), log.laps.column('start_time'))
            number_of_laps = len(log.laps) - 2 # less the out and in laps

            fastest_lap_time = pc.min(lap_times) # milliseconds
            fastest_lap = pc.index(lap_times, fastest_lap_time) # get fastest
            fastest_lap_time *= ms_to_sec # convert from milliseconds to seconds

            # process system odo time hh:mm:ss as decimal hours
            m = re.match(re_hms_pattern, system_odo_time_str)
            if m == None:
                hours = 0.0 # set hours to 0.0 if there are no matches
            else:
                hours = float(m[re_hours]) + (float(m[re_minutes]) / min_in_hr) + (float(m[re_seconds]) / sec_in_hr)

            # format CSV output fields
            csv_row = {
                common.date_time_field: log_date_time.strftime('%Y-%m-%d %H:%M:%S'),
                common.venue_field: venue,
                common.hours_field: hours,
                common.distance_field: system_distance_mi,
                common.laps_field: number_of_laps,
                common.fastest_lap_field: fastest_lap,
                common.fastest_lap_time_field: fastest_lap_time,
            }
            csv_data.append(csv_row)

            dbg.debug_print(
                f'Filepath: {f}',
                f'Log date: {log_date}',
                f'Log time: {log_time}',
                f'Venue: {venue}',
                f'Odo/System Time: {system_odo_time_str}',
                f'Odo/System Distance (miles): {system_distance_mi}',
                f'log_date_time: {log_date_time}',
                f'{csv_row}\n',
            )

    # create and write the header for the CSV file
    csv_writer = csv.DictWriter(output_fd, fieldnames=common.xrk_log_csv_fieldnames)
    csv_writer.writeheader()

    # iterate through sorted csv_data
    for csv_row in sorted(csv_data, key=lambda k: k[common.date_time_field]):
        csv_writer.writerow(csv_row)

    # close the output file if it is not stdout
    if output_fd != sys.stdout:
        output_fd.close()
