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
"""File containing the IQPlot class"""

from __future__ import annotations

import os
import pickle

import ipywidgets as widgets
import matplotlib.colors as pltcol
import matplotlib.pyplot as plt
import numpy
from ipywidgets import interact

from qiclib.measurement.iq_fit import IQFit
from qiclib.packages.qkit_polyfill import QKIT_ENABLED, DateTimeGenerator


class IQPlot:
    colorlist: tuple[str] = ("b", "r", "g", "c", "m", "k")

    def __init__(self, iq_data=None):
        """
        :param iq_data: Data object holding IQ data to add
        :type iq_data: IQData
        """
        self.reset()
        if iq_data is not None:
            self.add(iq_data)

    def add(self, iq_data):
        """Adds a new IQData object to an existing IQPlot.

        :param iq_data: Data object holding IQ data to add
        :type iq_data: IQData
        """
        self._update_iq_data(iq_data)
        self.datalist.append(iq_data)
        maxvalue = numpy.amax(numpy.abs(iq_data.i_list + 1j * iq_data.q_list)) * 1.1
        self.maxvalue = numpy.max([self.maxvalue, maxvalue])

    def plot_points(self):
        """Plots the IQ datasets as points."""
        if len(self.datalist) == 0:
            raise Warning("To draw an IQ scatter graph some data has to be added.")
        fig = plt.figure()
        axis = fig.add_subplot(111, aspect="equal")

        for i, iqdata in enumerate(self.datalist):
            self._add_iq_cloud(
                axis, iqdata, color=IQPlot.colorlist[i % len(IQPlot.colorlist)]
            )

        axis.set_xlim(-self.maxvalue, self.maxvalue)
        axis.set_ylim(-self.maxvalue, self.maxvalue)
        plt.grid(True)
        plt.legend(loc="upper left")
        plt.xlabel("I")
        plt.ylabel("Q")
        plt.show()

    def plot_slider(self, maxlim=False):
        """Plots one dataset but presents a slider to go through the different ones."""
        if len(self.datalist) == 0:
            raise Warning("To draw an IQ graph some data has to be added.")

        def plot_func(idx):
            x = self.datalist[idx].i_list
            y = self.datalist[idx].q_list

            fig = plt.figure()
            axis = fig.add_subplot(111, aspect="equal")
            axis.plot(x, y, "x")
            plt.title(self.datalist[idx].label)
            plt.grid(True)
            plt.xlabel("I")
            plt.ylabel("Q")

            if maxlim:
                axis.set_xlim(-self.maxvalue, self.maxvalue)
                axis.set_ylim(-self.maxvalue, self.maxvalue)

            plt.show()

        interact(
            plot_func,
            idx=widgets.IntSlider(value=0, min=0, max=len(self.datalist) - 1, step=1),
        )

    def plot_segmented_population(
        self, center_list=None, order=4, bins=400, limits=None
    ):
        """Plots the population of the states determined by segmentation as bar plot."""
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw population plots some data has to be added.")

        fig = plt.figure()
        for i, iqdata in enumerate(self.datalist):
            # If center_list is None in the first run it will be determined by IQFit and then saved for reuse
            count_list, center_list = IQFit(
                iqdata, bins, limits
            ).get_plane_segmentation_count(center_list, order=order, plot=False)
            population = count_list / iqdata.count

            ax = fig.add_subplot((nplots + 1) / 2, 2, i + 1)
            ax.bar(list(range(order)), population * 100)
            ax.set_ylim(0, 100)

            plt.title(iqdata.label)
            plt.xlabel("State")
            plt.ylabel("Population [%]")

        plt.tight_layout()
        plt.show()

    def plot_population(self, order=4, bins=400, limits=None):
        """Plots the population of the states as bar plot."""
        if bins <= 0:
            raise ValueError(f"Bins must be positive (is: {bins})")
        if order < 1:
            raise ValueError(f"Order must at least be one (is: {order})")
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw population plots some data has to be added.")

        fig = plt.figure()
        for i, iqdata in enumerate(self.datalist):
            population = IQFit(iqdata, bins, limits).get_population(
                order=order, plot=False
            )

            ax = fig.add_subplot((nplots + 1) / 2, 2, i + 1)
            ax.bar(list(range(order)), population * 100)
            ax.set_ylim(0, 100)

            plt.title(
                f"{iqdata.label} ({numpy.sum(population) * 100:.1f}% of all points)"
            )
            plt.xlabel("State")
            plt.ylabel("Population [%]")

        plt.tight_layout()
        plt.show()

    def plot(
        self, state_cfg=None, limits=None, cmap="jet", scaling=None, cmin=1, bins=400
    ):
        """Plots the IQ datasets as one histogram per set."""
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw an IQ plot some data has to be added.")

        def get_xy(iqdata):
            return (iqdata.i_list, iqdata.q_list)

        lists, data_limits, _ = self._analyze_data_for_plot(get_xy)

        if limits is None or limits is True:
            limits = data_limits
        elif limits is False:
            limits = None
        elif len(limits) != 4:
            raise Warning(
                "limits need to have four components (I min & max, Q min & max)"
            )

        def plot_extra(fig, ax, hist, edges_x, edges_y):
            if state_cfg is not None:
                ax.plot(
                    edges_x,
                    (state_cfg[0] * edges_x + state_cfg[2]) / (-state_cfg[1]),
                    "-r",
                )

        self._plot_2d_histogram(
            lists,
            int((nplots + 1) / 2),
            2,
            limits,
            "I",
            "Q",
            aspect=1.0,
            cmap=cmap,
            scaling=scaling,
            cmin=cmin,
            bins=bins,
            plot_extra=plot_extra,
        )

    def plot_single_to_file(
        self,
        filename,
        dataset=0,
        state_cfg=None,
        limits=None,
        cmap="jet",
        scaling=None,
        cmin=1,
        bins=400,
        vmax=None,
    ):
        """Plots a single dataset without axis to file."""
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw an IQ plot some data has to be added.")

        def get_xy(iqdata):
            return (iqdata.i_list, iqdata.q_list)

        lists, data_limits, _ = self._analyze_data_for_plot(
            get_xy, [self.datalist[dataset]]
        )

        if limits is None or limits is True:
            limits = data_limits
        elif limits is False:
            limits = None
        elif len(limits) != 4:
            raise Warning(
                "limits need to have four components (I min & max, Q min & max)"
            )

        if scaling is not None:
            norm = {"log": pltcol.LogNorm(), "linear": pltcol.Normalize()}.get(scaling)
            if norm is None:
                raise Warning(
                    "Parameter scaling not understood. Possible values: log | linear"
                )
        else:
            norm = None

        if limits is None:
            limit_range = None
        else:
            limit_range = [[limits[0], limits[1]], [limits[2], limits[3]]]

        def plot_extra(fig, ax, hist, edges_x, edges_y):
            if state_cfg is not None:
                ax.plot(
                    edges_x,
                    (state_cfg[0] * edges_x + state_cfg[2]) / (-state_cfg[1]),
                    "-r",
                )

        xs, ys, _ = next(zip(*lists))

        def single_plot(fig, ax):
            hist, _, _ = self._plot_single(
                fig,
                ax,
                xs,
                ys,
                bins,
                cmap,
                norm,
                cmin,
                limit_range,
                plot_extra=plot_extra,
                axis=False,
                vmax=vmax,
            )
            return numpy.nanmin(hist), numpy.nanmax(hist)

        # return colormap limits
        return (
            self._plot_to_file(
                filename, single_plot, figsize=(bins / 100.0, bins / 100.0)
            ),
            limits,
        )

    def plot_polar_single_to_file(
        self,
        filename,
        dataset=0,
        limits=None,
        cmap="jet",
        scaling=None,
        cmin=1,
        bins=400,
        vmax=None,
    ):
        """Plots a single dataset in polar representation without axis to file."""
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw an IQ plot some data has to be added.")

        def get_xy(iqdata):
            phases = numpy.angle(iqdata.i_list + 1j * iqdata.q_list)
            amplitudes = numpy.abs(iqdata.i_list + 1j * iqdata.q_list)
            return (phases, amplitudes)

        lists, data_limits, means = self._analyze_data_for_plot(
            get_xy, [self.datalist[dataset]]
        )

        if limits is None or limits is True:
            limits = data_limits
        elif limits is False:
            limits = None
        elif len(limits) == 4:
            limits = (limits[2], limits[3], limits[0], limits[1])
        else:
            raise Warning(
                "limits need to have four components (I min & max, Q min & max)"
            )

        if scaling is not None:
            norm = {"log": pltcol.LogNorm(), "linear": pltcol.Normalize()}.get(scaling)
            if norm is None:
                raise Warning(
                    "Parameter scaling not understood. Possible values: log | linear"
                )
        else:
            norm = None

        if limits is None:
            limit_range = None
        else:
            limit_range = [[limits[0], limits[1]], [limits[2], limits[3]]]

        xs, ys, _ = next(zip(*lists))

        # Keep correct aspect ratio
        bins_r = bins * means[1] * (limits[1] - limits[0]) / (limits[3] - limits[2])
        figsize = (bins / 100.0, bins_r / 100.0)  # / means[1])

        def single_plot(fig, ax):
            hist, _, _ = self._plot_single(
                fig,
                ax,
                xs,
                ys,
                [bins, bins_r],
                cmap,
                norm,
                cmin,
                limit_range,
                axis=False,
                vmax=vmax,
            )
            return numpy.nanmin(hist), numpy.nanmax(hist)

        # return colormap limits
        return self._plot_to_file(filename, single_plot, figsize=figsize), limits

    def plot_polar(self, limits=None, cmap="jet", scaling=None, cmin=1, bins=400):
        """Plots the IQ datasets as one histogram per set in polar coordinates."""
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw an IQ polar plot some data has to be added.")

        def get_xy(iqdata):
            phases = numpy.angle(iqdata.i_list + 1j * iqdata.q_list)
            amplitudes = numpy.abs(iqdata.i_list + 1j * iqdata.q_list)
            return (phases, amplitudes)

        lists, data_limits, means = self._analyze_data_for_plot(get_xy)

        if limits is None:
            limits = data_limits
        elif len(limits) != 4:
            raise Warning(
                "limits need to have four components (amplitude min & max, phase min & max)"
            )
        else:
            # Rearrange:
            # amplitude is given first but is y axis
            limits = (limits[2], limits[3], limits[0], limits[1])

        self._plot_2d_histogram(
            lists,
            nplots,
            1,
            limits,
            "Phase",
            "Amplitude",
            aspect=1.0 / means[1],
            cmap=cmap,
            scaling=scaling,
            cmin=cmin,
            bins=bins,
        )

    def plot_phase_histogram(self, amplitude, limits=None, bins=400):
        nplots = len(self.datalist)
        if nplots == 0:
            raise Warning("To draw phase histogram plots some data has to be added.")

        def get_xy(iqdata):
            phases = numpy.angle(iqdata.i_list + 1j * iqdata.q_list)
            amplitudes = numpy.abs(iqdata.i_list + 1j * iqdata.q_list)
            return (phases, amplitudes)

        lists, data_limits, _ = self._analyze_data_for_plot(get_xy)

        if limits is None:
            limits = data_limits
        elif len(limits) != 4:
            raise Warning(
                "limits need to have four components (amplitude min & max, phase min & max)"
            )
        else:
            # Rearrange:
            # amplitude is given first but is y axis
            limits = (limits[2], limits[3], limits[0], limits[1])

        if amplitude < limits[2] or amplitude > limits[3]:
            print(limits)
            raise Warning(
                "Amplitude has to be within the given limits! (maybe of data?)"
            )

        fig = plt.figure()
        for i, (phases, amplitudes, label) in enumerate(zip(*lists)):
            hist, edges_pha, edges_amp = numpy.histogram2d(
                phases,
                amplitudes,
                bins=bins,
                range=[[limits[0], limits[1]], [limits[2], limits[3]]],
            )

            amp_index = numpy.abs(edges_amp - amplitude).argmin()
            hist_phase = hist[:, amp_index]

            ax = fig.add_subplot(nplots, 1, i + 1)
            ax.plot(edges_pha[:-1], hist_phase)

            plt.title(label)
            plt.xlabel("Phase")
            plt.ylabel("Count")

        plt.tight_layout()
        plt.show()

    def save_data(self, filename=None):
        if filename is None and not QKIT_ENABLED:
            raise Warning("Filename has to be given to store IQPlot data.")
        if filename is None:
            filename = DateTimeGenerator().new_filename("iq-plot")["_filepath"]
            filename = filename[:-2] + "dat"
        elif not os.path.isabs(filename):
            filename = DateTimeGenerator().new_filename(filename)["_filepath"]
            filename = filename[:-2] + "dat"

        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))

        with open(filename, "wb") as output:
            pickle.dump(self.datalist, output, -1)
        print(f"Data saved in: {filename}")

    def load_data(self, filename=None):
        if filename is None:
            raise Warning("Filename has to be given to load IQPlot data.")
        with open(filename, "rb") as fopen:
            datalist = pickle.load(fopen)
            self.reset()
            for iqdata in datalist:
                self.add(iqdata)

    def reset(self):
        self.maxvalue = 0
        self.datalist = []  # type: list[IQData]

    def _add_iq_cloud(self, axis, iq_data, color=None):
        """Adds an IQData object as scatter cloud to the plot.

        :param axis: Axis object to add the cloud to
        :type axis: matplotlib.axes.Axes
        :param iq_data: Data object holding IQ data to add to plot
        :type iq_data: IQData
        :param color: The color of the plot.
        :type color: str
        """
        axis.scatter(
            iq_data.i_list, iq_data.q_list, c=color, marker="x", label=iq_data.label
        )
        axis.add_artist(plt.Circle((0, 0), iq_data.amplitude, color=color, fill=False))
        plt.arrow(
            0,
            0,
            iq_data.amplitude * numpy.cos(iq_data.phase),
            iq_data.amplitude * numpy.sin(iq_data.phase),
            fc=color,
            ec=color,
        )

    def _analyze_data_for_plot(self, get_xy, datalist=None):
        """Returns data that can be plotted in histograms.

        :param get_xy: function that gets IQData object and returns x and y arrays as tuple.

        :return:
            (xs_list, ys_list, label_list), (x_min, x_max, y_min, y_max), (x_mean, y_mean)
        """
        if datalist is None:
            datalist = self.datalist

        x_min = numpy.inf
        x_max = -numpy.inf
        y_min = numpy.inf
        y_max = -numpy.inf

        x_mean = 0
        y_mean = 0

        xs_list = []
        ys_list = []
        label_list = []

        for iqdata in datalist:
            xs, ys = get_xy(iqdata)

            x_min = numpy.min([x_min, numpy.min(xs)])
            x_max = numpy.max([x_max, numpy.max(xs)])
            y_min = numpy.min([y_min, numpy.min(ys)])
            y_max = numpy.max([y_max, numpy.max(ys)])

            x_mean += numpy.mean(xs)
            y_mean += numpy.mean(ys)

            xs_list.append(xs)
            ys_list.append(ys)
            label_list.append(iqdata.label)

        x_mean = x_mean * 1.0 / len(self.datalist)
        y_mean = y_mean * 1.0 / len(self.datalist)

        return (
            (xs_list, ys_list, label_list),
            (x_min, x_max, y_min, y_max),
            (x_mean, y_mean),
        )

    def _plot_2d_histogram(
        self,
        data_lists,
        rows: int,
        cols: int,
        limits: tuple[float, float, float, float],
        xlabel: str,
        ylabel: str,
        aspect: float = 1.0,
        cmap: str = "jet",
        scaling: str | None = None,
        cmin: int = 1,
        bins: int = 400,
        plot_extra=None,
    ):
        """Plots a 2D histogram with the given Parameters

        :param data_lists:
            A tuple with three elements holding lists for x and y values and for the labels
        :type data_lists: Tuple[(float[], float[], float[])]
        :param rows:
            The number of rows the plot will have
        :param cols:
            The number of columns the plot will have
        :param limits:
            The limits of the plot (xmin, xmax, ymin, ymax)
        :param xlabel:
            Label of the x axis
        :param ylabel:
            Lavbel of the y axis
        :param aspect:
            The aspect ratio of x and y axis (the default is 1.0, which means equal spacing)
        :param cmap:
            Specification of the color map to use
        :param scaling:
            If the colormap values should be spaced the same across different plots and if the spacing should be
            'linear' or 'log'arithmic (the default is None, which means each plot has its own colormap)
        :param cmin:
            The minimum number of counts that will be displayed (the default is 1, meaning that no counts will be blank in the plot)
        :param bins:
            How many bins in each direction should be performed (the default is 400)

        """
        if scaling is not None:
            norm = {"log": pltcol.LogNorm(), "linear": pltcol.Normalize()}.get(scaling)
            if norm is None:
                raise Warning(
                    "Parameter scaling not understood. Possible values: log | linear"
                )
        else:
            norm = None

        if limits is None:
            limit_range = None
        else:
            limit_range = [[limits[0], limits[1]], [limits[2], limits[3]]]

        fig = plt.figure()
        for i, (xs, ys, label) in enumerate(zip(*data_lists)):
            ax = fig.add_subplot(rows, cols, i + 1, aspect=aspect)
            self._plot_single(
                fig,
                ax,
                xs,
                ys,
                bins,
                cmap,
                norm,
                cmin,
                limit_range,
                label,
                ylabel,
                xlabel,
                plot_extra,
            )

        plt.tight_layout()
        plt.show()

    def get_amplitude_list(self, limits, bins):
        def get_xy(iqdata):
            phases = numpy.angle(iqdata.i_list + 1j * iqdata.q_list)
            amplitudes = numpy.abs(iqdata.i_list + 1j * iqdata.q_list)
            return (phases, amplitudes)

        lists, _, _ = self._analyze_data_for_plot(get_xy)

        amplitude_list = numpy.zeros(len(lists[0]))
        amplerror_list = numpy.zeros(len(lists[0]))

        for i, (phases, amplitudes, _) in enumerate(zip(*lists)):
            histodata = numpy.histogram2d(
                phases,
                amplitudes,
                bins=bins,
                range=[[limits[2], limits[3]], [limits[0], limits[1]]],
            )
            amplitude, amplitude_error = IQFit._get_gauss_amplitude(*histodata)
            amplitude_list[i] = amplitude
            amplerror_list[i] = amplitude_error

        return amplitude_list, amplerror_list

    def _plot_single(
        self,
        fig,
        ax,
        xs,
        ys,
        bins,
        cmap,
        norm,
        cmin,
        limit_range,
        label="",
        xlabel="",
        ylabel="",
        plot_extra=None,
        axis=True,
        vmax=None,
    ):
        hist, edges_x, edges_y, img = ax.hist2d(
            xs,
            ys,
            bins=bins,
            cmap=cmap,
            norm=norm,
            cmin=cmin,
            range=limit_range,
            vmax=vmax,
        )

        if callable(plot_extra):
            plot_extra(fig, ax, hist, edges_x, edges_y)

        if limit_range is not None:
            ax.set_xlim(limit_range[0][0], limit_range[0][1])
            ax.set_ylim(limit_range[1][0], limit_range[1][1])

        if axis:
            plt.colorbar(img, ax=ax).set_label("count")
            plt.title(label)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)

        return hist, edges_x, edges_y

    def _plot_to_file(self, filename, plot_function, figsize=(1, 1)):
        fig = plt.figure(figsize=figsize, dpi=100, frameon=False)
        ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
        ax.set_axis_off()
        fig.add_axes(ax)

        result = plot_function(fig, ax)

        fig.savefig(filename, dpi=100)

        return result

    def _update_iq_data(self, iq_data):
        try:
            iq_data.count
        except AttributeError:
            iq_data.count = len(iq_data.i_list)


class IQData:
    """Data object for storing IQ data."""

    def __init__(self, i, q, label=None):
        """Initializing data object with list of I and Q values.

        :param i: Array of I (inphase) values.
        :type i: list[float]
        :param q: Array of Q (quadrature) values.
        :type q: list[float]
        :param label: Label of the dataset
        :type label: str
        """
        self.label = label
        self.count = len(i)
        self.i_list = numpy.array(i)
        self.q_list = numpy.array(q)
        self.i_mean = numpy.mean(self.i_list)
        self.q_mean = numpy.mean(self.q_list)
        self.amplitude = numpy.mean(numpy.abs(self.i_list + 1j * self.q_list))
        self.phase = numpy.angle(numpy.mean(self.i_list + 1j * self.q_list))
