from utils import get_next_index, create_qr
import cv2
import pytest
import random


def test_get_next_index():
    assert get_next_index(0) == 1
    assert get_next_index(1) == 2
    assert get_next_index(9) == 0
    assert get_next_index(99) == 0
    assert get_next_index(51) == 2

    with pytest.raises(ValueError):
        assert get_next_index(-1) == 0
        assert get_next_index(-100) == 0
        assert get_next_index(-42) == 0

def test_get_index_less_than_10():
    for _ in range(100):
        random_value = random.randint(1, 1000)
        assert 0 <= get_next_index(random_value) < 10

def test_create_qr():
    data = b'abcd' * 10
    qr = create_qr(data)
    decoded_data = cv2.QRCodeDetector().detectAndDecode(qr)
    assert data.decode() == decoded_data[0]
    
