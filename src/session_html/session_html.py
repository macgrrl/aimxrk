'''
session_html.py

Input:
    arg 1: XRK log CSV, produced by xrkcsv_session.py
    arg 2: maintenance CSV, self maintained

Input file structures are specified in README.md


Output:
    See README.md

Usage:
session_html.py [-h, --help] [-o, --output filename.html] [-d, --debug [-v, --verbose]] session_data.csv maint.csv

'''

# import modules
import sys
import argparse
import datetime as dt

import pandas as pd

import jinja2

import frc_debug as dbg
import xrk_common as common


# constants
app_name = 'session_html.py' # application name
app_version = '1.0' # application version
app_description = 'Outputs HTML report from XRK-derived Session data and Maintenance log CSVs'

# filepath argument names
session_csv_filepath_arg = 'session_csv_filepath'
maint_csv_filepath_arg = 'maint_csv_filepath'

log_template_filepath = 'log_template.html'

# table fields
# daily log
delta_hours_field = 'Delta Hours'
delta_distance_field = 'Delta Distance'

# indices to fields
hours_field_index = 0
distance_field_index = 1
delta_hours_field_index = 2
delta_distance_field_index = 3


# functions

'''
compute the time since maintenance was performed
input:
- maint: maint_data DataFrame
- session: session_data DataFrame
- maint_field: maintenance field name string
- last_time: last day time float
returns tuple:
- date the maintenance was performed (string formatted as %Y-%m-%d)
- number of hours since maintenance (2 decimal places, string)
'''
def time_since_last_maintenance(maint, session, maint_field, last_time):
    # maintenance DataFrame for which maint_field is True
    # - loc: all items for which maint_field is True
    maint_df = maint.loc[maint[maint_field]]

    if len(maint_df) > 0:
        # at least one row in maintenance DataFrame

        # get last maintenance datestamp
        # - tail(1): last maintenance row
        # - index[0]: index item
        last_maintenance_ds = maint_df.tail(1).index[0]

        # set time to 23:59, so we catch all events during the day
        last_maintenance_ds = pd.Timestamp(ts_input=last_maintenance_ds.strftime('%Y-%m-%d 23:59'))

        # get number of hours at session before last maintenance, i.e. last session up to and including that date
        change_hours = session.loc[session.index <= last_maintenance_ds].tail(1)[common.hours_field].values[0]

        # format last maintenance date
        maint_date = last_maintenance_ds.strftime('%Y-%m-%d')

        # compute hours since maintenance and format to 2 decimal places
        hours_since = '{:.2f}'.format(last_time - change_hours)
    else:
        # return N/A for maintenance date and hours since
        maint_date = 'N/A'
        hours_since = 'N/A'

    # return tuple of formatted strings for last maintenance date and hours since last maintenance
    return (maint_date, hours_since)


# main program

# parse options & arguments
parser = argparse.ArgumentParser(prog=app_name, description=app_description)

parser.add_argument('-d', '--debug', action='store_true',
                    help='turn on debugging')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='enable verbose mode')
parser.add_argument('-o', '--output', action='store', default='',
                    help='output HTML filepath')

parser.add_argument('--version', action='version', version='%(prog)s ' + app_version)

parser.add_argument(session_csv_filepath_arg, help='Session CSV filepath')
parser.add_argument(maint_csv_filepath_arg, help='Maintenance CSV filepath')

arguments_namespace, passed_args = parser.parse_known_args()
arguments_dict = vars(arguments_namespace)

dbg.set_debug(arguments_dict['debug'])
verbose_flag = arguments_dict['verbose']
output_html_filepath = arguments_dict['output']
session_filepath = arguments_dict[session_csv_filepath_arg]
maint_filepath = arguments_dict[maint_csv_filepath_arg]

dbg.debug_print(
    f'session_filepath: {session_filepath}',
    f'maint_filepath: {maint_filepath}',
    f'output_html_filepath: {output_html_filepath}',
    ''
)

# read input data into DataFrames
session_data = pd.read_csv(session_filepath,
                           dtype=common.xrk_log_dtypes,
                           parse_dates=[0],
                           date_format={0: '%Y-%m-%d %H:%M:%S'},
                           index_col=0,
                           na_filter=False,
                           )
# Note: session data is generated in ascending date order

