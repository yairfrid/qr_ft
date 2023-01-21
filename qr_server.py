import base64
from time import sleep

import cv2

from utils import (
    BREAK_KEY,
    EOF,
    FIRST_CHUNK_INDEX,
    MAX_CHUNK_SIZE,
    create_qr,
    get_next_index,
    trace,
)

_SERVER_WINDOW = "server"

def _qr_generator(path):
    """
    iterate over a file and produce qr for each chunk
    """

    i = FIRST_CHUNK_INDEX

    # generate qrs for file data in chunks
    with open(path, 'rb') as f:
        while data := f.read(MAX_CHUNK_SIZE):
            chunk_to_send = str(i).encode() + base64.standard_b64encode(data)
            qred_chunk = create_qr(chunk_to_send)
            yield i, qred_chunk
            i = get_next_index(i)

    img = create_qr(str(i).encode() + EOF.encode())
    yield i, img

@trace
def _did_ack(cap, index):
    """
    read ack from camera, return true if acked
    """
    _, img = cap.read()
    data, _, _ = cv2.QRCodeDetector().detectAndDecode(img)
    return len(data) != 0 and int(data) == index

@trace
def send_file_from_path(cap, path):
    """
    Sends a file `path` over QR

    cap: cv2.VideoCapture
    path: file path to send
    """
    cv2.namedWindow(_SERVER_WINDOW, cv2.WINDOW_FULLSCREEN)

    # send file chunk by chunk
    for i, img in _qr_generator(path):
        cv2.imshow(_SERVER_WINDOW, img)
        while True:
            # if we dont wait we will exit too soon, we will not wait when BREAK_KEY is pressed (for testing)
            if cv2.waitKey(1) & 0xFF == ord(BREAK_KEY):
                break

            if _did_ack(cap, i):
                break
            sleep(1)

    cv2.destroyAllWindows()

