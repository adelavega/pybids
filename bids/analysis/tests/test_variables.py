from bids.grabbids import BIDSLayout
# from bids.analysis.variables.base import Run, Session, Subject, Dataset
import pytest
from os.path import join, dirname, abspath
from bids import grabbids
from bids.analysis import load_variables
from bids.analysis.variables import (merge_variables, DenseRunVariable,
                                     SparseRunVariable, SimpleVariable)
from bids.analysis.variables.entities import RunInfo
import numpy as np
import pandas as pd
import uuid
# # from grabbit import merge_layouts
# import tempfile
# import shutil


def generate_DEV(name='test', sr=20, duration=480):
    n = duration * sr
    values = np.random.normal(size=n)
    ent_names = ['task', 'run', 'session', 'subject']
    entities = {e: uuid.uuid4().hex for e in ent_names}
    image = uuid.uuid4().hex + '.nii.gz'
    run_info = RunInfo(1, entities, duration, 2, image)
    return DenseRunVariable('test', values, run_info, 'dummy', sr)


@pytest.fixture(scope="module")
def layout1():
    mod_file = abspath(grabbids.__file__)
    path = join(dirname(mod_file), 'tests', 'data', 'ds005')
    layout = BIDSLayout(path)
    return layout


@pytest.fixture(scope="module")
def layout2():
    mod_file = abspath(grabbids.__file__)
    path = join(dirname(mod_file), 'tests', 'data', '7t_trt')
    layout = BIDSLayout(path)
    return layout


def test_dense_event_variable_init():
    dev = generate_DEV()
    assert dev.sampling_rate == 20
    assert dev.run_info[0].duration == 480
    assert dev.source == 'dummy'
    assert len(dev.values) == len(dev.entities)


def test_dense_event_variable_resample():
    dev = generate_DEV()
    dev2 = dev.clone().resample(sampling_rate=40)
    assert len(dev2.values) == len(dev2.entities)
    assert len(dev2.values) == 2 * len(dev.values)


def test_merge_wrapper():
    dev = generate_DEV()
    data = pd.DataFrame({'amplitude': [4, 3, 2, 5]})
    sev = SimpleVariable('simple', data, 'dummy')
    # Should break if asked to merge different classes
    with pytest.raises(ValueError) as e:
        merge_variables([dev, sev])
    assert "Variables of different classes" in str(e)


def test_sparse_run_variable_to_dense(layout1):
    dataset = load_variables(layout1, 'events', scan_length=480)
    runs = dataset.get_runs(subject='01', session=1)
    var = runs[0].variables['RT']
    dense = var.to_dense(20)
    assert isinstance(dense, DenseRunVariable)
    assert dense.values.shape == (9600, )
    assert len(dense.run_info) == len(var.run_info)
    assert dense.source == 'events'


def test_merge_simple_variables(layout2):
    dataset = load_variables(layout2, 'sessions')
    variables = [s.variables['panas_sad'] for s in dataset.children.values()]
    n_rows = sum([len(c.values) for c in variables])
    merged = merge_variables(variables)
    assert len(merged.values) == n_rows
    assert merged.entities.columns.equals(variables[0].entities.columns)
    assert variables[3].values.iloc[1] == merged.values.iloc[7]


def test_merge_sparse_run_variables(layout1):
    dataset = load_variables(layout1, 'events', scan_length=480)
    runs = dataset.get_runs()
    variables = [r.variables['RT'] for r in runs]
    n_rows = sum([len(c.values) for c in variables])
    merged = merge_variables(variables)
    assert len(merged.values) == n_rows
    assert merged.entities.columns.equals(variables[0].entities.columns)


def test_merge_dense_run_variables(layout2):
    variables = [generate_DEV() for i in range(20)]
    variables += [generate_DEV(duration=400) for i in range(8)]
    n_rows = sum([len(c.values) for c in variables])
    merged = merge_variables(variables)
    assert len(merged.values) == n_rows
    assert merged.entities.columns.equals(variables[0].entities.columns)
