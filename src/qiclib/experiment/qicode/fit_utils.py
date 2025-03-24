import warnings

import numpy as np
from scipy.optimize import OptimizeWarning, curve_fit


def custom_piecewise_linear(t, t1, t2, A1, A2):
    if t1 == t2:  # Case where there is no region 2
        condlist = [t < t1, t >= t1]
        funclist = [
            lambda t: A1,
            lambda t: A2,
        ]
    elif t2 >= max(t):  # Case where there is no region 3 (t2 is at the end)
        condlist = [t < t1, t >= t1]
        funclist = [
            lambda t: A1,
            lambda t: ((A2 - A1) / (t2 - t1)) * (t - t1) + A1,
        ]
    else:  # Case where are there are all three regions
        condlist = [t < t1, (t >= t1) & (t < t2), t >= t2]
        funclist = [
            lambda t: A1,
            lambda t: ((A2 - A1) / (t2 - t1)) * (t - t1) + A1,
            lambda t: A2,
        ]

    return np.piecewise(t, condlist, funclist)


def compute_custom_piecewise_linear_fit(offsets, amplitude):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", OptimizeWarning)
        try:
            initial_guess = [
                offsets[np.argmax(amplitude)],
                offsets[np.argmax(amplitude)]
                + (1024e-9 - offsets[np.argmax(amplitude)]) / 2,
                np.max(amplitude),
                np.min(amplitude),
            ]

            bounds = ([0, 0, 0, 0], [1024e-9, 1024e-9, np.inf, np.inf])

            popt, _ = curve_fit(
                custom_piecewise_linear,
                offsets,
                amplitude,
                p0=initial_guess,
                bounds=bounds,
            )

            t1, t2, A1, A2 = popt
            if t1 == t2:
                print("Note: No region 2 detected (t1 == t2).")
            if t2 >= max(offsets):
                print("Note: No region 3 detected (t2 is at the end of the range).")

            return popt
        except (OptimizeWarning, RuntimeError, ValueError) as e:
            print(f"Curve fitting error: {e}")
            return None
