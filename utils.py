import functools
import numpy as np
import qrcode

_TRACE = False # Flip to True for tracing to print
DEBUG = True
MAX_CHUNK_SIZE = 45 # Maximum size to read from a file before sending
FIRST_CAMERA = 0 # This is just the first camera, if this doesn't work you can try 1 or 2 etc..
EOF = '$' # Just a random EOF character
FIRST_CHUNK_INDEX = 0 # We start indexing from 0
BREAK_KEY = ' ' # press ' ' to break the loop and exit the program prematurely

def create_qr(data):
    """
    generate qr code from binary data
    """
    qr = qrcode.QRCode(version=1, border=5)
    qr.add_data(data)
    qr.make(fit=True)
    return np.asarray(qr.make_image(fill='black', back_color='white').convert("L"))

def get_next_index(i):
    """
    Get the next index for a frame
    """
    if i < 0:
        raise ValueError(f"get_next_index only supports positive values, got: {i}")
    return (i + 1) % 10

def trace(f):
    """
    Trace decorator to trace function calls for debugging
    """
    if not _TRACE:
        return f
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        print(f.__name__, f"start")
        val = f(*args, **kwargs)
        print(f.__name__, f"end, {f'return: {val}' if val else ''}")
        return val
    return wrapper
