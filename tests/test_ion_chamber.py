import pytest
import time
from unittest import mock

from haven.instrument import ion_chamber
from haven import exceptions
import epics


def test_gain_level(ioc_preamp, ioc_scaler):
    positioner = ion_chamber.SensitivityLevelPositioner(
        f"{ioc_preamp.prefix}SR01", name="positioner"
    )
    positioner.wait_for_connection()
    assert positioner.get(use_monitor=False).sens_value.readback == epics.caget(
        ioc_preamp.pvs["preamp1_sens_num"]
    )
    assert positioner.get(use_monitor=False).sens_unit.readback == epics.caget(
        ioc_preamp.pvs["preamp1_sens_unit"]
    )
    # Move the gain level
    positioner.sens_level.set(12)
    time.sleep(0.1)  # Caproto breaks pseudopositioner status
    # Check that the preamp sensitivities are moved
    assert positioner.get(use_monitor=False).sens_value.readback == 3
    assert positioner.get(use_monitor=False).sens_unit.readback == 1
    # Check that the preamp sensitivity offsets are moved
    assert positioner.get(use_monitor=False).offset_value.readback == 0
    assert positioner.get(use_monitor=False).offset_unit.readback == 1
    # Change the preamp settings
    epics.caput(ioc_preamp.pvs["preamp1_sens_num"], 0)
    epics.caput(ioc_preamp.pvs["preamp1_sens_unit"], 3)
    epics.caput(ioc_preamp.pvs["preamp1_offset_num"], 1)
    epics.caput(ioc_preamp.pvs["preamp1_offset_unit"], 3)
    time.sleep(0.1)
    # Check that the gain level moved
    assert positioner.sens_level.get(use_monitor=False).readback == 27


def test_gain_changes(ioc_preamp, ioc_scaler, sim_registry):
    # Setup the ion chamber and connect to the IOC
    device = ion_chamber.IonChamber(
        prefix=ioc_scaler.prefix,
        preamp_prefix=f"{ioc_preamp.prefix}SR01",
        ch_num=2,
        name="ion_chamber",
    )
    time.sleep(0.01)
    device.wait_for_connection(timeout=20)
    statuses = [
        device.sensitivity.sens_value.set(2),
        device.sensitivity.sens_unit.set(1),
    ]
    [status.wait() for status in statuses]
    assert device.sensitivity.sens_value.get(use_monitor=False).readback == 2
    assert device.sensitivity.sens_unit.get(use_monitor=False).readback == 1
    # Change the gain without changing units
    device.increase_gain().wait()
    assert device.sensitivity.sens_value.get(use_monitor=False).readback == 1
    assert device.sensitivity.sens_unit.get(use_monitor=False).readback == 1
    device.decrease_gain().wait()
    assert device.sensitivity.sens_value.get(use_monitor=False).readback == 2
    assert device.sensitivity.sens_unit.get(use_monitor=False).readback == 1
    # Change the gain so that it overflows and we have to change units
    max_sensitivity = len(device.sensitivity.values) - 1
    max_unit = len(device.sensitivity.units) - 1
    device.sensitivity.sens_value.set(max_sensitivity).wait()
    assert device.sensitivity.sens_value.get(use_monitor=False).readback == 8
    device.decrease_gain().wait()
    assert device.sensitivity.sens_value.get(use_monitor=False).readback == 0
    assert device.sensitivity.sens_unit.get(use_monitor=False).readback == 2
    # Check that the gain can't overflow the acceptable values
    device.sensitivity.sens_value.set(0).wait()
    device.sensitivity.sens_unit.set(0).wait()
    with pytest.raises(exceptions.GainOverflow):
        device.increase_gain()
    device.sensitivity.sens_value.set(0).wait()
    device.sensitivity.sens_unit.set(max_unit).wait()
    with pytest.raises(exceptions.GainOverflow):
        device.decrease_gain()


def test_load_ion_chambers(sim_registry):
    new_ics = ion_chamber.load_ion_chambers()
    print(new_ics)
    # Test the channel info is extracted properly
    ic = sim_registry.find(label="ion_chambers")
    assert ic.ch_num == 2
    assert ic.sensitivity.prefix.split(":")[-1] == "SR01"


def test_default_pv_prefix():
    """Check that it uses the *prefix* argument if no *scaler_prefix* is
    given.

    """
    prefix = "myioc:myscaler"
    # Instantiate the device with *scaler_prefix* argument
    device = ion_chamber.IonChamber(
        name="device", prefix="gibberish", ch_num=1, scaler_prefix=prefix
    )
    device.scaler_prefix = prefix
    assert device.scaler_prefix == prefix
    # Instantiate the device with *scaler_prefix* argument
    device = ion_chamber.IonChamber(name="device", ch_num=1, prefix=prefix)
    assert device.scaler_prefix == prefix


def test_offset_pv(sim_registry):
    """Check that the device handles the weird offset numbering scheme.

    Net count PVs in the scaler go as

    - 25idcVME:3820:scaler1_netA.B
    - 25idcVME:3820:scaler1_netA.C
    - etc.

    but the offset PVs go
    - 25idcVME:3820:scaler1_offset0.B
    - ...
    - 25idcVME:3820:scaler1_offset0.D
    - 25idcVME:3820:scaler1_offset1.A
    - ...

    """
    channel_suffixes = [
        (2, "offset0.B"),
        (3, "offset0.C"),
        (4, "offset0.D"),
        (5, "offset1.A"),
        (6, "offset1.B"),
        (7, "offset1.C"),
        (8, "offset1.D"),
        (9, "offset2.A"),
        (10, "offset2.B"),
        (11, "offset2.C"),
        (12, "offset2.D"),
    ]
    for ch_num, suffix in channel_suffixes:
        ic = ion_chamber.IonChamber(
            prefix="scaler_ioc:scaler1", ch_num=ch_num, name=f"ion_chamber_{ch_num}"
        )
        assert ic.offset.pvname == f"scaler_ioc:scaler1_{suffix}", f"channel {ch_num}"
