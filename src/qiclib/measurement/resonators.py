# only for saving data
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np

# needed for qfactor calculations
# switched to python 3.6.8 for this
from lmfit import Model, Parameters


class ResonatorsConfig:
    def __init__(self, vna):
        self.frequency_start = None
        self.frequency_stop = None
        self.frequency_step = None
        self.frequency_center = 0

        self.vna = vna

        # more parameters for the resonator detection. Can be changed by change_detector_parameters if necessary
        self.smoothing_window = 8
        self.derivative_smoothing_window = 5
        self.filtering_window = 120
        self.sample_option = 0

        # if the filtering window parameter is changed automatically when less than three resonators are in the spectrum
        # default is true, prevents false negative bug
        self.auto_filtering_window = True

        self.frequency_range_set = False

    def change_detector_parameters(
        self,
        smoothing_window=None,
        derivative_smoothing_window=None,
        filtering_window=None,
        auto_filtering_window=None,
    ):
        if smoothing_window is not None:
            self.smoothing_window = smoothing_window
        if derivative_smoothing_window is not None:
            self.derivative_smoothing_window = derivative_smoothing_window
        if filtering_window is not None:
            self.filtering_window = filtering_window
        if auto_filtering_window is not None:
            self.auto_filtering_window = auto_filtering_window

    def use_sample_data(self, sample_option):
        # if preloaded data is to be used: set frequency range according to file option
        self.sample_option = sample_option

        if self.sample_option == 1:
            print("using sample option: 1")
            self.frequency_start = 0
            self.frequency_stop = 100e6
            self.frequency_step = 40e3
        elif self.sample_option == 2:
            print("using sample option: 2")
            self.frequency_start = 0
            self.frequency_stop = 200e6
            self.frequency_step = 40e3
        elif self.sample_option == 3:
            print("using sample option: 3")
            self.frequency_start = 0
            self.frequency_stop = 200e6
            self.frequency_step = 40e3
        elif self.sample_option == 4:
            print("using sample option: 4")
            self.frequency_start = 0
            self.frequency_stop = 50e6
            self.frequency_step = 40e3
        elif self.sample_option == 5:
            print("using sample option: 5")
            self.frequency_start = -100e6
            self.frequency_stop = 100e6
            self.frequency_step = 25e3
        elif self.sample_option == 6:
            print("using sample option: 6")
            self.frequency_start = 100e6
            self.frequency_stop = 200e6
            self.frequency_step = 40e3
        elif self.sample_option == 7:
            print("using sample option: 7")
            self.frequency_start = 25e6
            self.frequency_stop = 75e6
            self.frequency_step = 40e3
        elif self.sample_option == 8:
            print("using sample option: 8")
            self.frequency_start = 25e6
            self.frequency_stop = 75e6
            self.frequency_step = 40e3
        elif self.sample_option == 9:
            print("using sample option: 9")
            self.frequency_start = 300e6
            self.frequency_stop = 400e6
            self.frequency_step = 40e3
        elif self.sample_option == 10:
            print("using sample option: 10")
            self.frequency_start = -400e6
            self.frequency_stop = 400e6
            self.frequency_step = 100e3
        elif self.sample_option == 11:
            print("using sample option: 11")
            self.frequency_start = -400e6
            self.frequency_stop = 400e6
            self.frequency_step = 200e3
        elif self.sample_option == 12:
            print("using sample option: 12")
            self.frequency_start = -400e6
            self.frequency_stop = 400e6
            self.frequency_step = 200e3
        elif self.sample_option == 13:
            print("using sample option: 13")
            self.frequency_start = -400e6
            self.frequency_stop = 400e6
            self.frequency_step = 200e3
        elif self.sample_option == 14:
            print("using sample option: 14")
            self.frequency_start = 50e6
            self.frequency_stop = 75e6
            self.frequency_step = 40e3
        elif self.sample_option == 15:
            print("using sample option: 15")
            self.frequency_start = 90e6
            self.frequency_stop = 100e6
            self.frequency_step = 2000
        elif self.sample_option == 16:
            print("using sample option: 16")
            self.frequency_start = 90e6
            self.frequency_stop = 93e6
            self.frequency_step = 1000
        elif self.sample_option == 17:
            print("using sample option: 17")  # "F08_Spec_4-10GHz_20000pt_400HzBW.txt"
            self.frequency_start = 4e9
            self.frequency_stop = 10e9 + 300e3
            self.frequency_step = 300e3
        elif self.sample_option == 18:
            print(
                "using sample option: 18"
            )  # "F08_Spec_7.8G_20MHzSpan_2000pt_400HzBW.txt";
            self.frequency_start = 7.858534957390000343e09
            self.frequency_step = 7.858549957390000343e09 - 7.858534957390000343e09
            self.frequency_stop = 7.888534957390000343e09 + self.frequency_step
        elif self.sample_option == 19:
            print(
                "using sample option: 19"
            )  # "RM7UQF_GeQCoS7Qv3-7C5_Spec_7.5-7.9GHz.txt"; #!! bounds may not be correct
            self.frequency_start = 7.5e9
            self.frequency_step = 25e4
            self.frequency_stop = 7.9e9 + self.frequency_step
        elif self.sample_option == 20:
            print(
                "using sample option: 20"
            )  # "S5LR3Y_TAN018_C7_Spec_5-11GHz_20000pt_400HzBW.txt";
            self.frequency_start = 5e9
            self.frequency_step = 300e3
            self.frequency_stop = 11e9 + self.frequency_step
        elif self.sample_option == 21:
            print(
                "using sample option: 21"
            )  # "S5LRKK_TAN018_C7_Spec_9.41GHz_4000pt_400HzBW.txt";
            self.frequency_start = 9.385e9
            self.frequency_step = 12.5e3
            self.frequency_stop = 9.435e9 + self.frequency_step
        elif self.sample_option == 22:
            print(
                "using sample option: 22"
            )  # "Resonators_DATA_10.0Mhzstart_400.0Mhzstop_100.0kHzstep_2024-04-30_11-58-58.tsv";
            self.frequency_start = 10e6
            self.frequency_step = 100e3
            self.frequency_stop = 400e6
        elif self.sample_option == 23:
            print(
                "using sample option: 23"
            )  # "Resonators_DATA_-350.0Mhzstart_-250.0Mhzstop_50.0kHzstep_2024-04-30_12-27-40.tsv";
            self.frequency_start = -350e6
            self.frequency_step = 50e3
            self.frequency_stop = -250e6
        elif self.sample_option == 24:
            print(
                "using sample option: 24"
            )  # "Resonators_DATA_-500.0Mhzstart_500.0Mhzstop_1000.0kHzstep_2024-04-30_12-59-14.tsv";
            self.frequency_start = -500e6
            self.frequency_step = 1000e3
            self.frequency_stop = 500e6
        elif self.sample_option == 25:
            print(
                "using sample option: 25"
            )  # "SCR5R2_MW_Transistor_Spec_6-10GHz_without_first_column.txt";
            self.frequency_start = 6e9
            self.frequency_step = 100e3
            self.frequency_stop = 9e9
        else:
            raise ValueError("Not a valid file number")

        self.frequency_range_set = True

    def set_frequency_range(self, frequency_start, frequency_stop, frequency_step):
        if self.sample_option != 0:
            print("Frequency range automatically set, as preloaded data is used.")
        else:
            self.frequency_start = frequency_start
            self.frequency_stop = frequency_stop
            self.frequency_step = frequency_step
            self.frequency_range_set = True

    # set the center frequency manually if an additional mixer is used. This will only influence the visualization, not the actual measurement
    def set_center_frequency(self, frequency_center):
        self.frequency_center = frequency_center