maint_data = pd.read_csv(maint_filepath,
                         dtype=common.maintenance_dtypes,
                         true_values=['X'], false_values=[''],
                         parse_dates=[0],
                         date_format={0: '%Y-%m-%d'},
                         index_col=0,
                         na_filter=False,
                         )

# omit sessions where number of laps is -1
session_data.drop(session_data.loc[session_data[common.laps_field] == -1].index, inplace=True)

# specify number of decimal places for output
session_data = session_data.round({common.hours_field: 2, common.distance_field: 2, common.fastest_lap_time_field: 2,})

# ensure maintenance data is sorted in index (date) default ascending order
maint_data.sort_index(inplace=True)

# generate daily log

# get: extracts duration and distance columns
day_data = session_data.get([common.hours_field, common.distance_field])

# replace index with YYYY-MM-DD
day_data.index = day_data.index.strftime('%Y-%m-%d')

# change index name
day_data.index.name = 'Date'

# groupby & lambda: group by session day
# tail: gets last session for the day
day_data = day_data\
    .groupby(lambda x: x)\
    .tail(1)

# add delta columns
# delta duration
day_data[delta_hours_field] = day_data.get([common.hours_field]).diff()
# copy the duration at index 0 (first row) to the delta duration
day_data.iat[0, delta_hours_field_index] = day_data.iat[0, hours_field_index]

# delta distance
day_data[delta_distance_field] = day_data.get([common.distance_field]).diff()
# copy the distance at index 0 (first row) to the delta distance
day_data.iat[0, delta_distance_field_index] = day_data.iat[0, distance_field_index]

# specify number of decimal places for output
day_data = day_data.round({delta_hours_field: 2, delta_distance_field: 2, })

# first day
first_day = day_data.head(1)

# last day
last_day = day_data.tail(1)
last_day_hours = last_day[common.hours_field].values[0]

# compute number of hours since oil change
(oil_change_date, hours_since_oil_change) = time_since_last_maintenance(maint_data, session_data, common.oil_field, last_day_hours)

dbg.debug_print(f'Oil Change Date:{oil_change_date}, Hours since:{hours_since_oil_change}')

# compute number of hours since clutch maintenance
(clutch_maint_date, hours_since_clutch_maint) = time_since_last_maintenance(maint_data, session_data, common.clutch_field, last_day_hours)

dbg.debug_print(f'Clutch Maintenance Date:{clutch_maint_date}, Hours since:{hours_since_clutch_maint}')

# in-place sort descending for output (latest first)
session_data.sort_index(ascending=False, inplace=True)
day_data.sort_index(ascending=False, inplace=True)

dbg.debug_print(
    '\n*** session_data',
    session_data, type(session_data), session_data.dtypes,
    '\n*** maint_data',
    maint_data, type(maint_data), maint_data.dtypes,
    '\n*** day_data',
    day_data, type(day_data), day_data.dtypes,
    '\n*** first_day',
    first_day, type(first_day), first_day.dtypes,
    '\n*** last_day',
    last_day, type(last_day), last_day.dtypes,
)

# generate HTML

# open output file or use stdout
if len(output_html_filepath) == 0:
    # output file not specified - use stdout
    output_fd = sys.stdout
else:
    # open the specified output HTML file
    output_fd = open(output_html_filepath, mode='w')

env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates/'))
html_template = env.get_template(log_template_filepath)

# generate html from dataframes
session_table_html = session_data.to_html()
maint_table_html = maint_data.to_html()
day_table_html = day_data.to_html()

context = {
    'from_date': first_day.index[0],
    'to_date': last_day.index[0],
    'total_hours': last_day.iat[0, hours_field_index],
    'total_distance': last_day.iat[0, distance_field_index],
    'oil_change_date': oil_change_date,
    'hours_since_oil_change': hours_since_oil_change,
    'clutch_maint_date': clutch_maint_date,
    'hours_since_clutch_maint': hours_since_clutch_maint,
    'session_log': session_filepath,
    'maint_log': maint_filepath,
    'session_table_html': session_table_html,
    'maint_table_html': maint_table_html,
    'day_table_html': day_table_html,
    'log_generated_at': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}
html_output = html_template.render(context)

output_fd.write(html_output)

# close the output file if it is not stdout
if output_fd != sys.stdout:
    output_fd.close()
