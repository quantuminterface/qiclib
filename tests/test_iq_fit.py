# Copyright © 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
# Richard Gebauer, IPE, Karlsruhe Institute of Technology
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os
import pickle

import numpy as np
import pytest

from qiclib.measurement.iq_fit import IQFit
from qiclib.measurement.iq_plot import IQData, IQPlot


@pytest.mark.skipif(
    pickle.HIGHEST_PROTOCOL < 5, reason="test-file written using pickle 5"
)
def test_sample_data():
    """
    Testing 'real-world' data that were obtained from a qubit
    """
    file = os.path.join(os.path.dirname(__file__), "data/iq_clouds_power_sweep.dat")
    plot = IQPlot()
    plot.load_data(file)

    # There are only zero states in the first data list
    fit = IQFit(
        plot.datalist[0],
        bins=int(150 * np.sqrt(len(plot.datalist[0].i_list) / 1e6)),
    )
    state_0, state_1 = fit.get_population(order=2, plot=False)
    assert state_0 == pytest.approx(1, abs=0.05)
    assert state_1 == pytest.approx(0, abs=0.05)

    # There are only one states in the second data list
    fit = IQFit(
        plot.datalist[1],
        bins=int(150 * np.sqrt(len(plot.datalist[0].i_list) / 1e6)),
    )
    state_0, state_1 = fit.get_population(order=2, plot=False)
    assert state_0 == pytest.approx(0, abs=0.05)
    assert state_1 == pytest.approx(1, abs=0.05)


def test_fit_2d_distribution():
    """
    Fit a 2D Gauss distribution using numpy's multivariante_normal 2D distribution.
    Mean value and variance should match.
    """
    # Fixed random state for reproducibility
    rand = np.random.RandomState(561876584)
    mean = (-100, 80)
    cov = [[45, 0], [0, 22]]
    dist = rand.multivariate_normal(mean, cov, size=100000)
    i_values, q_values = dist[:, 0], dist[:, 1]
    fit = IQFit(IQData(i_values, q_values), bins=50)
    popt, _, _ = fit.get_blobs(order=1, plot=False)
    _, x, y, sx, sy, theta = popt[0]
    assert x == pytest.approx(-100, abs=1)
    assert y == pytest.approx(80, abs=1)
    assert sx * sx == pytest.approx(45, abs=1)
    assert sy * sy == pytest.approx(22, abs=1)


@pytest.mark.skip(
    reason="This should theoretically work, but the estimated values are too far off"
)
def test_fit_multiple_states():
    """
    Setup two distributions (two-state system) relatively close to each other and compute
    counts. The values should be relatively close to the actual values.
    """
    # Fixed random state for reproducibility
    rand = np.random.RandomState(561876584)
    mean_1 = (-100, 80)
    mean_2 = (30, 55)
    # Assume that the cov is the same for both states
    cov = [[45, 0], [0, 22]]
    dist = np.concatenate(
        (
            rand.multivariate_normal(mean_1, cov, size=10000000),
            rand.multivariate_normal(mean_2, cov, size=100000),
        )
    )
    i_values, q_values = dist[:, 0], dist[:, 1]
    fit = IQFit(IQData(i_values, q_values), bins=80)
    popt, _, counts = fit.get_blobs(order=2, plot=False)
    # Debug prints. The first fit is pretty good but the second fit is horrible.
    # maybe this can be improved by being smarter about how data is being cropped.
    print(popt[0])
    print(popt[1])
    assert counts[0] / counts[1] == pytest.approx(100, abs=1)
