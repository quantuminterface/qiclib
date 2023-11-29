Getting Started
===============

After powering on the QiController and connecting it to the same network as the
control computer, it can be accessed via its IP address or host name:

.. code-block:: python

    import qiclib as ql
    qic = ql.QiController('IP ADDRESS OR HOST NAME')

The whole QiController can be accessed using the properties of this object.
The most important components are:

- :class:`qic.sequencer <qiclib.hardware.sequencer.Sequencer>`:
  Controls the experiment execution with nanosecond precision.

- :class:`qic.recording <qiclib.hardware.recording.Recording>`:
  Performs recording and demodulation of system response signals.

- :class:`qic.readout <qiclib.hardware.pulsegen.PulseGen>`:
  Generates pulses for the readout channel.

- :class:`qic.manipulation <qiclib.hardware.pulsegen.PulseGen>`:
  Generates pulses to control the qubit.

- :class:`qic.taskrunner <qiclib.hardware.taskrunner.TaskRunner>`:
  Provides high-level control using a real-time subsystem.

For a more detailed introduction into the QiController architecture, refer to :class:`qiclib.hardware`.

Interacting with the controller
-------------------------------

In general, most configuration involves simply assigning values to properties. At the same time, reading these properties will fetch the current value directly from the controller.
For example, to set the number of repetitions/averages the controller shall perform for each experiment, you can simply perform an assignment like the following:

.. code-block:: python

   qic.sequencer.averages = 1000

   # The value is now set on the controller and can be queried the same way:
   print(f'Average count is currently set to {qic.sequencer.averages}!')

Interacting with the QiController is as easy as that.

Describing the experimental setup
---------------------------------

The driver also stores a (Qkit) sample object which describes the experimental setup.
A previous sample object can be loaded with
:python:`qic.sample.load('path')` (only available with Qkit).

For this demonstration, we initialize the most important properties with some initial values:

.. code-block:: python

   qic.sample.tpi = 160e-9              # pi pulse duration
   qic.sample.tpi2 = 80e-9              # pi/2 pulse duration
   qic.sample.T_rep = 10e-6             # delay to thermalize qubit
   qic.sample.rec_if_frequency = 60e6   # IF frequency for readout pulse
   qic.sample.manip_if_frequency = 80e6 # IF frequency for control pulse

See :class:`qiclib.packages.qkit_polyfill.SampleObject` for a list of available parameters to adjust.

Performing a first experiment
-----------------------------

:python:`qiclib` offers a collection of common experiments (available as :python:`qiclib.exp`).
At the beginning, one typically would like to calibrate the delay of the readout pulse through the experimental setup.
qiclib offers an automated scheme for this purpose,
optimizing for the highest signal amplitude at the IF frequency.
Of course, manual calibration (see :class:`qiclib.hardware.recording`) is also possible.

.. code-block:: python

   ql.exp.AutoconfReadout(
       qic, # The first argument is always the QiController itself
       pulse_length=400e-9,
       recording_length=400e-9
   ).run()

This will configure a 400ns recording pulse and a recording window of the same length.
Using matplotlib, it will also output multiple plots illustrating the optimization process for the latency, as well as a time trace of the final readout window.

Congratulation! You have successfully put the QiController into operation. Now you can continue with your experiment-specific experiments.
