'''
xrk_common.py

Common declarations for the xrk suite

'''


# Constants

# XRK session log CSV field names
date_time_field = 'Date/Time'
venue_field = 'Venue'
hours_field = 'Hours'
distance_field = 'Distance'
laps_field = 'Laps'
fastest_lap_field = 'Fastest Lap'
fastest_lap_time_field = 'Fastest Lap Time'

xrk_log_csv_fieldnames = [date_time_field, venue_field, hours_field, distance_field, laps_field, fastest_lap_field, fastest_lap_time_field]
# pandas datatypes
xrk_log_dtypes = {venue_field: 'string', hours_field: 'float64',
    distance_field: 'float64', laps_field: 'int16', fastest_lap_field: 'int16', fastest_lap_time_field: 'float64', }


# Maintenance CSV field names
date_field = 'Date'
oil_field = 'Oil'
clutch_field = 'Clutch'
notes_field = 'Notes'

maintenance_csv_fieldnames = [date_field, oil_field, clutch_field, notes_field]
# pandas datatypes
maintenance_dtypes = {oil_field: 'boolean', clutch_field: 'boolean', notes_field: 'string', }
