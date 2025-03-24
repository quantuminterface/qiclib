"""Contains a class and utilities to communicate with the Vector Network Analyzer (VNA) component"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from google.protobuf.empty_pb2 import Empty
from google.protobuf.wrappers_pb2 import DoubleValue, StringValue, UInt32Value

from qiclib.packages.grpc import vna_pb2, vna_pb2_grpc

MagnitudeUnits = Literal["dBFS", "linear"]


def _magnitude_unit_to_proto(unit):
    if isinstance(unit, int):
        return unit
    elif unit.lower() in {"dbfs", "dbf", "db fs"}:
        return vna_pb2.MagnitudeUnit.DB_FS
    elif unit.lower() in {"lin", "linear"}:
        return vna_pb2.MagnitudeUnit.LINEAR
    else:
        raise ValueError(f"Magnitude unit '{unit}' does not name a valid unit")


PhaseUnits = Literal["degree", "radian"]


def _phase_unit_to_proto(unit):
    if isinstance(unit, int):
        return unit
    if unit.lower() in {"°", "deg", "degree", "degrees"}:
        return vna_pb2.PhaseUnit.DEGREES
    elif unit.lower() in {"rad", "radian", "radians"}:
        return vna_pb2.PhaseUnit.RADIAN
    else:
        raise ValueError(f"Phase unit '{unit}' does not name a valid unit")


@dataclass
class NativeFrequencySpec:
    """Return type helper for the native frequency spec getter"""

    start: float
    step: float
    count: int


class VNA:
    """The VNA is a measurement device used to measure the S-Parameter in amplitude and phase."""

    def __init__(self, connection):
        self._connection = connection
        self._stub = vna_pb2_grpc.VNAServiceStub(self._connection.channel)
        self._calibration = Calibration(self._stub)

    def reset(self):
        """Resets the device"""
        self._stub.Reset(Empty())

    @property
    def busy(self):
        """Returns whether the VNA is busy (aka currently measuring a spectrum)"""
        return self._stub.IsBusy(Empty()).value

    def set_frequencies_native(self, start: float, step: float, count: int):
        """Set the frequencies relevant to the VNA in the native representation.

        :param start: The starting frequency
        :param step: The step frequency
        :param count: How many points to sweep
        """
        self._stub.SetFreqSpec(
            vna_pb2.FrequencySpec(start=start, step=step, count=count)
        )

    @property
    def native_frequencies(self) -> NativeFrequencySpec:
        """Returns the frequencies swept in it's native representation

        :return: The frequency specification using start, step and count.
        """
        return self._stub.GetFreqSpec(Empty())

    def set_frequency_span(self, center: float, span: float):
        """Set the frequency span keeping the number of sample point currently selected constant.

        :param center: The center frequency in Hz
        :param span: The frequency span in Hz
        """
        spec = self.native_frequencies
        start = center - span / 2
        count = spec.count
        step = center / count
        self.set_frequencies_native(start, step, count)

    def set_frequency_range(self, start: float, stop: float):
        """Set the frequency range keeping the number of sample points currently selected constant.

        :param start: The start frequency
        :param stop: The stop frequency
        """
        spec = self.native_frequencies
        count = spec.count
        step = (stop - start) / count
        self.set_frequencies_native(start, step, count)

    def set_frequency_step(self, step: float):
        """Sets the frequency step width keeping start and stop frequency constant

        :param step: the step width
        """
        spec = self.native_frequencies
        start = spec.start
        stop = start + spec.count * spec.step
        count = int((stop - start) / step)
        self.set_frequencies_native(start, step, count)

    def set_sample_points(self, points: int):
        """Sets the number of sample points keeping start anf stop frequencies constant

        :param points: The number of frequency points
        """
        spec = self.native_frequencies
        start = spec.start
        stop = start + spec.count * spec.ste
        step = (stop - start) / points
        self.set_frequencies_native(start, step, points)

    @property
    def averages(self) -> int:
        """Get the number of averages used to determine the S-parameter for a given frequency

        :return: The count of averages
        """
        return self._stub.GetAverages(Empty()).value

    @averages.setter
    def averages(self, value: int):
        """Set the number of averages used to determine the S-parameter for a given frequency

        :param value: The number of averages
        """
        self._stub.SetAverages(UInt32Value(value=value))

    @property
    def setup_time(self):
        """Get the time the VNA waits for system build up prior to any measurement

        :return: The time in seconds
        """
        return self._stub.GetSetupTime(Empty()).value

    @setup_time.setter
    def setup_time(self, new_value: float):
        """Set the time the VNA waits for system build up prior to any measurement

        :param new_value: The time in seconds
        """
        self._stub.SetSetupTime(DoubleValue(value=new_value))

    def sweep(self, progress: bool = False) -> tuple[list[int], list[int]]:
        """Sweeps the frequency range provided via

        :param progress: show a progress bar, defaults to False
        :return: A tuple containing magnitude and phase (in that order)
        """
        result_iterator = self._stub.Sweep(Empty())
        data = []
        if progress:
            # We only want tqdm if `progress=True`
            # pylint: disable=import-outside-toplevel
            from tqdm.autonotebook import tqdm

            metadata = result_iterator.initial_metadata()
            total_size = None
            for key, value in metadata:
                if key == "total-size":
                    total_size = int(value)
            with tqdm(total=total_size, unit="point", unit_scale=True) as progress_bar:
                for element in result_iterator:
                    data.extend(element.values)
                    progress_bar.update(len(element.values))
        else:
            for element in result_iterator:
                data.extend(element.values)

        magnitude = [it.magnitude for it in data]
        phase = [it.phase for it in data]
        return (magnitude, phase)

    @property
    def phase_corr(self):
        """Returns the phase correction in seconds that the system uses to compensate delay

        :return: The phase-correction value in seconds
        """
        return self._stub.GetPhaseCorr(Empty()).value

    @phase_corr.setter
    def phase_corr(self, value: float):
        """Set the phase correction value that the system uses to compensate delay

        :param value: The delay in seconds
        """
        self._stub.SetPhaseCorr(DoubleValue(value=value))

    # pylint: disable=too-many-arguments
    def get_resonators(
        self,
        n_resonators: int,
        smoothing_window: int,
        derivative_smoothing_window: int,
        sample_option: int,
        filtering_window: int,
    ):
        """Resonator finder API"""
        options = vna_pb2.ResonatorOptions(
            n_resonators=n_resonators,
            smoothing_window=smoothing_window,
            derivative_smoothing_window=derivative_smoothing_window,
            sample_option=sample_option,
            filtering_window=filtering_window,
        )
        return self._stub.GetResonators(options)

    @property
    def phase_unit(self) -> PhaseUnits:
        """Returns the unit that the phase will be returned in

        :return: The unit, either degree or radian
        """
        unit = self._stub.GetTransmissionOptions(Empty()).magnitude_unit
        if unit == vna_pb2.PhaseUnit.DEGREES:
            return "degree"
        elif unit == vna_pb2.PhaseUnit.RADIAN:
            return "radian"
        else:
            raise ValueError("idk")

    @phase_unit.setter
    def phase_unit(self, unit: PhaseUnits):
        """Sets the unit that the phase will be returned in

        :param unit: The unit
        """
        unit = _phase_unit_to_proto(unit)
        self._stub.SetPhaseUnit(vna_pb2.PhaseUnit_(phase_unit=unit))

    @property
    def magnitude_unit(self) -> MagnitudeUnits:
        """Returns the unit that the magnitude will be returned in

        :return: The unit, either linear or decibel relative to full scale.
        """
        unit = self._stub.GetTransmissionOptions(Empty()).phase_unit
        if unit == vna_pb2.MagnitudeUnit.LINEAR:
            return "linear"
        elif unit == vna_pb2.MagnitudeUnit.DB_FS:
            return "dBFS"
        else:
            raise ValueError("idk")

    @magnitude_unit.setter
    def magnitude_unit(self, unit: MagnitudeUnits):
        """Sets the unit that the magnitude will be returned in

        :param unit: The unit
        """
        unit = _magnitude_unit_to_proto(unit)
        self._stub.SetMagnitudeUnit(vna_pb2.MagnitudeUnit_(magnitude_unit=unit))

    @property
    def transmission_options(self):
        """Return transmission options relevant when sweeping.

        :return: The transmission options - magnitude unit, phase unit and whether to unwrap phase.
        """
        return self._stub.GetTransmissionOptions(Empty())

    def set_transmission_options(
        self,
        magnitude_unit: MagnitudeUnits = "dBFS",
        phase_unit: PhaseUnits = "radian",
        unwrap_phase: bool = False,
    ):
        """Set all of the transmission options relevant when sweeping.

        :param magnitude_unit: The magnitude unit
        :param phase_unit: The phase unit
        :param unwrap_phase: Whether to return the phase wrapped to +- pi or unwrap it
        """
        mag = _magnitude_unit_to_proto(magnitude_unit)
        pha = _phase_unit_to_proto(phase_unit)
        self._stub.SetTransmissionOptions(
            vna_pb2.TransmissionOptions(
                magnitude_unit=mag, phase_unit=pha, unwrap_phase=unwrap_phase
            )
        )

    @property
    def calibration(self) -> Calibration:
        """Returns a reference to the calibration subsystem.
        Read the respective docstring for more information
        """
        return self._calibration


class Calibration:
    """The calibration module provides capabilities to calibrate magnitude and phase response for the VNA component
    using an electrical short as model.
    """

    def __init__(self, stub: vna_pb2_grpc.VNAServiceStub) -> None:
        self._stub = stub

    def calibrate(self, name: str, comment: str = "", fulcrums=10000, averages=10000):
        """Issue a calibration. This assumes that the output of the VNA is physically shorted.

        :param name: The name of the calibration
        :param comment: A comment describing, for example to describe specifics for the setup, defaults to ""
        :param fulcrums: The amount of fulcrums used for the resulting calibration set.
            Less fulcrums is faster but the result is worse, defaults to 10000
        :param averages: The nunmber of averages used for calibration, defaults to 10000
        """
        self._stub.Calibrate(
            vna_pb2.CalibrationOptios(
                name=name, comment=comment, fulcrums=fulcrums, averages=averages
            )
        )

    def remove_calibration(self, name: str) -> bool:
        """Remove a calibration set, given by it's name.
        This operation is final and cannot be undonw.

        :param name: The name of the set to remove
        :return: Whether a set was actually removed. If `False`, the set didn't exist.
        """
        return self._stub.RemoveCalibration(StringValue(value=name)).value

    def available_calibrations(self):
        """Return all available calibrations

        :return: the calibrations as map
        """
        return self._stub.GetAvailableCalibrations(Empty()).values

    def download_calibration(self, name: str):
        """Download a calibration set by it's name. Relevant data will be in JSON format.

        :param name: The name of the set to download
        :return: The set in JSON format
        """
        return self._stub.DownloadCalibration(StringValue(value=name)).json

    def upload_calibration(self, name: str, json: str):
        """Upload a calibration set in JSON format

        :param name: The name of the set
        :param json: The JSON formatted set
        """
        self._stub.UploadCalibration(vna_pb2.CalibrationData(name=name, json=json))

    def set_active_calibration(self, name: str):
        """Set the calibration set that should be used.

        :param name: The name of the set
        """
        self._stub.SetActiveCalibration(StringValue(value=name))

    def get_active_calibration(self) -> str:
        """Return the name of the active calibration set

        :return: The name of the set
        """
        return self._stub.GetActiveCalibration(Empty()).value
