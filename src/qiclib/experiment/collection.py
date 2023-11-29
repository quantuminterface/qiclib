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
"""Collection of most QiController experiment classes.

.. note::
    Even more experiment classes might be available in the `qiclib.experiment`
    submodule, the common place for all integrated experiments in `qiclib`.

Be aware that, if they are not listed below, they cannot be accessed via
`qiclib.exp` and need to be imported separately.

Available experiments
---------------------

- `qiclib.experiment.active_reset_t1.ActiveResetT1`
- `qiclib.experiment.autoconf_readout.AutoconfReadout`
- `qiclib.experiment.benchmarking.Benchmarking`
- `qiclib.experiment.g1_correlation.G1Correlation`
- `qiclib.experiment.g1_correlation_conv.G1CorrelationConv`
- `qiclib.experiment.g1_meas_setuptest.G1setuptest`
- `qiclib.experiment.g2_correlation.G2Correlation`
- `qiclib.experiment.g2_correlation_conv.G2CorrelationConv`
- `qiclib.experiment.inverted_t1.InvertedT1`
- `qiclib.experiment.iq_clouds.IQClouds`
- `qiclib.experiment.iq_clouds_multi_qfb.IQCloudsMultiQFB`
- `qiclib.experiment.iq_clouds_qfb.IQCloudsQFB`
- `qiclib.experiment.iq_clouds_qfb_decay.IQCloudsQFBDecay`
- `qiclib.experiment.iq_clouds_ramsey.IQCloudsRamsey`
- `qiclib.experiment.readout.IQFtReadout`
- `qiclib.experiment.readout.IQRawReadout`
- `qiclib.experiment.multi_pi.MultiPi`
- `qiclib.experiment.multi_pi_t1.MultiPiT1`
- `qiclib.experiment.rabi.Rabi`
- `qiclib.experiment.rabi_drag.RabiDRAG`
- `qiclib.experiment.rabi_short.RabiShort`
- `qiclib.experiment.ramsey.Ramsey`
- `qiclib.experiment.resonator_ringup.ResonatorRingup`
- `qiclib.experiment.resonator_ringup_window.ResonatorRingupWindow`
- `qiclib.experiment.single_pulse.SinglePulse`
- `qiclib.experiment.spinecho.SpinEcho`
- `qiclib.experiment.t1.T1`
- `qiclib.experiment.test_two_pulse.TestTwoPulse`
- `qiclib.experiment.quantum_jumps.QuantumJumps`
- `qiclib.experiment.quantum_jumps_long.QuantumJumpsLong`
- `qiclib.experiment.qubit_times.QubitTimes`
- `qiclib.experiment.qubit_times_qkit.QubitTimesQkit`

"""
# TODO Move untested/special experiments to own submodule