class FindResonators:
    def __init__(self, config):
        self.config = config

        if not self.config.frequency_range_set:
            raise ValueError("Frequency range not set.")

        # get the frequency axis from bounds and center frequency, if set
        self.frequency_axis_start = config.frequency_start + config.frequency_center
        self.frequency_axis_stop = config.frequency_stop + config.frequency_center
        self.frequency_step = config.frequency_step

        self.axis_frequencies = np.arange(
            self.frequency_axis_start,
            self.frequency_axis_stop,
            self.frequency_step,
        )

        # convert to Mhz
        self.conv_axis_frequencies = self.axis_frequencies * 1e-6

    def find_n_resonators(self, n):
        result = Resonators(n)

        # set range on VNA, this is not influenced by setting a frequency center
        if self.config.sample_option == 0:
            self.config.vna.set_frequency_range(
                self.config.frequency_start,
                self.config.frequency_stop,
                self.config.frequency_step,
            )
            print(
                f"Frequency range for VNA set to min: {self.config.frequency_start* 1e-6} MHz max: {self.config.frequency_stop * 1e-6} MHz, step size: {self.config.frequency_step * 1e-3} kHz"
            )

        # set the filtering window higher for closeups of resonators to avoid false negatives (may be overwritten by changing the detector options in config)
        if self.config.auto_filtering_window and n < 3:
            filtering_window = 1000
        else:
            filtering_window = self.config.filtering_window

        # measure spectrum and detect resonance frequencies
        detection = self.config.vna.get_resonators(
            n,
            self.config.smoothing_window,
            self.config.derivative_smoothing_window,
            self.config.sample_option,
            filtering_window,
        )

        if not detection.detection_successful:
            print("Error: could not get resonators")
            return
        else:
            print(
                "Resonator detection complete. Number of data points:",
                len(detection.unsmoothed_spectrum),
            )

        if len(detection.resonator_indices) < n:
            print(f"Found {len(detection.resonator_indices)} out of {n} resonances.")

        # get the resonant frequencies
        resonator_frequencies = []
        for i in range(len(detection.resonator_indices)):
            res_frequency = self.axis_frequencies[detection.resonator_indices[i]]
            resonator_frequencies.append(res_frequency)

        print("Resonators suspected at frequencies (decreasing persistence):")

        for i, frequency in enumerate(resonator_frequencies):
            print(f"({i+1}) {frequency*1e-6:.2f} MHz")

        print("for n < 3, be sure to enter the correct number of resonators.")
        print("In case of false negatives, try increasing n.")

        # get the result
        result.n = n
        result.smoothed_spectrum = detection.smoothed_spectrum
        result.unsmoothed_spectrum = detection.unsmoothed_spectrum
        result.derivative = detection.derivative
        result.phase_data = detection.phase
        result.resonator_indices = detection.resonator_indices
        result.resonator_frequencies = resonator_frequencies
        result.sample_option = self.config.sample_option

        result.frequency_axis_start = self.frequency_axis_start
        result.frequency_axis_stop = self.frequency_axis_stop
        result.frequency_step = self.frequency_step
        result.axis_frequencies = self.axis_frequencies
        result.conv_axis_frequencies = self.conv_axis_frequencies

        return result


