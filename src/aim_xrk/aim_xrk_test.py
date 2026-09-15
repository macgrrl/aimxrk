import os
import sys

import pyarrow as pa
import pyarrow.compute as pc
import pandas as pd

from libxrk import aim_xrk

# Use the Rust parser backend for ~3x faster file loading
os.environ['LIBXRK_BACKEND'] = 'rust'

# Define a context manager to suppress stdout and stderr.
class suppress_stdout_stderr(object):
    '''
    A context manager for doing a "deep suppression" of stdout and stderr in
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


# main program

if len(sys.argv) <= 1:
    print("Please provide the path to the file")
else:
    xrk_filepath = sys.argv[1]

    with suppress_stdout_stderr():
        log = aim_xrk(xrk_filepath)

    print(f'Log file_name: {log.file_name}\n')
    print(f'Channel keys\n{log.channels.keys()}\n')
    print(f'Metadata keys\n{log.metadata.keys()}\n')
    print()

    print('Metadata')
    for key in log.metadata.keys():
        print(f'{key}: {log.metadata[key]} {type(log.metadata[key])}')
    print()

    lap_times = pc.subtract(log.laps.column('end_time'), log.laps.column('start_time'))
    print(f'Lap times\n{lap_times}\n')

    number_of_laps = len(log.laps) - 2
    print(f'Number of laps: {number_of_laps}')

    fastest_lap_time = pc.min(lap_times)
    fastest_lap = pc.index(lap_times, fastest_lap_time)
    print(f'min lap time: {fastest_lap_time}, lap:{fastest_lap}\n')

    laps = log.laps
    print(f'Laps\n{laps.to_pandas()}')
