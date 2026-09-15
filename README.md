# Overview
Python scripts to process AIM XRK files (e.g. from MyChron) and generate session log CSV file, and use this session file along with a maintenance log CSV file to generate a HTML report for maintenance, as well as output tables of the maintenance log, session day log, and full session log.

Uses the [m3rlin45 / libxrk](https://github.com/m3rlin45/libxrk) Python / Rust library to read and process XRK files.

# File Structures
## CSV Files
### Session Log
#### Fields
- Date/Time: Date and time of session, `[YYYY-MM-DD hh:mm:ss]`
- Venue: location of session
- Hours: Cumulative session times, in hours
- Distance: Cumulative session distance, in miles
- Laps: Number of full laps
- Fastest Lap: Fastest lap number, 1..n, 1 is first full lap, n is last
- Fastest Lap Time: Fastest lap time, in seconds

#### Notes
Generated from XRK datafiles
Sorted in ascending date order by xrkcsv_session.py

### Maintenance Log
#### Fields
- Date: Date (usually for session), formatted as `YYYY-MM-DD`
- Oil: Oil change: Boolean, X for true, blank for false
- Clutch: Clutch change: Boolean, X for true, blank for false
- Notes: String

#### Notes
Should be sorted in ascending order of Date, however session_html.py will perform a sort to ensure that.

# Scripts
## xrkcsv_session.py
Generates Session Log file from AIM XRK datafiles.

usage: `xrkcsv_session.py [-h] [-d] [-v] [-o OUTPUT] [--version] ...`

See script help output for more details, `xrkcsv_session.py -h`

## session_html.py
Generates HTML file from Session Log data and Maintenance Log Data.

usage: `session_html.py [-h] [-d] [-v] [-o OUTPUT] [--version] session_csv_filepath maint_csv_filepath`

See script help output for more details, `session_html.py -h`

### HTML Output
Report file with following structure
- First and last session dates
- Total hours and distance
- Times since last oil change and clutch maintenance
- Distances since last oil change and clutch maintenance
- Maintenance log (4 columns)
- Day log with the following columns, in descending order of Date
    - Date
    - Hours: cumulative hours
    - Distance: cumulative distance in miles
    - Delta Hours: Time difference from the previous session
    - Delta Distance: Distance difference from the previous session
- Session Log (CSV file columns) in descending order of Date/Time
- Input File paths
- Data/Time report generated
