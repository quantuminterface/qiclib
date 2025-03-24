import os

import numpy as np
import pytest

from qiclib.experiment.qicode.fit_utils import compute_custom_piecewise_linear_fit


def test_compute_custom_piecewise_linear_fit():
    file = os.path.join(os.path.dirname(__file__), "data/amplitude_data.npy")
    amplitude_data = np.load(file)
    offsets = 4e-9 * np.arange(len(amplitude_data))

    fit_params = compute_custom_piecewise_linear_fit(offsets, amplitude_data)

    assert fit_params is not None, "Fit parameters should not be None."

    t1, t2, A1, A2 = fit_params

    assert t1 >= 0, "t1 (max_offset) should be >= 0"
    assert t1 <= 1024e-9, "t1 (max_offset) should be <= 1024 ns"
    assert t2 >= t1, "t2 should be >= t1"
    assert t2 <= 1024e-9, "t2 should be <= 1024 ns"

    expected_t1 = 292e-9

    assert t1 == pytest.approx(expected_t1, abs=30e-9), "t1 is not as expected."
