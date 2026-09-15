'''
frc_debug.py

Module with debugging assistance functions
'''

# Globals
_debug_flag = False


# Debugging

'''
Set debug mode on
'''
def debug_on():
    global _debug_flag
    _debug_flag = True


'''
Set debug mode off
'''
def debug_off():
    global _debug_flag
    _debug_flag = False


'''
Toggle debug mode
'''
def toggle_debug():
    global _debug_flag
    _debug_flag = not _debug_flag


'''
Set debug mode off
'''
def set_debug(d):
    global _debug_flag
    _debug_flag = d


'''
Returns debug state
'''
def debug_flag():
    global _debug_flag
    return _debug_flag


'''
Debug print
Iterates through string parameters and prints them if debug_flag is True
'''
def debug_print(*strings):
    global _debug_flag
    if _debug_flag:
        for s in strings:
            print(s)
