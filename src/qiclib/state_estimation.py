from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt


def _ensure_complex(arr):
    if np.iscomplexobj(arr):
        return arr
    return arr[0] + 1j * arr[1]


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
        >>> LinearDiscriminator.estimate((1, 2), (1, -2j))
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
        >>> cfg = LinearDiscriminator(a=(0, -1), b=0)
        >>> cfg.get_state((0.5, 0.5))
        array(1)
        >>> cfg.get_state((0.5, -0.5))
        array(0)

        The input can be a tuple of two value (I and Q), a complex number or an array of tuplex
        or complex numbers.
        """
        data = np.atleast_1d(data)
        if np.iscomplexobj(data):
            data_i, data_q = data.float, data.imag
        else:
            data_i, data_q = data
        return np.where(data_i * self.a[0] + data_q * self.a[1] + self.b >= 0, 1, 0)

    def plot_separation_line(self, x_min=-1, x_max=1):
        """
        Plots the separation line on the x-interval given by `x_min` and `x_max`
        """
        import matplotlib.pyplot as plt

        y0 = -(self.a[0] * x_min + self.b) / self.a[1]
        y1 = -(self.a[0] * x_max + self.b) / self.a[1]
        plt.plot([x_min, x_max], [y0, y1])

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
