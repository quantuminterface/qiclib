.. _qi_code:

QiCode
======

QiCode is an experiment description language that uses python syntax to describe experiments.

Getting Started
---------------

The necessary functions can be imported through:

.. code-block:: python

    from qiclib.code import *

At first a :class:`~qiclib.code.qi_jobs.QiJob` has to be created, and the necessary cells have to be defined through :class:`~qiclib.code.qi_jobs.QiCells`.

.. code-block:: python

    with QiJob() as do_nothing:
        q = QiCells(1)
        Wait(q[0], 200e-9)

Optional parameters at QiJob initialisation include :python:`skip_nco_synch = False` to skip the first NCO Synch trigger and :python:`nco_sync_length = 0` to define the length of the NCO Synch Trigger.

.. code-block:: python

    with QiJob() as nested_loop:
        q = QiCells(1)
        p1_length = QiTimeVariable()
        iterations = QiVariable(int)
        result = QiResult()

        with ForRange(p1_length, 0, 52e-9, 4e-9):
            with ForRange(iterations, 0, 5):
                PlayReadout(q[0], QiPulse(length=p1_length))
                Play(q[0], QiPulse(length=p1_length))
                Recording(q[0], result)
                Wait(q[0], 0.5)

Variables inside a job are defined by using :class:`~qiclib.code.qi_jobs.QiTimeVariable` or :class:`~qiclib.code.qi_jobs.QiVariable`. Resultboxes are
generated with :class:`~qiclib.code.qi_jobs.QiResult` and registered for the job (Currently only one Resultbox per job). To react to the state of a qubit, a :class:`~qiclib.code.qi_jobs.QiStateVariable` var_state can be declared and used in a recording command: :python:`Recording(cell, state_to=state_variable)`

Inside the QiJob context manager the cell commands :class:`~qiclib.code.qi_jobs.Sync`, :class:`~qiclib.code.qi_jobs.Play`, :class:`~qiclib.code.qi_jobs.PlayReadout`, :class:`~qiclib.code.qi_jobs.Wait`, :class:`~qiclib.code.qi_jobs.Assign` and :class:`~qiclib.code.qi_jobs.Recording` can be used.

Pulses are defined via the :class:`~qiclib.code.qi_pulse.QiPulse` constructor.

The :class:`~qiclib.code.qi_jobs.ForRange` context manager can be used as the python equivalent of :python:`for x in range()`. If used with a :python:`QiTimeVariable`, and starting with a time of 0, the first loop is unrolled by the compiler, excluding all commands exclusively using the defined :python:`QiTimeVariable`.

.. code-block:: python

    with QiJob() as conditional:
        q = QiCells(1)
        p1_length = QiTimeVariable(250e-9)
        iterations = QiVariable(int)
        result = QiResult()

        with ForRange(iterations, 0, 5):
            with If(iterations == 3):
                PlayReadout(q[0], QiPulse(length=p1_length))
            with Else():
                Play(q[0], QiPulse(length=p1_length))

            Wait(q[0], 0.5)

Conditionals can be used with the :class:`~qiclib.code.qi_jobs.If` and :class:`~qiclib.code.qi_jobs.Else` Context managers.

.. code-block:: python

    with QiJob() as parallel_pulse:
        q = QiCells(1)
        with Parallel():
            PlayReadout(q[0], QiPulse(length=128e-9))
        with Parallel():
            Play(q[0], QiPulse(length=52e-9))
            Wait(q[0], 24e-9)
            Play(q[0], QiPulse(length=52e-9))

        Wait(q[0], 0.5)

Commands :class:`~qiclib.code.qi_jobs.Play`, :class:`~qiclib.code.qi_jobs.PlayReadout`, :class:`~qiclib.code.qi_jobs.Recording` and :class:`~qiclib.code.qi_jobs.Wait` can be used inside a :class:`~qiclib.code.qi_jobs.Parallel` context manager, to execute the commands simultaneously. A program sequence will be generated interlacing both bodies of the context manager. Variable lengths can also be used inside a context manager, but special care has to be given
not to overlap multiple pulses. Parallel context managers should not be used with variable lengths inside a ForRange context manager, instead unroll the cases.

.. code-block:: python

    with QiJob() as pi_pulse:
        q = QiCells(1)

        Play(q[0], QiPulse(length = q[0]["pi_pulse"]))

        Wait(q[0], 0.5)

Jobs can be defined with cell properties as lengths. Before running the job, the properties need to be resolved, for this hand over the desired cell/cells containing the relevant properties, which are then inserted at the relevant places:

.. code-block:: python

    sample1 = QiCells(1)
    sample2 = QiCells(1)

    sample1["pi_pulse"] = 100e-9
    sample2["pi_pulse"] = 150e-9

    pi_pulse.run(qic, sample1, averages = 1)
    pi_pulse.run(qic, sample2, averages = 1)

To run a program simply call the :python:`run` method of the :python:`QiJob`. The first execution will play a pulse of 100ns, the second a pulse of 150e-9. Multiple cells can be defined for a single job, per default, the job for the first defined cell is executed (change parameter :python:`cell_index` of :python:`run()` for other cells).

.. code-block:: python

    with QiJob() as parallel_pulse:
        q = QiCells(2)
        p1_length = QiTimeVariable()
        iterations = QiVariable(int)

        Assign(p1_length, 250e-9)

        Play(q[0], QiPulse(length=p1_length))
        Play(q[1], QiPulse(length=p1_length))

        Wait(q[0], 0.5)
        Wait(q[1], 0.5)

When using multiple cells inside a :python:`QiJob`, commands are generated per cell.

.. code-block:: python

    with QiJob() as parallel_pulse:
        q = QiCells(2)
        p1_length = QiTimeVariable()
        iterations = QiVariable(int)

        Assign(p1_length, 250e-9)

        Play(q[0], QiPulse(length=p1_length))

        Sync(q[0], q[1])
        Play(q[0], QiPulse(length=p1_length))
        Play(q[1], QiPulse(length=p1_length))

        Wait(q[0], 0.5)
        Wait(q[1], 0.5)

To ensure commands are executed in parallel use :class:`~qiclib.code.qi_jobs.Sync`. The compiler inserts wait times to the cell q[1] in this case so the Play-pulses after the :python:`Sync` are
executed in parallel. When using a :python:`ForRange`, :python:`If` or :python:`Parallel` context manager, multiple cells are synced too, before entering. After the execution of a :python:`ForRange` loop, another synchronisation happens. Synchronisation is currently implemented by inserting halt commands, so the use of :python:`If` context managers invalidates automatic synching, requiring input from the user.
