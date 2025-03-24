# qiclib Python package

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pipeline status](https://gitlab.kit.edu/kit/ipe-sdr/ipe-sdr-dev/software/qiclib/badges/master/pipeline.svg)](https://gitlab.kit.edu/kit/ipe-sdr/ipe-sdr-dev/software/qiclib/-/commits/master)
[![coverage report](https://gitlab.kit.edu/kit/ipe-sdr/ipe-sdr-dev/software/qiclib/badges/master/coverage.svg)](https://gitlab.kit.edu/kit/ipe-sdr/ipe-sdr-dev/software/qiclib/-/commits/master)

qiclib is Quantum Interface's official Python client for the QiController.

The QiController is currently developed at the [Institute for Data Processing and Electronics](https://ipe.kit.edu/) from [Karlsruhe Institute of Technology (KIT)](https://www.kit.edu/).

## Installing

To install the `qiclib` and make it available system-wide using, use:

```shell
pip install qiclib
```

or

```shell
uv pip install qiclib
```

## Developing

**Important:** This section describes development using the internal, Gitlab based repository, not the public GitHub based mirror.

The recommended development process involves [uv](https://docs.astral.sh/uv/). Install the tool as mentioned in the [documentation](https://docs.astral.sh/uv/getting-started/installation/).

To install, clone this repository and initialize it using `uv`;

```shell
git clone git@gitlab.kit.edu:kit/ipe-sdr/ipe-sdr-dev/software/qiclib.git --recurse-submodules
cd qiclib
uv sync
```

You can then refer to the [Testing](#testing) section to verify that the setup is correct.

The usage of [pre-commit](https://pre-commit.com) is recommended and you can install it using

```shell
uvx pre-commit install
```

### Visual Studio Code

This repository includes settings and recommended extensions for [VSCode](https://code.visualstudio.com). If you open this repository using VSCode for the first time, a popup will appear on the bottom-right corner asking for permission to install recommended extensions.
If you want to inspect these recommendations or have accidentally discarded the notification, go to the Notifications tab and search for `@recommended`.

## Using jupyter

If you have installed `qiclib` system-wide, or in a virtual environment, you can import `qiclib` simply by calling `import qiclib`.
Example notebooks can be found in the [examples](./examples/) subdirectory.

### Development with jupyter

By default, `uv sync` will also install jupyter so no further setup is required.

It is recommended to store notebooks in the [Notebooks](./Notebooks/) folder that are used for development and testing purposes exclusively.
This folder is ignored in `git`, but uses the same virtual environment as `qiclib`.

## Testing

Run

```shell
uv run pytest
```

to run all unittests

## Getting Started

The QiController needs to be powered and connected to the same network as the control computer. It can then be accessed via its IP address or host name.

Everything is based on the QiController driver class, so simply import qiclib and establish a connection:

```python
import qiclib as ql
from qiclib.code import *

qic = ql.QiController('IP ADDRESS OR HOST NAME')
```

qiclib includes a high-level description language called QiCode (already imported using the second line above). With it, you can conveniently specify your experiments in an easy and intuitive manner.

QiCode lets you specify experiments in a generic way, so-called QiJobs, and then execute them on your superconducting qubit chip.
The physical properties of your sample are stored inside a `QiSample` object.
The sample can consist of one or more cells.
Each cell corresponds to a qubit and defines all relevant properties for this qubit.
This can be pulse lengths, frequencies, but also other experiment-related parameters.

For this introduction, we will stick with one qubit and thus one cell:

```python
sample = QiSample(1) # 1 cell/qubit only
sample[0]["rec_pulse"] = 416e-9 # s readout pulse length
sample[0]["rec_length"] = 400e-9 # s recording window size
sample[0]["rec_frequency"] = 60e6 # Hz readout pulse frequency
sample[0]["manip_frequency"] = 80e6 # Hz control pulse frequency
```

One can define as many properties as one likes.
The naming convention of these properties is left completely up to you.
However, if you want to use pre-built experiments from qiclib, you should use the same property names as are used there.
You can also store qubit-related characteristics, like decay times and further information which are not needed for the experiments.
As the sample can be exported as JSON file and imported again later, this can become quite useful.

In the sample, we already provided some information on how our readout pulse should look like and how long our recording window should be.
At the beginning, one now typically wants to calibrate the electrical delay of the readout pulse through the experimental setup.
qiclib offers an automated scheme for this purpose, optimizing for the highest signal amplitude at the IF frequency.
Of course, manual calibration (see other methods inside `ql.init`) is also possible.

```python
ql.init.calibrate_readout(qic, sample, averages=1000)
```

This will perform multiple experiments on the QiController to determine the electrical delay and to record the final readout window.
It will also plot you the resulting data using matplotlib.
The optimal delay will be stored as `"rec_offset"` inside the sample object so it can be used for the following experiments.

Congratulation! You have successfully put the QiController into operation. Now you can continue reading how to use QiCode for your custom experiments.

## QiCode Usage

The basic commands and classes that are provided for building your experiments with QiCode are:

- `QiPulse(length, shape, amplitude, phase)`

  Creates a pulse object that can be used in other commands

- `Play(cell, pulse)`

  Play the given `pulse` at the manipulation output for the given `cell`

- `PlayReadout(cell, pulse)`

  Same as `Play` but for the readout pulse output

- `Recording(cell, duration, offset, save_to, state_to)`

  Performs a recording at the input of the cell of given `duration` and `offset` (electrical delay). Typically used directly after a `PlayReadout` command. With `save_to`, the result data can be stored and labeled by the given string. With `state_to`, the obtained state can be saved to a QiVariable.

- `Wait(cell, delay)`

  Waits the given `delay` in the execution time of the `cell` before continuing with the next command.

- `QiVariable(type)`, `QiTimeVariable()` and `QiStateVariable()`

  Creates a variable that can be used during the control flow or to temporarily store a measured qubit state.

Furthermore, there are context managers (which are used with the `with` statement) to represent control logic:

- `with If(condition):`

  Conditional branching, only executes the indented block that follows if the condition is true.

- `with Else():`

  Can follow after `with If` and does exactly what you would expect it to do.

- `with ForRange(variable, start, end, step):`

  The passed `variable` will be looped from `start` to `end` (excluded) with `step` increments. The following idented block will be repeated for each value of `variable`.

One nice thing about QiCode is that you can define reusable building blocks for your experiments. We call these QiGates and annotate them accordingly (`@QiGate`). Together with the property names of the `QiSample`, one can really reuse them for different qubits without any adaptations to the gates:

```python
@QiGate
def Readout(cell: QiCell, save_to: str = None):
    PlayReadout(cell, QiPulse(cell["rec_pulse"], frequency=cell["rec_frequency"]))
    Recording(
        cell,
        duration=cell["rec_length"],
        offset=cell["rec_offset"],
        save_to=save_to
    )

@QiGate
def PiPulse(cell: QiCell):
    Play(cell, QiPulse(cell["pi"], frequency=cell["manip_frequency"]))

@QiGate
def Thermalize(cell: QiCell):
    Wait(cell, 5 * cell["T1"])
```

As with the basic commands, the QiGates typically start by defining the cell on which they act. This is not strictly required though. Furthermore, also multi-qubit gates can be implemented in the same manner acting on multiple cells.

Now, one can define a first experiment. In QiCode, experiments are called `QiJob` and written in an abstract way so they can be easily reused for different samples. Let us consider a Rabi experiment:

```python
# Commands are always encapsulated within the QiJob context
with QiJob() as rabi:
    # First, we define how many qubits the experiment requires
    q = QiCells(1)
    # Rabi consists of variable length excitation pulses,
    # so we need to create a time variable
    length = QiTimeVariable()
    # The variable can then be changed within a for loop
    with ForRange(length, 0, 1e-6, 20e-9):
        # Output the manipulation pulse with variable length
        Play(q[0], QiPulse(length, frequency=q[0]["manip_frequency"]))
        # Perform a consecutive readout (using the above QiGate)
        # The data can later by accessed via the specified name "result"
        Readout(q[0], save_to="result")
        # Wait for the qubit to thermalize (also a QiGate)
        Thermalize(q[0])
```

The `QiCells` object inside the `QiJob` only acts as placeholder for the real qubit sample and will be replaced by it once we run the experiment.
The placeholder specifies how many cells/qubits the experiment is written for, so one in this case.
All cell properties that are needed for the Rabi experiment are already defined in our `sample` above where we just calibrated the readout.
So we can just run the job by passing both `QiController` and `QiSample` object to it:

```python
rabi.run(qic, sample, averages=1000)
data = rabi.cells[0].data("result")
```

This will execute the whole job including the for loop and repeat and average the whole experiment 1000 times. The resulting `data` object will look like this:

```python
[
    # Averaged I results (len = 50 in this example)
    np.array([...]),
    # Averaged Q results (same len)
    np.array([...])
]
```

Job description for the most common experiments are readily available as `ql.jobs.*` functions, like `ql.jobs.Rabi` or `ql.jobs.T1`.

More information on QiCode can be found [here](src/qiclib/code/README.md).

## Qkit Integration

<a href="https://github.com/qkitgroup/qkit" target="_blank"><img src="https://raw.githubusercontent.com/qkitgroup/qkit/master/images/Qkit_Logo.png" width="100" /></a>

This package is best used together with the quantum measurement suite [Qkit](https://github.com/qkitgroup/qkit) which has to be installed separately. Stand-alone usage of qiclib with reduced capabilities is also possible.

After installation, convenience features like storing sample objects (see `qkit.measure.samples_class`) and displaying progress bars within Jupyter(lab) notebooks are available.

The following code demonstrates how both packages can be easily combined to perform a Rabi experiment (based on the code above):

```python
from qkit.measure.timedomain.measure_td import Measure_td

# We use the rabi QiJob from above and extract an experiment object from it
exp = rabi.create_experiment(qic, sample, averages=1000)

# Create Qkit measurement object and pass an adapter object as Qkit sample
m = Measure_td(exp.qkit_sample)
m.set_x_parameters(exp.time_range(0, 1e-6, 20e-9), 'pulse_length', None, 's')
m.dirname = 'rabi'

# Start the measurement, and lean back:
m.measure_1D_AWG(iterations=1)
```

Everything else is handled for you by Qkit and qiclib! Have fun performing your experiments.

## Contributing

Ideas for new features and bug reports are highly welcome. Please use the issue tracker for this purpose.

## LICENSE

qiclib is released under the terms of the **GNU General Public License** as published by the Free Software Foundation, either version 3 of the License, or any later version.

Please see the [COPYING](COPYING) files for details.
