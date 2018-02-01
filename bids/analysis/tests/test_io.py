from bids.grabbids import BIDSLayout
from bids.analysis.variables import (SparseEventColumn, SimpleColumn,
                                     load_variables)
from bids.analysis.variables.base import Run, Dataset
import pytest
from os.path import join, dirname, abspath
from bids import grabbids


@pytest.fixture
def layout():
    mod_file = abspath(grabbids.__file__)
    path = join(dirname(mod_file), 'tests', 'data', 'ds005')
    return BIDSLayout(path)


def test_load_events(layout):
    dataset = load_variables(layout, 'events', scan_length=480)
    runs = dataset.get_runs(subject='01')
    assert len(runs) == 3
    assert isinstance(runs[0], Run)
    variables = runs[0].variables
    assert len(variables) == 10
    targ_cols = {'parametric gain', 'PTval', 'trial_type', 'respnum'}
    assert not (targ_cols - set(variables.keys()))
    assert isinstance(variables['parametric gain'], SparseEventColumn)
    assert variables['parametric gain'].entities.shape == (86, 4)


def test_load_participants(layout):
    dataset = load_variables(layout, 'participants')
    assert isinstance(dataset, Dataset)
    assert len(dataset.variables) == 2
    assert {'age', 'sex'} == set(dataset.variables.keys())
    age = dataset.variables['age']
    assert isinstance(age, SimpleColumn)
    assert age.entities.shape == (16, 1)
    assert age.values.shape == (16,)
