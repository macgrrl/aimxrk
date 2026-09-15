'''
Outputs
- Log date and time
- System odometer information (time and distance in miles)

Usage:
aim_xrk_odo.py filename.xrk

'''

# Use the Rust parser backend for ~3x faster file loading
import os
import sys

from libxrk import aim_xrk

os.environ["LIBXRK_BACKEND"] = "rust"

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

# constants
# number of miles in a kilometre
km_to_mi = 0.6213712

# main program

if len(sys.argv) <= 1:
    print("Please provide the path to the file")
else:        
    xrk_filepath = sys.argv[1]

    with suppress_stdout_stderr():
        log = aim_xrk(xrk_filepath)
    
    if log == None:
        print("Unable to parse file " + xrk_filepath)
    else:
        system_distance_mi = log.metadata['Odo/System Distance (km)'] * km_to_mi

        print("Filepath: " + xrk_filepath)
        print()

        print("Log date: " + log.metadata['Log Date'])
        print("Log time: " + log.metadata['Log Time'])
        print("Venue:" + log.metadata['Venue'])
        print()
        
        print(f"Odo/System Time: {log.metadata['Odo/System Time']}")
        print(f"Odo/System Distance (miles): {system_distance_mi}")
