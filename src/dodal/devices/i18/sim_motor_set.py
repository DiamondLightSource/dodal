import os

from ophyd import EpicsMotor
from ophyd.sim import Syn2DGauss, SynAxis, SynGauss


def create_epics_motor(motor_name="epics_motor", motor_base_pv="ws416-MO-SIM-01:M1"):
    print(f"Creating Epics motor for {motor_base_pv}")
    epics_motor = EpicsMotor(motor_base_pv, name=motor_name)
    # epics_motor.wait_for_connection(timeout=5) # blueapi fails to connect any PVs!
    return epics_motor


def create_dummy_motor(motor_name="dummy_motor"):
    print(f"Creating dummy motor {motor_name}")
    return SynAxis(name=motor_name, labels={"motors"})


def create_syn_gaussian(det_name, motor, motor_field, noise="none", noise_multiplier=1):
    print(f"Creating synthetic Gaussian detector {det_name}")
    syn_gauss = SynGauss(
        det_name, motor, motor_field, center=0, Imax=5, sigma=0.5, labels={"detectors"}
    )
    syn_gauss.noise.put(noise)
    syn_gauss.noise_multiplier.put(noise_multiplier)
    return syn_gauss


def create_syn_2d_gaussian(
    det_name,
    motor1,
    motor1_field,
    motor2,
    motor2_field,
    noise="none",
    noise_multiplier=1,
):
    print(f"Creating synthetic 2d Gaussian detector {det_name}")

    syn_gauss = Syn2DGauss(
        det_name,
        motor1,
        motor1_field,
        motor2,
        motor2_field,
        center=0,
        Imax=1,
        labels={"detectors"},
    )
    syn_gauss.noise.put(noise)
    syn_gauss.noise_multiplier.put(noise_multiplier)
    return syn_gauss


dummy_mot1 = create_dummy_motor("dummy_motor1")
dummy_mot2 = create_dummy_motor("dummy_motor2")
dummy_mot1.delay = 0.05


def dummy_motor1(name: str = "dummy_motor1") -> SynAxis:
    return dummy_mot1


def dummy_motor2(name: str = "dummy_motor2") -> SynAxis:
    return dummy_mot2


def sim_gauss_det(name: str = "sim_gauss_det") -> SynGauss:
    return create_syn_gaussian(name, dummy_mot1, "dummy_motor1")


def sim_2d_gauss_det(name: str = "sim_2d_gauss_det") -> Syn2DGauss:
    return create_syn_2d_gaussian(
        name, dummy_mot1, "dummy_motor1", dummy_mot2, "dummy_motor2"
    )


# Make sure EPICS_CA_SERVER_PORT is set to correct value (6064 for DLS sim area detector and motors, 5064 on beamlines)
os.environ["EPICS_CA_SERVER_PORT"] = "6064"


# def sim_x(name : str, pv_name : str) -> EpicsMotor:
def sim_x(name: str = "sim_x", pv_name: str = "ws416-MO-SIM-01:M1") -> EpicsMotor:
    return create_epics_motor(name, pv_name)


def sim_y(name: str = "sim_y", pv_name: str = "ws416-MO-SIM-01:M2") -> EpicsMotor:
    return create_epics_motor(name, pv_name)
