import base64
from time import sleep
from PIL import Image

import cv2

from utils import BREAK_KEY, DEBUG, EOF, FIRST_CHUNK_INDEX, create_qr, get_next_index, trace

_ACK_WINDOW = 'ack'

@trace
def _next_chunk(frame):
    """
    Read the next file chunk from frame, 
    if chunk is EOF, we return it's index and done=true
    if chunk does not exist, we return no data and done=false
    if chunk exists, we return it's data and index.
    """
    chunk, _, _ = cv2.QRCodeDetector().detectAndDecode(frame)

    if len(chunk) == 0:
        return None, None, False

    i = int(chunk[:1])
    chunk = chunk[1:]

    if chunk == EOF:  # If we encountered the end of transmission QR
        return i, None, True

    return i, base64.standard_b64decode(chunk), False

@trace
def _ack(i):
    """
    Show an ack for index `i`

    i integer
    """
    img = create_qr(str(i).encode())
    if DEBUG:
        Image.fromarray(img).save(f"ack_{i}.png")
    cv2.imshow(_ACK_WINDOW, img)

def _read_loop(f, cap):
    """
    This is the read loop,
    we read a frame, if it has significant data, we write it to the file.

    f file descriptor
    cap cv2.VideoCapture
    """
    next_index = FIRST_CHUNK_INDEX 

    while True:
        _, frame = cap.read()
        if frame is None:
            raise IOError("Can't read from camera")

        i, data, done = _next_chunk(frame)
        if done:
            _ack(i)
            cv2.waitKey(10000)  # Show the final ack for 10 seconds, then exit
            return

        if data is None:
            sleep(1)
            continue

        if i == next_index: # we got the correct chunk, write it and keep going
            f.write(data)
            next_index = get_next_index(next_index)

        _ack(i) # ack even if we didn't get the correct index

        # Stop the loop if BREAK_KEY is pressed, for testing purposes.
        if cv2.waitKey(1) & 0xFF == ord(BREAK_KEY):
            break
@trace
def read_file_to_path(cap, path):
    """
    Write a file from qr capture to file path

    cap cv2.VideoCapture
    path file path
    """
    with open(path, 'wb') as f:
        _read_loop(f, cap)


    cv2.destroyAllWindows()