class Resonators:
    def __init__(self, n):
        self.n = n
        self.smoothed_spectrum = None
        self.unsmoothed_spectrum = None
        self.derivative = None
        self.phase_data = None
        self.resonator_indices = None
        self.resonator_frequencies = None
        self.sample_option = None

        self.frequency_axis_start = None
        self.frequency_axis_stop = None
        self.frequency_step = None
        self.axis_frequencies = None
        self.conv_axis_frequencies = None

    def __getitem__(self, index):
        return self.resonator_frequencies[index - 1] * 1e6

    def display(
        self,
        display_amplitude=True,
        display_derivative=False,
        arbitrary_units=True,
        display_phase=True,
        titleline=True,
        save_to=None,
    ):
        plt.rc("xtick", labelsize=20)
        plt.rc("ytick", labelsize=20)

        # display amplitude
        plt.figure(figsize=(20, 10))
        if display_amplitude:
            plt.plot(
                self.conv_axis_frequencies,
                self.unsmoothed_spectrum,
                color="purple",
                label="Amplitude",
            )
        if display_derivative:
            scaled_derivative_data = [value * 50 for value in self.derivative]
            plt.plot(self.conv_axis_frequencies, scaled_derivative_data, color="plum")

        if arbitrary_units:
            plt.xlabel("Frequency (MHz)", fontsize=20)
            plt.ylabel("Amplitude (AU)", fontsize=20)
        else:
            plt.xlabel("Frequency (MHz)", fontsize=20)
            plt.ylabel("Amplitude (dB)", fontsize=20)

        plotheight = max(self.unsmoothed_spectrum) - min(self.unsmoothed_spectrum)
        plotwidth = max(self.conv_axis_frequencies) - min(self.conv_axis_frequencies)

        plt.xlim(self.frequency_axis_start * 1e-6, self.frequency_axis_stop * 1e-6)
        # plt.ylim(min(self.unsmoothed_spectrum), max(self.unsmoothed_spectrum))
        if display_derivative and not display_amplitude:
            plt.ylim(
                min(scaled_derivative_data),
                max(scaled_derivative_data) + 0.4 * plotheight,
            )
        else:
            plt.ylim(
                min(self.unsmoothed_spectrum),
                max(self.unsmoothed_spectrum) + 0.5 * plotheight,
            )

        ylim = plt.ylim()

        for i in range(len(self.resonator_indices)):
            resonator_freq = self.conv_axis_frequencies[self.resonator_indices[i]]
            plt.axvline(
                x=self.conv_axis_frequencies[self.resonator_indices[i]],
                color="gray",
                linestyle="dotted",
                label=f"Detected Resonator {i + 1} ",
                zorder=0,
                linewidth=2.2,
            )
            plt.text(
                self.conv_axis_frequencies[self.resonator_indices[i]]
                + plotwidth * 8e-3,
                ylim[1] - plotheight * 1e-2,
                f"{resonator_freq:.2f} MHz ({i+1})",
                color="gray",
                rotation=90,
                verticalalignment="top",
                fontsize=18,
            )

        # if path is specified, save figure
        if save_to is not None:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = f"Resonators_PLOT_Amplitude_{self.frequency_axis_start* 1e-6}Mhzstart_{self.frequency_axis_stop* 1e-6}Mhzstop_{self.frequency_step* 1e-3}kHzstep_{timestamp}.pdf"
            file_path = f"{save_to}/{file_name}"  # Constructing the file path directly

            plt.savefig(file_path)
            print(f"Figure saved to: {file_path}")

        if display_phase:
            # display phase
            plt.figure(figsize=(20, 3))
            plt.plot(
                self.conv_axis_frequencies, self.phase_data, color="grey", label="Phase"
            )
            plt.xlabel("Frequency (MHz)", fontsize=15)
            plt.ylabel("Phase (rad)", fontsize=15)
            if self.sample_option != 0:
                plt.title(
                    f"Measured Spectrum (Phase) - Sample {self.sample_option} - {len(self.unsmoothed_spectrum)} points",
                    fontsize=15,
                )
            else:
                plt.title(
                    f"Measured Spectrum with Detected Resonators (Phase) - {len(self.unsmoothed_spectrum)} points",
                    fontsize=15,
                )

            plt.xlim(self.frequency_axis_start * 1e-6, self.frequency_axis_stop * 1e-6)
            for i in range(self.n):
                # resonator_freq = self.conv_axis_frequencies[self.resonator_indices[i]]
                plt.axvline(
                    x=self.conv_axis_frequencies[self.resonator_indices[i]],
                    color="wheat",
                    linestyle="-",
                    label=f"Detected Resonator {i + 1}",
                )

        # if path is specified, save figure
        if save_to is not None:
            timestamp = datetime.now().strftime("%d_%H-%M-%S")
            file_name = f"Resonators_PLOT_Phase_{self.frequency_axis_start* 1e-6}Mhzstart_{self.frequency_axis_stop* 1e-6}Mhzstop_{self.frequency_step* 1e-3}kHzstep_{timestamp}.pdf"
            file_path = f"{save_to}/{file_name}"  # Constructing the file path directly

            plt.savefig(file_path)
            print(f"Figure saved to: {file_path}")

    def make_figure(
        self, file_path, sample_number, titleline=True, save=True, comment=""
    ):
        timestamp = datetime.now().strftime("%d_%H-%M-%S")
        file_name = f"Resonators_FIGURE_Sample_{sample_number}_n: {self.n}_{comment}_{timestamp}.pdf"
        file_path = f"{file_path}/{file_name}"  # Constructing the file path directly
        self.display(display_derivative=False, display_phase=False, titleline=titleline)
        if save:
            plt.savefig(file_path)
            print(f"Figure saved to: {file_path}")

    def display_single_resonator(
        self,
        index,
        width=50e6,
        height=None,
        display_derivative=None,
        arbitrary_units=True,
    ):
        if not index <= self.n:
            print(f"Error: Please specify a number between 1 and {self.n}")
            return

        local_resonator = self.resonator_indices[index - 1]

        print(
            f"Resonator ({index}) at {self.conv_axis_frequencies[local_resonator]:.2f} MHz (Index {local_resonator})"
        )
        leftbound = self.conv_axis_frequencies[local_resonator] - width / 2 * 1e-6
        rightbound = self.conv_axis_frequencies[local_resonator] + width / 2 * 1e-6
        print(f"Amplitude: {self.unsmoothed_spectrum[local_resonator]}")

        # display amplitude around resonator

        plt.rc("xtick", labelsize=15)
        plt.rc("ytick", labelsize=15)

        plt.figure(figsize=(7, 7))
        plt.plot(
            self.conv_axis_frequencies,
            self.unsmoothed_spectrum,
            linestyle="-",
            color="purple",
            # marker=".",
        )
        if display_derivative:
            plt.scatter(
                self.conv_axis_frequencies,
                self.derivative,
                linestyle="-",
                color="lightgrey",
                marker=".",
            )

        plt.xlim(leftbound, rightbound)
        if height is not None:
            plt.ylim(
                self.unsmoothed_spectrum[local_resonator] - height / 4,
                self.unsmoothed_spectrum[local_resonator] + height * 3 / 4,
            )
        if arbitrary_units:
            plt.xlabel("Frequency (MHz)", fontsize=15)
            plt.ylabel("Amplitude (AU)", fontsize=15)
        else:
            plt.xlabel("Frequency (MHz)", fontsize=15)
            plt.ylabel("Amplitude (dB)", fontsize=15)
        # plt.title(
        #     f"Resonator at {self.conv_axis_frequencies[local_resonator]:.2f} MHz : Amplitude (index {local_resonator})"
        # )
        plt.axvline(
            x=self.conv_axis_frequencies[local_resonator],
            color="orange",
            linestyle="-",
            linewidth=2,
            label="Resonator Index",
            zorder=0,
        )
        plt.tight_layout()

    def display_iq_plane(self, bound=100):
        print(
            "optional: specify the number of points to be plotted around each resonator"
        )

        plt.rc("xtick", labelsize=20)
        plt.rc("ytick", labelsize=20)

        # Create IQ data
        iq_data_real = self.unsmoothed_spectrum * np.cos(self.phase_data)
        iq_data_imag = self.unsmoothed_spectrum * np.sin(self.phase_data)

        # Indices bound
        index_bound = bound

        # Generate colors for each resonator
        colors = [
            "r",
            "g",
            "b",
            "c",
            "m",
            "y",
            "k",
            "orange",
            "purple",
            "brown",
            "pink",
            "olive",
            "navy",
            "teal",
            "maroon",
            "gold",
            "indigo",
            "lime",
        ]
        num_resonators = self.n
        color_index = 0

        # Plot IQ data
        plt.figure(figsize=(13, 10))
        plt.axis("equal")

        # Scatter only points within index bounds around resonator_indices
        for idx, index in enumerate(self.resonator_indices):
            start_index = max(0, index - index_bound)
            end_index = min(len(iq_data_real), index + index_bound + 1)
            plt.plot(
                iq_data_real[start_index:end_index],
                iq_data_imag[start_index:end_index],
                color=colors[color_index % num_resonators],
                label=f"Resonator ({idx+1}) at {self.conv_axis_frequencies[index]:.2f} MHz",
            )
            color_index += 1

        plt.xlabel("I", fontsize=20)
        plt.ylabel("Q", fontsize=20)
        plt.grid(True)
        plt.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), fontsize=15, ncol=2)
        plt.tight_layout()

    def get_qfactors(self, width=20e6):
        qfactors = Qfactors()
        qfactors.n = self.n
        qfactors.width = width
        qfactors.window_steps = int((width / 2) // self.frequency_step)
        qfactors.qfac_frequencies_window = [[] for _ in range(self.n)]
        qfactors.qfac_resonator_window = [[] for _ in range(self.n)]
        qfactors.qfac_index_best_fit = [[] for _ in range(self.n)]
        qfactors.bandwidth_value = [[] for _ in range(self.n)]
        qfactors.corrected_f0 = [[] for _ in range(self.n)]
        qfactors.q_factors = [[] for _ in range(self.n)]
        qfactors.qfactors_result = [[] for _ in range(self.n)]

        print(
            f"Approx. loaded Q-factors for detected resonators by Lorentzian fit using window of {width * 1e-6} Mhz:"
        )

        for index in range(self.n):
            local_resonator = self.resonator_indices[index]
            resonator_frequency = self.conv_axis_frequencies[local_resonator]
            resonator_amplitude = self.unsmoothed_spectrum[local_resonator]

            model = Model(qfactors.lorentzian_model)

            left_index = local_resonator - qfactors.window_steps
            right_index = local_resonator + qfactors.window_steps

            qfactors.qfac_frequencies_window[index] = self.conv_axis_frequencies[
                left_index:right_index
            ]
            qfactors.qfac_resonator_window[index] = self.unsmoothed_spectrum[
                left_index:right_index
            ]

            if left_index < 0 or right_index > len(self.unsmoothed_spectrum):
                print(
                    f"Resonator ({index}) at {self.conv_axis_frequencies[local_resonator]} MHz :    Frequency window with width {width * 1e-6} MHz out of bounds for this measurement"
                )
                qfactors.q_factors[index] = 0
                continue

            # set initial guesses for fitting parameters
            guess_constant_background = (
                self.unsmoothed_spectrum[right_index]
                + self.unsmoothed_spectrum[left_index]
            ) / 2
            guess_background_slope = (
                self.unsmoothed_spectrum[right_index]
                - self.unsmoothed_spectrum[left_index]
            ) / (width * 1e-6)
            guess_skew = 0.0
            guess_maximum_magnitude = resonator_amplitude
            guess_bandwidth = 1.0

            params = Parameters()
            params.add("constant_background", value=guess_constant_background)
            params.add("background_slope", value=guess_background_slope)
            params.add("skew", value=guess_skew)
            params.add("resonator_frequency", value=resonator_frequency)
            params.add("maximum_magnitude", value=guess_maximum_magnitude)
            params.add("bandwidth", value=guess_bandwidth, min=0.0)

            # run the fitting algorithm
            qfactors.qfactors_result[index] = model.fit(
                qfactors.qfac_resonator_window[index],
                params,
                f=qfactors.qfac_frequencies_window[index],
                fit_kws={"ftol": 1e-3},
            )
            qfactors.qfac_index_best_fit[index] = qfactors.qfactors_result[
                index
            ].best_fit
            params_qfactors_result = qfactors.qfactors_result[index].params
            qfactors.bandwidth_value[index] = params_qfactors_result["bandwidth"].value
            qfactors.corrected_f0[index] = params_qfactors_result[
                "resonator_frequency"
            ].value

            calc_qfactor = (
                qfactors.corrected_f0[index] / qfactors.bandwidth_value[index]
            )

            if calc_qfactor > 100000:
                qfactors.q_factors[index] = 0
                print(
                    f"Resonator ({index+1}) at {qfactors.corrected_f0[index]:.3f} MHz:    Q = N/A"
                )
            else:
                qfactors.q_factors[index] = calc_qfactor
                print(
                    f"Resonator ({index+1}) at {qfactors.corrected_f0[index]:.3f} MHz (corrected):    Q = {calc_qfactor:.2f}"
                )

        print("Call visualize_qfactor(index) to visualize the fitting for a resonator.")

        return qfactors

    def save_data(self, path):
        data = np.column_stack((self.unsmoothed_spectrum, self.phase_data))

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"Resonators_DATA_{self.frequency_axis_start* 1e-6}Mhzstart_{self.frequency_axis_stop* 1e-6}Mhzstop_{self.frequency_step* 1e-3}kHzstep_{timestamp}.tsv"
        file_path = f"{path}/{file_name}"  # Constructing the file path directly

        np.savetxt(file_path, data, delimiter="\t", header="amplitude\tphase")

        print(f"Data saved to: {file_path}")

    def save_resonators(self, path):
        data = np.column_stack((self.resonator_indices, self.resonator_frequencies))

        # Create file name based on resonator attributes and timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"Resonators_FOUND_{self.frequency_axis_start* 1e-6}Mhzstart_{self.frequency_axis_stop* 1e-6}Mhzstop_{self.frequency_step* 1e-3}kHzstep_{timestamp}.tsv"
        file_path = f"{path}/{file_name}"  # Constructing the file path directly

        # Save array to TSV file
        np.savetxt(
            file_path,
            data,
            delimiter="\t",
            header="index\tfrequency(Mhz)",
            fmt=["%d", "%.9e"],
        )

        print(f"Resonators saved to: {file_path}")


class Qfactors:
    def __init__(self):
        self.n = None
        self.width = None
        self.window_steps = None
        self.qfac_frequencies_window = None
        self.qfac_resonator_window = None
        self.qfac_index_best_fit = None
        self.bandwidth_value = None
        self.corrected_f0 = None
        self.q_factors = None
        self.qfactors_result = None

    def __getitem__(self, index):
        return self.q_factors[index - 1]

    def lorentzian_model(
        self,
        f,
        constant_background,
        background_slope,
        skew,
        resonator_frequency,
        maximum_magnitude,
        bandwidth,
    ):
        A_1 = constant_background
        A_2 = background_slope
        A_3 = skew
        f_0 = resonator_frequency
        S_max = maximum_magnitude
        delta_f_lorentz = bandwidth

        return (
            A_1
            + A_2 * f
            + (S_max + A_3 * f)
            / np.sqrt(1 + 4 * np.square((f - f_0) / (delta_f_lorentz)))
        )

    def display(self, index, arbitrary_units=True):
        if not 1 <= index <= self.n:
            print(f"Error: Please specify a number between 1 and {self.n}")
            return
        elif self.q_factors[index - 1] == 0:
            print("No valid qfactor found for this resonator.")
            return

        plt.rc("xtick", labelsize=20)
        plt.rc("ytick", labelsize=20)

        plt.figure(figsize=(9.5, 7))
        plt.scatter(
            self.qfac_frequencies_window[index - 1],
            self.qfac_resonator_window[index - 1],
            color="purple",
            marker=".",
        )
        plt.plot(
            self.qfac_frequencies_window[index - 1],
            self.qfac_index_best_fit[index - 1],
            "darkturquoise",
            label="Lorentzian Fit",
        )
        if arbitrary_units:
            plt.xlabel("Frequency (MHz)", fontsize=15)
            plt.ylabel("Amplitude (AU)", fontsize=15)
        else:
            plt.xlabel("Frequency (MHz)", fontsize=15)
            plt.ylabel("Amplitude (dB)", fontsize=15)

        plt.title(
            f"Resonator ({index}) at {self.corrected_f0[index-1]:.2f} MHz (corr.) Q = {self.q_factors[index-1]:.2f}",
            fontsize=15,
        )

        # Adjust x-axis limits to fit the window
        plt.xlim(
            self.qfac_frequencies_window[index - 1][0],
            self.qfac_frequencies_window[index - 1][-1],
        )
        plt.legend()
