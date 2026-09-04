from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import numpy.typing as npt

# Regions smaller than this fraction of the plotted area are not shaded.
_MIN_REGION_AREA = 1e-9


def _ensure_complex(arr):
    if np.iscomplexobj(arr):
        return arr
    return arr[0] + 1j * arr[1]


def _clip_line_to_unit_box(
    a: float, b: float, c: float
) -> tuple[tuple[float, float], tuple[float, float]] | None:
    """
    Clips the line `a * u + b * v + c == 0` to the unit box (0, 0) - (1, 1).

    :return:
        the two end points of the resulting segment or `None` if the line does not
        intersect the unit box.
    """
    tol = 1e-9
    candidates = []
    if b != 0:
        candidates += [(0.0, -c / b), (1.0, -(a + c) / b)]
    if a != 0:
        candidates += [(-c / a, 0.0), (-(b + c) / a, 1.0)]
    inside = [
        point
        for point in candidates
        if -tol <= point[0] <= 1 + tol and -tol <= point[1] <= 1 + tol
    ]
    if len(inside) < 2:
        return None
    # The line may pass exactly through a corner, so pick the two points that are
    # furthest apart instead of just the first two.
    start, end = max(
        ((p, q) for i, p in enumerate(inside) for q in inside[i + 1 :]),
        key=lambda pair: np.hypot(pair[0][0] - pair[1][0], pair[0][1] - pair[1][1]),
    )
    if np.hypot(start[0] - end[0], start[1] - end[1]) < tol:
        return None
    return start, end


def _clip_polygon_to_half_plane(
    polygon: list[tuple[float, float]], a: float, b: float, c: float
) -> list[tuple[float, float]]:
    """
    Clips a convex polygon to the half plane `a * u + b * v + c >= 0`.

    :param polygon:
        the corners of the polygon in counter-clockwise order.

    :return:
        the corners of the resulting polygon in counter-clockwise order. The list is
        empty if the half plane does not cover any part of the polygon.
    """
    corners: list[tuple[float, float]] = []
    for (u_0, v_0), (u_1, v_1) in zip(polygon, polygon[1:] + polygon[:1]):
        d_0 = a * u_0 + b * v_0 + c
        d_1 = a * u_1 + b * v_1 + c
        if d_0 >= 0:
            corners.append((u_0, v_0))
        if (d_0 >= 0) != (d_1 >= 0):
            # The edge crosses the separation line, so add the intersection point.
            t = d_0 / (d_0 - d_1)
            corners.append((u_0 + t * (u_1 - u_0), v_0 + t * (v_1 - v_0)))
    return corners


def _polygon_area(polygon: list[tuple[float, float]]) -> float:
    """
    Returns the area of a polygon given by its corners.
    """
    return 0.5 * abs(
        sum(
            u_0 * v_1 - u_1 * v_0
            for (u_0, v_0), (u_1, v_1) in zip(polygon, polygon[1:] + polygon[:1])
        )
    )


