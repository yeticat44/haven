from unittest.mock import MagicMock
from bluesky import plans as bp
from bluesky.callbacks import CallbackBase
from ophyd.sim import det, motor, SynAxis

from haven import RunEngine, plans, baseline_decorator, baseline_wrapper


def test_baseline_wrapper(sim_registry):
    # Create a test device
    motor_baseline = SynAxis(name="baseline_motor", labels={"motors"})
    sim_registry.register(motor_baseline)
    # Set up a callback to motor streams generated by runengine
    cb = CallbackBase()
    cb.start = MagicMock()
    cb.descriptor = MagicMock()
    cb.event = MagicMock()
    cb.stop = MagicMock()
    RE = RunEngine(connect_databroker=False)
    plan = bp.count([det], num=1)
    plan = baseline_wrapper(plan, devices="motors")
    RE(plan, cb)
    # Check that the callback has the baseline stream inserted
    assert cb.start.called
    assert cb.descriptor.call_count > 1
    baseline_doc = cb.descriptor.call_args_list[0][0][0]
    primary_doc = cb.descriptor.call_args_list[1][0][0]
    assert baseline_doc["name"] == "baseline"
    assert "baseline_motor" in baseline_doc["data_keys"].keys()


def test_baseline_decorator(sim_registry):
    """Similar to baseline wrapper test, but used as a decorator."""
    # Create the decorated function before anything else
    func = baseline_decorator(devices="motors")(bp.count)
    # Create a test device
    motor_baseline = SynAxis(name="baseline_motor", labels={"motors"})
    sim_registry.register(motor_baseline)
    # Set up a callback to motor streams generated by runengine
    cb = CallbackBase()
    cb.start = MagicMock()
    cb.descriptor = MagicMock()
    cb.event = MagicMock()
    cb.stop = MagicMock()
    RE = RunEngine(connect_databroker=False)
    plan = func([det], num=1)
    RE(plan, cb)
    # Check that the callback has the baseline stream inserted
    assert cb.start.called
    assert cb.descriptor.call_count > 1
    baseline_doc = cb.descriptor.call_args_list[0][0][0]
    primary_doc = cb.descriptor.call_args_list[1][0][0]
    assert baseline_doc["name"] == "baseline"
    assert "baseline_motor" in baseline_doc["data_keys"].keys()


def test_metadata():
    """Similar to baseline wrapper test, but used as a decorator."""
    # Set up a callback to motor streams generated by runengine
    cb = CallbackBase()
    cb.start = MagicMock()
    cb.descriptor = MagicMock()
    cb.event = MagicMock()
    cb.stop = MagicMock()
    RE = RunEngine(connect_databroker=False)
    plan = bp.count([det], num=1)
    RE(plan, cb)
    # Check that the callback has the correct metadata
    assert cb.start.called
    assert cb.start.call_count == 1
    start_doc = cb.start.call_args[0][0]
    assert "versions" in start_doc.keys()
    versions = start_doc["versions"]
    assert "haven" in versions.keys()
    assert versions["haven"] == "0.1.0"
    assert "bluesky" in versions.keys()
