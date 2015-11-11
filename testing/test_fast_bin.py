import sys
sys.path.insert(0, '.')
import numpy as np
import pytest
from binmodule import fast_bin


@pytest.mark.parametrize('input,expected', [
    ((np.array([[1, 1], [2, 2]]), 2), np.array([[1, ], [2, ]])),
    ((np.array([[1, 1, 1, 1, 1, 1], [2, 2, 2, 2, 2, 2]]), 3),
     np.array([[1, 1], [2, 2]])),
    ((np.array([[1, 3, 1, 3], [2, 4, 2, 4]]), 2),
     np.array([[2, 2], [3, 3]])),
])
def test_fast_bin(input, expected):
    data, bin_size = input
    assert (fast_bin(data, bin_size=bin_size) == expected).all()
