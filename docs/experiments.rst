Experiments
===========

.. warning::

  The experiment syntax described herein contains mostly legacy content. Please refer to :ref:`qi_code`
  for the new way to describe experiments with the QiController.

The following section will give a brief overview over available
experiments and how to use them. For more details, please refer
to :meth:`qiclib.experiment`.

General usage
-------------

All experiments for the QiController are derived from a common base
class, :class:`~qiclib.experiment.base.BaseExperiment`. Thereby, all experiments
are structured the same way providing the following three main methods:

- :func:`qiclib.experiment.base.BaseExperiment.configure` to load the
  experiment configuration onto the QiController.

- :func:`qiclib.experiment.base.BaseExperiment.record` to start the experiment
  and return the measurement result at the end.

- :func:`qiclib.experiment.base.BaseExperiment.run` which combines the two
  commands above and also returns the measurement result.

Additionally, you can access a Qkit readout object via the
:attr:`qiclib.experiment.base.BaseExperiment.readout` attribute that can be passed
to Qkit's time-domain measurement class (:python:`Measure_td`) in order to perform
the whole experiment including configuration, recording and data storage
with Qkit.

Pre-defined experiments
-----------------------

The following list only provides an incomplete overview over the
most common available experiments. For a complete list, have a look
at :mod:`qiclib.experiment.collection`. All of the following experiments
can be accessed using the :python:`qiclib.exp`: collection.

- :class:`~qiclib.experiment.readout.IQFtReadout`: Single readout operation,
  returns the demodulated IQ value as amplitude and phase.
  Together with Qkit, this is enough to perform a Pseudo-VNA measurement to find the resonator frequency.
- :class:`~qiclib.experiment.readout.IQRawReadout`: Single readout operation,
  but returns the (averaged) raw IQ time trace without demodulation.
- :class:`~qiclib.experiment.autoconf_readout.AutoconfReadout`: Experiment to
  determine the delay of the readout pulse through the setup.
  This is typically one of the first experiments to perform after starting
  the QiController.
- :class:`~qiclib.experiment.single_pulse.SinglePulse`: Performs a single manipulation pulse before performing the readout.
  Together with Qkit, this is enough to perform a simple two-tone measurement to estimate the qubit frequency.
- :class:`~qiclib.experiment.rabi.Rabi`: Applies a manipulation pulse with variable
  length to obtain the duration of pi and pi/2 operations.
- :class:`~qiclib.experiment.t1.T1`: Excites the qubit by a pi pulse followed by a variable delay to determine the energy relaxation time \(T_1\).
- :class:`~qiclib.experiment.ramsey.Ramsey`: Performs two pi/2 pulses separated by a variable delay to determine the decoherence time \(T_2^R\) and fine-tune the pi pulse duration.
- :class:`~qiclib.experiment.spinecho.SpinEcho`: Performs a Ramsey experiment but inserts an additional pi pulse in between the pi/2 pulses. Can be used to determine the decoherence time \(T_2^E\).
- :class:`~qiclib.experiment.iq_clouds.IQClouds`: Performs repetitive qubit measurements and returns each IQ result. Can be used to generate a histogram in the IQ plane.
- :class:`~qiclib.experiment.quantum_jumps.QuantumJumps`: Performs repetitive single-shot qubit measurements and returns the states (each 0/1) of these consecutive measurements. All the data reduction happens directly on the QiController.
- :class:`~qiclib.experiment.iq_clouds_qfb.IQCloudsQFB`: Performs a configurable active reset operation on the qubit and returns the IQ result of a consecutive readout. Otherwise identical to `qiclib.experiment.iq_clouds.IQClouds`.

Writing your own experiment
---------------------------

.. todo:: Provide a short description

For more information, refer to :mod:`qiclib.experiment` and have a look at the source code of the :class:`~qiclib.experiment.base.BaseExperiment` class.
