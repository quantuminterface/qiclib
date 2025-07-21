from qiclib.code.qi_jobs import QiCells, QiJob, Recording
from qiclib.code.qi_sample import QiSample


def test_initial_offset_re_applied():
    sample = QiSample(1)
    sample[0]["offset"] = 100e-9

    with QiJob() as job:
        q = QiCells(1)
        Recording(q[0], duration=10e-6, offset=q[0]["offset"])

    job._build_program(sample)
    assert job.cells[0]._initial_rec_offset == 100e-9

    sample[0]["offset"] = 200e-9
    job._build_program(sample)
    assert job.cells[0]._initial_rec_offset == 200e-9
