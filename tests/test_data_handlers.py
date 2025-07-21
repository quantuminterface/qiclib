import numpy as np
from pytest import fixture

from qiclib.code import *
from qiclib.experiment.qicode.data_handler import DataHandler, DataProvider


@fixture
def iqcloud_handler_factory():
    return DataHandler.get_factory_by_name("iqcloud")


def test_iqcloud_handler_one_average(iqcloud_handler_factory):
    with QiJob() as job:
        q = QiCells(1)
        Recording(q[0], duration=1e-6, save_to="result")

    job._build_program()

    mock_data = [
        (
            np.array([1], dtype=np.int32),
            np.array([0], dtype=np.int32),
        )
    ]
    data_provider = DataProvider.create(result=mock_data, use_taskrunner=False)
    iqcloud_handler = iqcloud_handler_factory(data_provider, job.cells, 10)
    iqcloud_handler.process_results()
    np.testing.assert_equal(
        job.cells[0].data("result"),
        np.array([1, 0]),
    )


def test_iqcloud_handler_multiple_averages(iqcloud_handler_factory):
    with QiJob() as job:
        q = QiCells(1)
        Recording(q[0], duration=1e-6, save_to="result")

    job._build_program()

    mock_data = [
        (
            np.array([-1, -1, -1, -1, 0, 0, -1, -1, -2, 0], dtype=np.int32),
            np.array([0, -2, 0, -1, -1, 0, -1, -1, 0, 0], dtype=np.int32),
        )
    ]
    data_provider = DataProvider.create(result=mock_data, use_taskrunner=False)
    iqcloud_handler = iqcloud_handler_factory(data_provider, job.cells, 10)
    iqcloud_handler.process_results()
    np.testing.assert_equal(
        job.cells[0].data("result"),
        np.array(
            [[-1, -1, -1, -1, 0, 0, -1, -1, -2, 0], [0, -2, 0, -1, -1, 0, -1, -1, 0, 0]]
        ),
    )


def test_iqcloud_handler_multiple_recordings(iqcloud_handler_factory):
    with QiJob() as job:
        q = QiCells(1)
        f = QiFrequencyVariable()
        with ForRange(f, 0, 400e6, 100e6):
            PlayReadout(q[0], QiPulse(100e-9, frequency=f))
            Recording(q[0], duration=1e-6, save_to="result")

    job._build_program()

    # fmt: off
    mock_data = [(np.array([
        -334, -341, -341, -341, -343, -341, -342,  -37,  -35,  -33,  -36,
        -34,  -35,  -37,  308,  306,  308,  308,  307,  308,  305,  167,
        166,  166,  166,  167,  166,  167
        ], dtype=np.int32),
        np.array([
            -60,  -73,  -77,  -73,  -72,  -73,  -70, -353, -353, -351, -353,
       -355, -353, -352, -141, -141, -137, -141, -141, -138, -143,  233,
        232,  233,  234,  233,  233,  232
        ], dtype=np.int32))]
    # fmt: on
    data_provider = DataProvider.create(result=mock_data, use_taskrunner=False)
    iqcloud_handler = iqcloud_handler_factory(data_provider, job.cells, 7)
    iqcloud_handler.process_results()
    np.testing.assert_equal(
        job.cells[0].data("result"),
        np.array(
            [
                [
                    [-334, -341, -341, -341, -343, -341, -342],
                    [-37, -35, -33, -36, -34, -35, -37],
                    [308, 306, 308, 308, 307, 308, 305],
                    [167, 166, 166, 166, 167, 166, 167],
                ],
                [
                    [-60, -73, -77, -73, -72, -73, -70],
                    [-353, -353, -351, -353, -355, -353, -352],
                    [-141, -141, -137, -141, -141, -138, -143],
                    [233, 232, 233, 234, 233, 233, 232],
                ],
            ]
        ),
    )
