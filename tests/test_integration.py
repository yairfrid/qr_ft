import os
import shutil
import pytest
import cv2
import multiprocessing as mp


import qr_server
import qr_client
from utils import trace, create_qr

BLANK_QR = create_qr(b'')

class FakeVideoCapture:
    """
    A fake cv2 VideoCapture that reads an image with key img_key from img_map.
    this is used to monkeypatch capture.read() for testing (beacuse we don't want to use the camera in automated tests)
    """
    def __init__(self, img_map, img_key):
        """
        We pass the map itself instead of the key in order to always read the latest values, and not lock the values to when we create the capture
        """
        self._img_map = img_map
        self._img_key = img_key
    
    def read(self):
        if self._img_key not in self._img_map:
            return None, BLANK_QR # default to blank QR code
        return None, self._img_map[self._img_key]

class FakeImageShower:
    """
    FakeImageShower creates a tunnel between an imshow function and a fake video capture.
    when you show an image in a window, this image is saved in a virtual window.
    you can also create a fake video capture, that reads from this window (and only from that window).
    """
    def __init__(self, d):
        self._img_map = d

    @trace
    def imshow(self, window_name, img):
        """
        fakes an imshow for integration testing
        """
        self._img_map[window_name] = img
    
    def get_capture(self, window_name):
        """
        returns a video capture that always reads from the same window
        """
        return FakeVideoCapture(self._img_map, window_name)

@pytest.fixture
def input_file_path():
    """
    Fixture to automatically create and destroy input_file_path and it's directory
    """
    shutil.rmtree('/tmp/test_inp', ignore_errors=True)
    os.mkdir('/tmp/test_inp')
    yield '/tmp/test_inp/test_file.txt'
    shutil.rmtree('/tmp/test_inp', ignore_errors=True)


@pytest.fixture
def output_file_path():
    """
    Fixture to automatically create and destroy output_file_path and it's directory
    """
    shutil.rmtree('/tmp/test_out', ignore_errors=True)
    os.mkdir('/tmp/test_out')
    yield '/tmp/test_out/test_file.txt'
    shutil.rmtree('/tmp/test_out', ignore_errors=True)

def test_integration(input_file_path, output_file_path):
    """
    An integration test.
    create fake image shower with a managed dict (to synchronize between processes).
    this shower will be used to: monkey patch cv2.imshow
    when a cv2.imshow is called for a window, the img is saved in the imshower.
    a fake video capture can be created to read from this window.

    the client and the server run in seperate processes (because they block the thread they run on, and python only has one thread)
    they share the fake imshow method, and that's how we communicate the windows between the 2 processes.
    1 window is used to send the data and another is used to send the acks.
    server writes to _SERVER_WINDOW and reads from _ACK_WINDOW
    client writes to _ACK_WINDOW and reads from _SERVER_WINDOW

    we validate that the file sent has the same content as file received,
    and also that it reads from the given file path and writes to the given file path.
    """

    # Write input file
    file_data = b"test_content" * 10
    with open(input_file_path, "wb") as f:
        f.write(file_data)

    # create fake imshower and a managed dict, patch imshow to use shower.imshow, patch namedWindow to not create windows in test.
    manager = mp.Manager()
    shower = FakeImageShower(manager.dict())
    cv2.imshow = shower.imshow
    cv2.namedWindow = lambda _, __: None
    
    # create the ack window capture and pass it to send_file_from_path, run send_file_to_path in a seperate process
    ack_capture = shower.get_capture(qr_client._ACK_WINDOW)
    server_process = mp.Process(target=qr_server.send_file_from_path, args=(ack_capture, input_file_path))

    # create the server window capture and pass it to read_file_to_path, run read_file_to_path in a seperate process
    file_capture = shower.get_capture(qr_server._SERVER_WINDOW)
    client_process = mp.Process(target=qr_client.read_file_to_path, args=(file_capture, output_file_path))

    # start both processes and wait till they finish
    server_process.start() # server starts before client.
    client_process.start()
    server_process.join()
    client_process.join()

    # assert the file is written correctly by the client.
    with open(output_file_path, "rb") as output_file:
        output_contents = output_file.read()
        assert file_data == output_contents

