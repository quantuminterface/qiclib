# Copyright© 2017-2023 Quantum Interface (quantuminterface@ipe.kit.edu)
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
"""Module to analyze I/Q plane measurements."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
import scipy.optimize as opt
from scipy.special import erf


def gaussian_2d(position, amplitude, x0, y0, sigma_x, sigma_y, theta):
    (x, y) = position
    x0, y0 = float(x0), float(y0)
    a = (np.cos(theta) ** 2) / (2 * sigma_x**2) + (np.sin(theta) ** 2) / (
        2 * sigma_y**2
    )
    b = -(np.sin(2 * theta)) / (4 * sigma_x**2) + (np.sin(2 * theta)) / (4 * sigma_y**2)
    c = (np.sin(theta) ** 2) / (2 * sigma_x**2) + (np.cos(theta) ** 2) / (
        2 * sigma_y**2
    )
    g = amplitude * np.exp(
        -(a * ((x - x0) ** 2) + 2 * b * (x - x0) * (y - y0) + c * ((y - y0) ** 2))
    )
    return g.ravel()


def boltzmann_end(frequency_ghz, a, temp):
    # k_B in eV/K
    return a * np.exp(-(frequency_ghz * 1e9 * 4.13567e-15) / (temp * 8.61733e-5))


class IQFit:
    def __init__(self, iqdata, bins=400, limits=None):
        self.iqdata = iqdata  # type: IQData
        self.bins = bins
        self._set_range(limits)
        self._calculate_histogram()

        self._cache_blobs = []
        self._cache_blobs_error = []
        self._cache_blobs_count = []

    def calculate_bayessian_error(self):
        popts, _, _ = self.get_blobs(2, None, False)
        # Assume the first two blobs are |0> and |1>
        sigma_mean = np.mean([popts[0][3:5], popts[1][3:5]])
        distance = np.linalg.norm(popts[0][1:3] - popts[1][1:3])

        return 1 - erf(distance / (2 * np.sqrt(2) * sigma_mean)), distance, sigma_mean

    def get_population(self, order=4, histo=None, plot=True):
        popts, _, count = self.get_blobs(order, histo, plot=plot)
        positions_i, positions_q = popts.T[1:3]
        phases = np.angle(positions_i + 1.0j * positions_q)
        # gauss_integral = 2 * np.pi * sigma_i * sigma_q * amplitudes
        # count = 1.0 / (self.step_i * self.step_q) * gauss_integral
        total_count = np.sum(count)
        population = count[np.argsort(-phases)] / self.iqdata.count

        if plot:
            fig = plt.figure()
            ax = fig.add_subplot(111)
            ax.bar(list(range(order)), population * 100)
            ax.set_title(
                f"Qubit population (counting {total_count:.0f} of {self.iqdata.count} points)"
            )
            ax.set_xlabel("State")
            ax.set_ylabel("Population [%]")
            ax.set_ylim(0, 100)
            fig.show()
            fig.canvas.draw()
            plt.show()

        return population

    def get_plane_segmentation_count(
        self, center_list=None, order=4, histo=None, plot=True
    ):
        if center_list is None:
            popts, _, _ = self.get_blobs(order, histo, plot=False)
            center_list = np.array([(popt[1], popt[2]) for popt in popts])
            # Sort in order of decreasing phase
            pos_i, pos_q = popts.T[1:3]
            phases = np.angle(pos_i + 1j * pos_q)
            center_list = center_list[np.argsort(-phases)]
            print(center_list)
        else:
            order = len(center_list)

        def vlen(x, y):
            return (x[0] - y[0]) * (x[0] - y[0]) + (x[1] - y[1]) * (x[1] - y[1])

        # Assume same stddev for all blobs atm
        count_list = np.zeros(order)
        for iq_point in zip(self.iqdata.i_list, self.iqdata.q_list):
            min_dist = np.inf
            min_dist_idx = 0
            for state in range(order):
                dist = vlen(center_list[state], iq_point)
                if dist < min_dist:
                    min_dist = dist
                    min_dist_idx = state
            count_list[min_dist_idx] += 1

        return count_list, center_list

    def get_blobs(
        self,
        order=4,
        histo: npt.NDArray | None = None,
        crop_for_fit: bool = True,
        plot=True,
    ) -> tuple:
        """
        Returns the blob data from the given histogram.

        :param histo:
            The histogram. When omitted, the cached histogram will be used
        :param crop_for_fit:
        :param plot:
            When True, plots the histogram

        :return:
            A tuple containing the optimized blob values:
            - popt: The optimized parameters for the fitted 2D Gauss function
            - perr: The covariance matrix
            - counts: The absolute counts of qubits in the resp. states
        """
        if histo is None:
            histo = self.histogram

            if self._has_cached_blobs(order):
                return self._get_cached_blobs(order)

        if plot:
            fig = plt.figure()
            ax = fig.add_subplot(111, aspect=1.0)
            plt.imshow(
                histo.swapaxes(0, 1),
                cmap="jet",
                origin="lower",
                extent=(
                    self.i_values.min(),
                    self.i_values.max(),
                    self.q_values.min(),
                    self.q_values.max(),
                ),
            )
            fig.show()
            fig.canvas.draw()

        popts = []
        perrs = []
        counts = []
        for _ in range(order):
            histo, popt, perr, count = self._find_and_remove_blob(histo, crop_for_fit)
            popts.append(popt)
            perrs.append(perr)
            counts.append(count)

            if plot:
                print(popt)
                fit = self._gauss_to_2d(popt).swapaxes(0, 1)
                ax.contour(self.i_values, self.q_values, fit, 4, colors="w")
                fig.canvas.draw()

        if plot:
            plt.show()
            print(
                f"[{self.iqdata.label}] Remaining points: {np.sum(histo)} ({100.0 * np.sum(histo) / self.iqdata.count:.1f} %)"
            )
            print(counts, np.sum(counts))

        self._set_cached_blobs(popts, perrs, counts)
        return self._get_cached_blobs(order)

    def get_boltzmann_temperature(
        self, frequency_ghz, order=4, histo=None, population=None
    ):
        """energies in eV"""
        if population is None:
            population = self.get_population(order, histo, plot=False)

        # pylint: disable=unbalanced-tuple-unpacking
        ptopt, ptcov = opt.curve_fit(boltzmann_end, frequency_ghz, population)
        pterr = np.sqrt(np.diag(ptcov))

        # Plot
        frequencies_smooth = np.linspace(frequency_ghz.min(), frequency_ghz.max(), 100)
        ptfit = boltzmann_end(frequencies_smooth, *ptopt)

        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(frequency_ghz, population * 100, "o", label="I/Q plane measurement")
        ax.plot(frequencies_smooth, ptfit * 100, label="Maxwell-Boltzmann fit")
        ax.set_title(
            f"Temperature fit: {1e3 * ptopt[1]:.0f} +- {1e3 * pterr[1]:.0f} mK"
        )
        ax.set_xlabel("frequency [GHz]")
        ax.set_ylabel("population [%]")
        fig.show()
        fig.canvas.draw()

        return (ptopt[1], pterr[1]), ptopt, pterr

    def _calculate_histogram(self):
        result = np.histogram2d(
            self.iqdata.i_list, self.iqdata.q_list, bins=self.bins, range=self.range
        )
        self.histogram = result[0]
        self.i_values = result[1][:-1]
        self.q_values = result[2][:-1]
        self.iq_meshgrid: np.ndarray = np.meshgrid(
            self.i_values, self.q_values, indexing="ij"
        )

        # Set step size
        self.step_i = np.mean(self.i_values[1:] - self.i_values[:-1])
        self.step_q = np.mean(self.q_values[1:] - self.q_values[:-1])

    def _set_range(self, limits):
        if limits is None or len(limits) != 4:
            self.range = None
        else:
            self.range = [[limits[0], limits[1]], [limits[2], limits[3]]]

    def _find_and_remove_blob(self, histo, crop_for_fit=False):
        popt, perr = self._find_and_fit_blob(histo, crop_for_fit)
        fit = self._gauss_to_2d(popt)
        histo_new = histo - fit
        histo_new[np.where(histo_new < 0)] = 0
        # histo_new = histo.copy()
        # TODO Maybe use some relative deviation from the fit as cropping criteria?
        # TODO maybe we just subtract the fitted gauss?
        histo_new[np.where(fit >= np.max([0.5, popt[0] / 10.0]))] = 0
        count = np.sum(histo - histo_new)
        return histo_new, popt, perr, count

    def _find_and_fit_blob(self, histo, crop=False):
        pstart = self._guess_initial_fit_params(histo, self.i_values, self.q_values)
        if crop:
            guess = self._gauss_to_2d(pstart)
            histo = histo.copy()
            histo[np.where(guess < np.min([0.5, pstart[0] / 100.0]))] = 0

        # pylint: disable=unbalanced-tuple-unpacking
        popt, pcov = IQFit._fit_blob(histo, pstart, self.iq_meshgrid)
        perr = np.sqrt(np.diag(pcov))
        return popt, perr

    @staticmethod
    def _fit_blob(
        histo: np.ndarray, pstart: tuple, xy_meshgrid: np.ndarray
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Fit a 2D gaussian function to a blob of IQ data.
        The following parameters are optimized:
        - amplitude: The amplitude of the 2D Gauss
        - x0, x0: The center of the 2D Gauss
        - sigma_x, sigma_y: The standard deviation
        - theta: ?

        :param histo:
            2-dimensional histogram computed from the I and Q values
        :param pstart:
            initial guess for the fit. Format:
            (amplitude, x, y, sigma_x, sigma_y, theta)
        :param xy_meshgrid:
            The XY coordinates that the optimizer uses to search for the value

        :return:
            A tuple containing
            - popt: The optimal values for amplitude, position, standard deviation and theta
            - pcov: The covariance matrix from the fit
        """
        try:
            return opt.curve_fit(
                f=gaussian_2d,
                xdata=xy_meshgrid,
                ydata=histo.ravel(),
                p0=pstart,
                bounds=IQFit._initial_fit_params_bound(pstart),
            )
        except RuntimeError as e:
            raise RuntimeError(
                "Cannot fit blob to the provided data because the optimizer does not converge"
            ) from e

    def _gauss_to_2d(self, params):
        return gaussian_2d(self.iq_meshgrid, *params).reshape(self.iq_meshgrid[0].shape)

    @staticmethod
    def _guess_initial_fit_params(
        histo: np.ndarray, i_values: np.ndarray, q_values: np.ndarray
    ) -> tuple:
        r"""
        Guesses $x_0$, $y_0$, $\sigma_x$ and $\sigma_y$ from the given histogram and the IQ data.

        :param histo: numpy.ndarray
            The histogram computed from `i_values` and `q_values`
        :param i_values: numpy.ndarray
            The values for the in-phase components of the data
        :param q_values: numpy.ndarray
            The values for the quadrature components of the data

        :return:
            A tuple containing
            - amplitude: The maximum value of the histogram
            - x0: The i value at the maximum
            - y0: The q value at the maximum
            - sigma_x: The estimated standard derivation of the gaussian fit in x-direction
            - sigma_y: The estimated standard derivation of the gaussian fit in y-direction
            - theta: (?) 0
        """
        pstart_idx = IQFit._guess_initial_fit_params_idx(histo)
        amplitude, x0, y0, sigma_x, sigma_y, theta = pstart_idx
        # Get an x/y-value that is close to x0/y0.
        # When x0/y0 are on the left border (i.e. they are 0, choose the value to the right of x0 and y0.)
        # Otherwise, choose a value to the left.
        close_x = x0 + 1 if x0 == 0 else x0 - 1
        close_y = y0 + 1 if y0 == 0 else y0 - 1
        # Heuristic (?) to scale sigma_y to a more realistic value.
        sigma_x *= np.abs(i_values[close_x] - i_values[x0])
        sigma_y *= np.abs(i_values[close_y] - i_values[x0])
        x0, y0 = i_values[x0], q_values[y0]
        return amplitude, x0, y0, sigma_x, sigma_y, theta

    @staticmethod
    def _guess_initial_fit_params_idx(histo: np.ndarray) -> tuple:
        r"""
        Guesses $x_0$, $y_0$, $\sigma_x$ and $\sigma_y$ from the given histogram as an initial fit.
        $x_0$ and $y_0$ signify indices into the histogram and $\sigma_x$ as well as $\sigma_y$ are computed
        from the histogram.

        :param histo: numpy.ndarray
            The histogram with the blob

        :param:
            A tuple containing
            - amplitude: The amplitude of the maximum value
            - x0: The x-position using the max amplitude
            - y0: The y-position using the max amplitude
            - sigma_x: The standard deviation in x-direction using the max amplitude
            - sigma_y: The standard deviation in y-direction using the max amplitude
            - theta: (?) 0
        """
        (x0, y0), amplitude = IQFit._find_maximum_2d(histo)
        # fwhm: full width half maximum
        # This is the width, centered around the maximum of the histogram, at which the amplitude has dropped to
        # half of the maximum value.
        fwhm_x = 2 * np.min(np.abs(np.argwhere(histo[:, y0] <= amplitude / 2.0) - x0))
        fwhm_y = 2 * np.min(np.abs(np.argwhere(histo[x0, :] <= amplitude / 2.0) - y0))
        sigma_x = IQFit._convert_fwhm_to_sigma(fwhm_x)
        sigma_y = IQFit._convert_fwhm_to_sigma(fwhm_y)
        theta = 0
        return amplitude, x0, y0, sigma_x, sigma_y, theta

    @staticmethod
    def _initial_fit_params_bound(params):
        amplitude, x0, y0, sigma_x, sigma_y, _ = params
        return (
            [
                amplitude * 0.5,
                x0 - sigma_x,
                y0 - sigma_y,
                sigma_x * 0.2,
                sigma_y * 0.2,
                -np.pi,
            ],
            [
                amplitude * 2.0,
                x0 + sigma_x,
                y0 + sigma_y,
                sigma_x * 5.0,
                sigma_y * 5.0,
                +np.pi,
            ],
        )

    @staticmethod
    def _find_maximum_2d(histo: np.ndarray):
        """
        Returns the index and maximum value of a given 2 D array:
        >>> arr = np.array([[0, 2], [1, -1]])
        >>> IQFit._find_maximum_2d(arr)
        ((0, 1), 2)

        :param histo: numpy.ndarray
            A 2-dimensional numpy array

        :return:
            A tuple where the first element is the index and the second element is the value of the maximum.
            The index is itself also a tuple of x and y values.
        """
        idx = np.unravel_index(histo.argmax(), histo.shape)
        val = histo[idx]
        return idx, val

    def _has_cached_blobs(self, order):
        return (
            np.min(
                [
                    len(self._cache_blobs),
                    len(self._cache_blobs_error),
                    len(self._cache_blobs_count),
                ]
            )
            >= order
        )

    def _get_cached_blobs(self, order):
        return (
            self._cache_blobs[0:order],
            self._cache_blobs_error[0:order],
            self._cache_blobs_count[0:order],
        )

    def _set_cached_blobs(self, popts, perrs, counts):
        self._cache_blobs = np.atleast_1d(popts)
        self._cache_blobs_error = np.atleast_1d(perrs)
        self._cache_blobs_count = np.atleast_1d(counts)

    @staticmethod
    def _convert_fwhm_to_sigma(fwhm: float) -> float:
        """
        Convert full width at half maximum of a distribution to the standard deviation
        using the assumption that the distribution is a normal distribution.

        See https://en.wikipedia.org/wiki/Full_width_at_half_maximum

        :param fwmh: float
            The FWHM value

        :return:
        The standard deviation
        """
        return fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))

    @staticmethod
    def _get_gauss_amplitude(histo, edges_x, edges_y):
        pstart = IQFit._guess_initial_fit_params(histo, edges_x, edges_y)
        xy_meshgrid = np.meshgrid(edges_x[:-1], edges_y[:-1], indexing="ij")
        # pylint: disable=unbalanced-tuple-unpacking
        popt, pcov = IQFit._fit_blob(histo, pstart, xy_meshgrid)
        perr = np.sqrt(np.diag(pcov))
        return popt[0], perr[0]