@dataclass(frozen=True)
class LinearDiscriminator:
    """
    A linear discriminator used to distinguish between the states |0> and |1>
    from raw IQ data.

    This class contains method to obtain the discriminator from the representation used by the
    QiController using `LinearDiscriminator.from_platform_data(qic.cell[...].recording.state_config)`
    and store the data to the QiController using `qic.cell[...].recording.state_config = discriminator.to_platform_data()`
    """

    a: tuple[float, float]
    b: float

    @classmethod
    def from_normal_form(cls, p: tuple[float, float], n: tuple[float, float]):
        """
        Returns a discriminator from the normal form
        (x - p) * n = 0
        """
        return cls(a=n, b=-(p[0] * n[0] + p[1] * n[1]))

    @classmethod
    def from_parameter_form(cls, p: tuple[float, float], u: tuple[float, float]):
        """
        Returns a discriminator from its parameter form
        (i, q) = (p1, p1) + s * (u1, u2)
        """
        a = -u[1], u[0]
        return cls(a=a, b=-(p[0] * a[0] + p[1] * a[1]))

    @classmethod
    def through_points(cls, p1: tuple[float, float], p2: tuple[float, float]):
        """
        Returns a linear discriminator that passes through two points.
        """
        x1, y1 = p1
        x2, y2 = p2
        return cls(a=(y1 - y2, x2 - x1), b=x1 * y2 - x2 * y1)

    @classmethod
    def estimate(cls, state_0, state_1):
        """
        Estimates the config given data that are classified into two states.

        The state can be given as complex values, e.g.:
        >>> LinearDiscriminator.estimate(1 + 2j, 1 - 2j)
        LinearDiscriminator(a=(np.float64(0.0), np.float64(-4.0)), b=np.float64(0.0))

        or as tuples of two values, representing I and Q:
        >>> LinearDiscriminator.estimate((1, 2), (1, -2))
        LinearDiscriminator(a=(np.float64(0.0), np.float64(-4.0)), b=np.float64(0.0))

        or combinations thereof.

        Arrays are also supported and the best config is estimated based on the arithmetic mean:
        >>> LinearDiscriminator.estimate([1 + 1j, 1 + 3j], [1 - 3j, 1 - 1j])
        LinearDiscriminator(a=(np.float64(0.0), np.float64(-4.0)), b=np.float64(0.0))
        """
        np_st0: npt.NDArray = _ensure_complex(np.atleast_1d(state_0))
        np_st1: npt.NDArray = _ensure_complex(np.atleast_1d(state_1))
        a = np.mean(np_st1 - np_st0)
        b = np.mean(
            ((np_st0 * np_st0.conj()) - (np_st1 * np_st1.conj())) / 2,
        )
        return LinearDiscriminator(a=(a.real, a.imag), b=b.real)

    def get_state(self, data):
        """
        separates the data into state 0 and state 1 based on the set configuration.

        The following config separates the complex plane at the I-axis.
        States where Q >= 0 are classified as 1 while states where Q < 0 are classified as 0:
        >>> cfg = LinearDiscriminator(a=(0, 1), b=0)
        >>> cfg.get_state((0.5, 0.5))
        array(1)
        >>> cfg.get_state((0.5, -0.5))
        array(0)

        The input can be a tuple of two value (I and Q), a complex number or an array of tuplex
        or complex numbers.
        """
        data = np.atleast_1d(data)
        if np.iscomplexobj(data):
            data_i, data_q = data.real, data.imag
        else:
            data_i, data_q = data
        return np.where(data_i * self.a[0] + data_q * self.a[1] + self.b >= 0, 1, 0)

    def plot(
        self,
        ax=None,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        label: str | None = None,
        band_width: float = 0.02,
        **kwargs,
    ):
        """
        Draws the separation line of this discriminator onto a matplotlib axis.

        The line itself is the set of points where
        :math:`a_I \\cdot I + a_Q \\cdot Q + b = 0`.
        A narrow hatched band is drawn alongside the line on the :math:`|0\\rangle`
        side (where :math:`a_I \\cdot I + a_Q \\cdot Q + b < 0`), so the side that is
        classified as :math:`|1\\rangle` is the one *without* hatching.

        This is meant to be drawn on top of an existing plot, e.g. a scatter plot of
        IQ data::

            ax.scatter(data.real, data.imag)
            discriminator.plot(ax)

        :param ax:
            the `matplotlib.axes.Axes` to draw on. Defaults to the current axis
            (`matplotlib.pyplot.gca()`), which creates a new figure if none exists.
        :param xlim:
            the I range to draw within. Defaults to the current limits of `ax`.
        :param ylim:
            the Q range to draw within. Defaults to the current limits of `ax`.
        :param label:
            the legend label of the separation line. No legend entry is created if
            this is `None`. Call `ax.legend()` afterwards to show the legend.
        :param band_width:
            the width of the hatched band as a fraction of the plotted area.
        :param kwargs:
            further keyword arguments passed on to `matplotlib.axes.Axes.plot` for
            the separation line, e.g. ``color`` or ``linestyle``.

        :return:
            the `matplotlib.axes.Axes` that was drawn on.
        """
        import matplotlib.pyplot as plt

        if ax is None:
            ax = plt.gca()
        if xlim is None:
            xlim = ax.get_xlim()
        if ylim is None:
            ylim = ax.get_ylim()

        a_i, a_q = self.a
        if a_i == 0 and a_q == 0:
            raise ValueError(
                "Cannot plot a discriminator with a = (0, 0) as it does not define a line."
            )

        x_min, x_max = xlim
        y_min, y_max = ylim
        dx = x_max - x_min
        dy = y_max - y_min

        # Work in coordinates normalized to the plotted area so that the hatched band
        # has the same visual width independent of the axis scaling and aspect ratio.
        line = _clip_line_to_unit_box(
            a_i * dx, a_q * dy, a_i * x_min + a_q * y_min + self.b
        )
        if line is None:
            # The separation line does not cross the plotted area, nothing to draw.
            return ax

        (u_0, v_0), (u_1, v_1) = line

        def to_data(u, v):
            return x_min + u * dx, y_min + v * dy

        (line_x_0, line_y_0) = to_data(u_0, v_0)
        (line_x_1, line_y_1) = to_data(u_1, v_1)
        (separation_line,) = ax.plot(
            [line_x_0, line_x_1], [line_y_0, line_y_1], label=label, **kwargs
        )

        # The |0> side is where a * m + b < 0, i.e. opposite to the normal vector a.
        normal_u, normal_v = a_i * dx, a_q * dy
        normal_length = np.hypot(normal_u, normal_v)
        offset_u = -band_width * normal_u / normal_length
        offset_v = -band_width * normal_v / normal_length
        band = [
            to_data(u_0, v_0),
            to_data(u_1, v_1),
            to_data(u_1 + offset_u, v_1 + offset_v),
            to_data(u_0 + offset_u, v_0 + offset_v),
        ]
        ax.fill(
            [point[0] for point in band],
            [point[1] for point in band],
            facecolor="none",
            edgecolor=separation_line.get_color(),
            hatch="///",
            linewidth=0,
        )

        # Drawing may have triggered a rescale, so restore the limits we drew for.
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        return ax

    def shade(
        self,
        ax=None,
        result: int = 1,
        xlim: tuple[float, float] | None = None,
        ylim: tuple[float, float] | None = None,
        label: str | None = None,
        alpha: float = 0.15,
        **kwargs,
    ):
        """
        Fills the area of the plot in which this discriminator returns `result`.

        The area for ``result=1`` is the half plane where
        :math:`a_I \\cdot I + a_Q \\cdot Q + b \\geq 0`, the one for ``result=0`` is
        its complement, see `LinearDiscriminator.get_state`. To fill the area where
        several discriminators return a certain result, see `shade_region`.

        :param ax:
            the `matplotlib.axes.Axes` to draw on. Defaults to the current axis
            (`matplotlib.pyplot.gca()`), which creates a new figure if none exists.
        :param result:
            the discriminator result (0 or 1) whose area is filled.
        :param xlim:
            the I range to draw within. Defaults to the current limits of `ax`.
        :param ylim:
            the Q range to draw within. Defaults to the current limits of `ax`.
        :param label:
            the legend label of the area. No legend entry is created if this is `None`.
        :param alpha:
            the opacity of the filled area.
        :param kwargs:
            further keyword arguments passed on to `matplotlib.axes.Axes.fill`,
            e.g. ``color``.

        :return:
            the `matplotlib.axes.Axes` that was drawn on.
        """
        import matplotlib.pyplot as plt

        if ax is None:
            ax = plt.gca()
        shade_region(
            [self],
            [result],
            ax=ax,
            xlim=xlim,
            ylim=ylim,
            label=label,
            alpha=alpha,
            **kwargs,
        )
        return ax

    def platform_data(self) -> tuple[float, float, float]:
        """
        Returns the representation used by the QiController
        """
        return *self.a, self.b

    @classmethod
    def from_platform_data(cls, pdata: tuple[float, float, float]):
        """
        Returns a linear discriminator from a representation used by the QiController
        """
        return cls(a=(pdata[0], pdata[1]), b=pdata[2])


