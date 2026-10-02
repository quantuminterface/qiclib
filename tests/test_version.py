# Copyright © 2017-2024 Quantum Interface (quantuminterface@ipe.kit.edu)
# Lukas Scheller, IPE, Karlsruhe Institute of Technology
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
from pathlib import Path

import pytest
from packaging.requirements import Requirement

import qiclib


def test_has_version():
    assert isinstance(qiclib.__version__, str)
    assert isinstance(qiclib.__version_tuple__, tuple)


def test_qicode_matches_workspace():
    tomllib = pytest.importorskip("tomllib")  # Python >= 3.11

    root = Path(__file__).parent.parent
    qiclib_project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    qicode_project = tomllib.loads(
        (root / "qicode" / "python" / "pyproject.toml").read_text()
    )["project"]

    requirements = [Requirement(dep) for dep in qiclib_project["dependencies"]]
    (qicode_req,) = [req for req in requirements if req.name == "qicode"]
    assert str(qicode_req.specifier) == f"=={qicode_project['version']}"