def shade_region(
    discriminators: Sequence[LinearDiscriminator],
    results: Sequence[int],
    ax=None,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
    label: str | None = None,
    alpha: float = 0.15,
    **kwargs,
) -> list:
    """
    Fills the area of the plot in which every discriminator returns its result.

    The discriminators cut the plane into convex regions, one for each combination of
    results. This fills the single region in which `discriminators[i]` returns
    `results[i]` for every `i`, see `LinearDiscriminator.get_state`.

    :param discriminators:
        the discriminators that bound the region.
    :param results:
        the result (0 or 1) each discriminator returns within the region. Must have
        the same length as `discriminators`.
    :param ax:
        the `matplotlib.axes.Axes` to draw on. Defaults to the current axis
        (`matplotlib.pyplot.gca()`), which creates a new figure if none exists.
    :param xlim:
        the I range to draw within. Defaults to the current limits of `ax`.
    :param ylim:
        the Q range to draw within. Defaults to the current limits of `ax`.
    :param label:
        the legend label of the area. No legend entry is created if this is `None`.
    :param alpha:
        the opacity of the filled area.
    :param kwargs:
        further keyword arguments passed on to `matplotlib.axes.Axes.fill`,
        e.g. ``color``.

    :return:
        the polygons that were drawn. The list is empty if the region does not cover
        any part of the plotted area, in which case nothing was drawn at all.
    """
    import matplotlib.pyplot as plt

    if ax is None:
        ax = plt.gca()
    if xlim is None:
        xlim = ax.get_xlim()
    if ylim is None:
        ylim = ax.get_ylim()

    x_min, x_max = xlim
    y_min, y_max = ylim
    dx = x_max - x_min
    dy = y_max - y_min

    # Work in coordinates normalized to the plotted area, where the region is obtained
    # by successively clipping the plotted area to the half plane of each discriminator.
    corners = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    for discriminator, result in zip(discriminators, results, strict=True):
        a_i, a_q = discriminator.a
        if a_i == 0 and a_q == 0:
            raise ValueError(
                "Cannot shade a discriminator with a = (0, 0) as it does not define a line."
            )
        a, b, c = a_i * dx, a_q * dy, a_i * x_min + a_q * y_min + discriminator.b
        if not result:
            # The |0> side is where a * m + b < 0, i.e. the complementary half plane.
            a, b, c = -a, -b, -c
        corners = _clip_polygon_to_half_plane(corners, a, b, c)
        if len(corners) < 3:
            # The region does not cover any part of the plot, nothing to draw.
            return []

    if _polygon_area(corners) < _MIN_REGION_AREA:
        # Almost parallel discriminators can leave a sliver that is not worth drawing.
        return []

    polygons = ax.fill(
        [x_min + u * dx for u, _ in corners],
        [y_min + v * dy for _, v in corners],
        label=label,
        alpha=alpha,
        linewidth=0,
        zorder=0,
        **kwargs,
    )

    # Drawing may have triggered a rescale, so restore the limits we drew for.
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    return polygons
