# By Gareth Nisbet

import numpy as np


# ------------------------------------------------------------------------------#
#                     Calculate angle between vectors
# ------------------------------------------------------------------------------#
def vanglev(v1, v2):
    angle = np.arccos(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
    return angle


# ------------------------------------------------------------------------------#
#                Calculate angle between vector and a plane
# ------------------------------------------------------------------------------#


def vp_angle(v1, v2, v3):
    plane_normal = np.cross(v2, v3)
    return np.arccos(
        np.dot(v1, plane_normal) / (np.linalg.norm(v1) * np.linalg.norm(plane_normal))
    )


# ------------------------------------------------------------------------------#
#                  Rotate vector about another vector
# ------------------------------------------------------------------------------#


def rotxyz(v, u, angle):
    u = np.matrix(u) / np.linalg.norm(np.matrix(u))
    e11 = u[0, 0] ** 2 + (1 - u[0, 0] ** 2) * np.cos(angle * np.pi / 180.0)
    e12 = u[0, 0] * u[0, 1] * (1 - np.cos(angle * np.pi / 180.0)) - u[0, 2] * np.sin(
        angle * np.pi / 180.0
    )
    e13 = u[0, 0] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) + u[0, 1] * np.sin(
        angle * np.pi / 180.0
    )
    e21 = u[0, 0] * u[0, 1] * (1 - np.cos(angle * np.pi / 180.0)) + u[0, 2] * np.sin(
        angle * np.pi / 180.0
    )
    e22 = u[0, 1] ** 2 + (1 - u[0, 1] ** 2) * np.cos(angle * np.pi / 180.0)
    e23 = u[0, 1] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) - u[0, 0] * np.sin(
        angle * np.pi / 180.0
    )
    e31 = u[0, 0] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) - u[0, 1] * np.sin(
        angle * np.pi / 180.0
    )
    e32 = u[0, 1] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) + u[0, 0] * np.sin(
        angle * np.pi / 180.0
    )
    e33 = u[0, 2] ** 2 + (1 - u[0, 2] ** 2) * np.cos(angle * np.pi / 180.0)
    rotmat = np.matrix([[e11, e12, e13], [e21, e22, e23], [e31, e32, e33]])
    return (rotmat * v.T).T


# ------------------------------------------------------------------------------#
#                      Generate rotation matrix
# ------------------------------------------------------------------------------#


def rotmat(u, angle):
    # clockwise rotation
    u = np.matrix(u) / np.linalg.norm(np.matrix(u))
    e11 = u[0, 0] ** 2 + (1 - u[0, 0] ** 2) * np.cos(angle * np.pi / 180.0)
    e12 = u[0, 0] * u[0, 1] * (1 - np.cos(angle * np.pi / 180.0)) - u[0, 2] * np.sin(
        angle * np.pi / 180.0
    )
    e13 = u[0, 0] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) + u[0, 1] * np.sin(
        angle * np.pi / 180.0
    )
    e21 = u[0, 0] * u[0, 1] * (1 - np.cos(angle * np.pi / 180.0)) + u[0, 2] * np.sin(
        angle * np.pi / 180.0
    )
    e22 = u[0, 1] ** 2 + (1 - u[0, 1] ** 2) * np.cos(angle * np.pi / 180.0)
    e23 = u[0, 1] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) - u[0, 0] * np.sin(
        angle * np.pi / 180.0
    )
    e31 = u[0, 0] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) - u[0, 1] * np.sin(
        angle * np.pi / 180.0
    )
    e32 = u[0, 1] * u[0, 2] * (1 - np.cos(angle * np.pi / 180.0)) + u[0, 0] * np.sin(
        angle * np.pi / 180.0
    )
    e33 = u[0, 2] ** 2 + (1 - u[0, 2] ** 2) * np.cos(angle * np.pi / 180.0)
    rotmat = np.matrix([[e11, e12, e13], [e21, e22, e23], [e31, e32, e33]])
    return rotmat


def mat2euler(mat):
    alpha = -np.arctan2(mat[2, 1], mat[2, 2])
    gamma = -np.arctan2(mat[1, 0], mat[0, 0])
    beta = -np.arctan2(-mat[2, 0], np.sqrt(mat[2, 1] ** 2 + mat[2, 2] ** 2))  #  z-y-x
    return np.array([[alpha, beta, gamma]])


def eulerMatrix(alpha, beta, gamma):
    M_alpha = np.matrix(
        [
            [np.cos(alpha * np.pi / 180), np.sin(alpha * np.pi / 180), 0],
            [-np.sin(alpha * np.pi / 180), np.cos(alpha * np.pi / 180), 0],
            [0, 0, 1],
        ]
    )
    M_beta = np.matrix(
        [
            [np.cos(beta * np.pi / 180), 0, -np.sin(beta * np.pi / 180)],
            [0, 1, 0],
            [np.sin(beta * np.pi / 180), 0, np.cos(beta * np.pi / 180)],
        ]
    )
    M_gamma = np.matrix(
        [
            [np.cos(gamma * np.pi / 180), np.sin(gamma * np.pi / 180), 0],
            [-np.sin(gamma * np.pi / 180), np.cos(gamma * np.pi / 180), 0],
            [0, 0, 1],
        ]
    )
    return np.array(M_alpha * M_beta * M_gamma)


# ------------------------------------------------------------------------------#
#              Convert rotation matrix to ZYX Euler angles
# ------------------------------------------------------------------------------#


def rotationMatrixToEulerZYX(rmatrix):
    sy = np.sqrt(rmatrix[2, 1] ** 2 + rmatrix[2, 2] ** 2)
    singular = sy < 1e-6
    if not singular:
        alpha = -np.arctan2(
            rmatrix[2, 1], rmatrix[2, 2]
        )  #  z-y-x rotation matrix is constructed from vectors
        beta = -np.arctan2(
            -rmatrix[2, 0], np.sqrt(rmatrix[2, 1] ** 2 + rmatrix[2, 2] ** 2)
        )  #  z-y-x
        gamma = -np.arctan2(rmatrix[1, 0], rmatrix[0, 0])  #  in rows not columns
    else:
        alpha = np.pi - np.arctan2(
            rmatrix[0, 1], rmatrix[0, 2]
        )  #  z-y-x rotation matrix is constructed from vectors
        beta = -np.arctan2(
            -rmatrix[2, 0], np.sqrt(rmatrix[2, 1] ** 2 + rmatrix[2, 2] ** 2)
        )  #  z-y-x
        gamma = -np.arctan2(rmatrix[1, 0], rmatrix[0, 0])  #  in rows not columns
    return alpha, beta, gamma


# ------------------------------------------------------------------------------#
#              Convert rotation matrix to XYX Euler angles
# ------------------------------------------------------------------------------#


def rotationMatrixToEulerXYX(rmatrix):
    alpha = np.arctan2(
        rmatrix[1, 0], -rmatrix[2, 0]
    )  #  z-y-x rotation matrix is constructed from vectors
    beta = -np.arctan2(np.sqrt(1 - rmatrix[0, 0] ** 2), rmatrix[0, 0])  #  z-y-x
    gamma = -np.arctan2(rmatrix[0, 1], rmatrix[0, 2])  #  in rows not columns
    return alpha, beta, gamma


# ------------------------------------------------------------------------------#
#              Convert rotation matrix to ZYZ Euler angles
# ------------------------------------------------------------------------------#


def rotationMatrixToEulerZYZ_extrinsic(rmatrix):
    alpha = np.pi / 2 - np.arctan2(
        rmatrix[2, 0], rmatrix[2, 1]
    )  #  z-y-x rotation matrix is constructed from vectors
    beta = np.pi / 2 - np.arccos(rmatrix[2, 2])
    gamma = -(
        np.arctan2(rmatrix[0, 2], rmatrix[1, 2]) + np.pi / 2
    )  #  in rows not columns
    return alpha, beta, gamma


# ------------------------------------------------------------------------------#
#              Sets angles in terms of diffractometer angles
# ------------------------------------------------------------------------------#


def set_mu_eta_chi_phi(mu, eta, chi, phi):
    v = np.identity(3)
    rmatrix = (
        v
        * rotmat(v[2, :], phi)
        * rotmat(v[1, :], -(90 - chi))
        * rotmat(v[0, :], eta)
        * rotmat(v[2, :], mu)
    )
    rmatrix[np.where(np.abs(rmatrix) < 0.00001)] = 0
    alpha, beta, gamma = rotationMatrixToEulerZYX(rmatrix)
    return alpha, beta, gamma


# ------------------------------------------------------------------------------#
#          Finds consecutive numbers and group them into lists
# ------------------------------------------------------------------------------#


def consecutive(data, stepsize=1):
    return np.split(data, np.where(np.diff(data) != stepsize)[0] + 1)


# ------------------------------------------------------------------------------#
#      Calculates the minimum angle difference eg. minanglediff-170, 170)
#      would be 20
# ------------------------------------------------------------------------------#


def minanglediff(a, b):
    return (
        np.arccos(
            np.cos(a * np.pi / 180) * np.cos(b * np.pi / 180)
            + np.sin(a * np.pi / 180) * np.sin(b * np.pi / 180)
        )
        * 180
        / np.pi
    )


# ------------------------------------------------------------------------------#
#         This is the main class for the robot arm and calculates
#         both the forawrd and inverse kinematics with and includes
#         decision strategies for efficient path planning
# ------------------------------------------------------------------------------#


class kinematics:
    """
    Calculates forward and inverse kinematics for robot arm.\n
    with off centre base rotation.\n
    Instantiate with:\n
    kin = kinematics(axis_vects,L_vects,motor_limits,motor_offsets,tool_offset)
    """

    def __init__(self, *args):
        self.axis_vects = args[0]
        self.L_vects = args[1]
        self.motor_limits = args[2]
        self.motor_offsets = np.array(args[3])
        self.centre_offset = np.array(args[4])
        self.tool_offset = args[5]
        self.strategy = args[6]
        if len(args) > 6:
            self.weighting = args[7]
        self.new_offset = [0, 0, 0]
        self.motor_pos = np.array([0, 0, 0, 0, 0, 0])

    def setStrategy(self, strategy):
        self.strategy = strategy

    def setWeighting(self, weighting):
        self.weighting = weighting

    def setBase_cut_off(self, base_cut_off):
        self.base_cut_off = base_cut_off

    def setLimits(self, motor_limits):
        self.motor_limits = motor_limits

    def setToolOffset(self, tool_offset):
        self.tool_offset = tool_offset

    def setCentreOffset(self, centre_offset):
        self.centre_offset = centre_offset

    def setMotorOffset(self, motor_offsets):
        self.motor_offsets = motor_offsets

    def storeCurrentPosition(self, set_pos):
        self.motor_pos = set_pos

    def setEulerTarget(self, xyz, r_alpha, r_beta, r_gamma):
        MI = np.identity(3)
        vx = MI[0, :]
        vy = MI[1, :]
        vz = MI[2, :]
        em = (
            rotmat(vx, r_alpha) * rotmat(vy, r_beta) * rotmat(vz, r_gamma)
        )  # ZYX convention
        targetmatrix = np.array(
            [
                np.array((em * np.matrix([vx]).T).T)[0],
                np.array((em * np.matrix([vy]).T).T)[0],
                np.array((em * np.matrix([vz]).T).T)[0],
            ]
        )  # To make consisten with Euler in Blender
        tool = np.array(np.matrix([self.tool_offset]) * targetmatrix)[0]
        xyz = np.array(xyz + tool)
        tv1 = list(np.array(np.matrix([vx]) * targetmatrix)[0])
        tv2 = list(np.array(np.matrix([vy]) * targetmatrix)[0])
        tv3 = list(np.array(np.matrix([vz]) * targetmatrix)[0])
        return self.i_kinematics(np.array([xyz, tv1, tv2, tv3]))

    def f_kinematics(self, *inputs):
        inputs = inputs[0]

        angles = inputs + self.motor_offsets

        # L 0
        _v0 = np.array([self.axis_vects[0, :]])
        self.v0 = rotxyz(np.array([self.L_vects[0, :]]), _v0, angles[0])

        # L 1
        _v1 = rotxyz(np.array([self.L_vects[1, :]]), self.axis_vects[1, :], angles[1])
        self.v1 = self.v0 + rotxyz(_v1, self.axis_vects[0, :], angles[0])

        # L2
        _v2 = rotxyz(np.array([self.L_vects[2, :]]), self.axis_vects[2, :], angles[2])
        _v2 = rotxyz(_v2, self.axis_vects[1, :], angles[1])
        self.v2 = self.v1 + rotxyz(_v2, self.axis_vects[0, :], angles[0])

        # L3
        _v3 = rotxyz(np.array([self.L_vects[3, :]]), self.axis_vects[3, :], angles[3])
        _v3 = rotxyz(_v3, self.axis_vects[2, :], angles[2])
        _v3 = rotxyz(_v3, self.axis_vects[1, :], angles[1])
        self.v3 = self.v2 + rotxyz(_v3, self.axis_vects[0, :], angles[0])

        # L4
        _v4 = rotxyz(np.array([self.L_vects[4, :]]), self.axis_vects[4, :], angles[4])
        _v4 = rotxyz(_v4, self.axis_vects[3, :], angles[3])
        _v4 = rotxyz(_v4, self.axis_vects[2, :], angles[2])
        _v4 = rotxyz(_v4, self.axis_vects[1, :], angles[1])
        self.v4 = self.v3 + rotxyz(_v4, self.axis_vects[0, :], angles[0])

        # L5
        _v5 = rotxyz(np.array([self.L_vects[5, :]]), self.axis_vects[5, :], angles[5])
        _v5 = rotxyz(_v5, self.axis_vects[4, :], angles[4])
        _v5 = rotxyz(_v5, self.axis_vects[3, :], angles[3])
        _v5 = rotxyz(_v5, self.axis_vects[2, :], angles[2])
        _v5 = rotxyz(_v5, self.axis_vects[1, :], angles[1])
        self.v5 = rotxyz(_v5, self.axis_vects[0, :], angles[0])

        _t_off = rotxyz(np.array([self.tool_offset]), self.axis_vects[5, :], angles[5])
        _t_off = rotxyz(_t_off, self.axis_vects[4, :], angles[4])
        _t_off = rotxyz(_t_off, self.axis_vects[3, :], angles[3])
        _t_off = rotxyz(_t_off, self.axis_vects[2, :], angles[2])
        _t_off = rotxyz(_t_off, self.axis_vects[1, :], angles[1])
        self._t_off = rotxyz(_t_off, self.axis_vects[0, :], angles[0])

        new_centre = rotxyz(
            np.array([self.centre_offset]), self.axis_vects[0, :], angles[0]
        )

        _v6 = rotxyz(np.array([self.L_vects[6, :]]), self.axis_vects[5, :], angles[5])
        _v6 = rotxyz(_v6, self.axis_vects[4, :], angles[4])
        _v6 = rotxyz(_v6, self.axis_vects[3, :], angles[3])
        _v6 = rotxyz(_v6, self.axis_vects[2, :], angles[2])
        _v6 = rotxyz(_v6, self.axis_vects[1, :], angles[1])
        self.v6 = rotxyz(_v6, self.axis_vects[0, :], angles[0])

        _v7 = rotxyz(np.array([self.L_vects[7, :]]), self.axis_vects[5, :], angles[5])
        _v7 = rotxyz(_v7, self.axis_vects[4, :], angles[4])
        _v7 = rotxyz(_v7, self.axis_vects[3, :], angles[3])
        _v7 = rotxyz(_v7, self.axis_vects[2, :], angles[2])
        _v7 = rotxyz(_v7, self.axis_vects[1, :], angles[1])
        self.v7 = rotxyz(_v7, self.axis_vects[0, :], angles[0])

        # ----------------  Conversion back to Euler angles  -------------------#
        rmatrix = np.concatenate((self.v5, self.v6, self.v7), 0)
        rmatrix[np.where(np.abs(rmatrix) < 0.00001)] = 0
        alpha, beta, gamma = rotationMatrixToEulerZYX(rmatrix)
        self.al_be_gam = np.array([[alpha, beta, gamma]])
        self.position = self.v4 - self._t_off + new_centre

        return np.concatenate(
            (
                self.v0,
                self.v1,
                self.v2,
                self.v3,
                self.v4,
                self.v5,
                self.v6,
                self.v7,
                self.position,
                self.al_be_gam,
            ),
            0,
        )

    def i_kinematics(self, target):
        solutions = np.array([[]] * 6).T
        valid_solutions = np.array([[]] * 6).T
        self.target = target
        L_vects = np.copy(self.L_vects)
        L_vects[np.r_[:3], 0] = 0
        L1 = np.linalg.norm(L_vects[1, :])
        L2 = np.linalg.norm(L_vects[2, :] + L_vects[3, :])
        v0 = self.target[0, :]
        v1 = self.target[1, :]
        # v2 = self.target[2, :]
        v3 = self.target[3, :]

        vlength = np.linalg.norm(L_vects[4, :])
        vc1 = (v0 - (v3 / np.linalg.norm(v3) * vlength)) - L_vects[
            0, :
        ]  # Calculate the origin of L4

        # -----------------------------------------------------------------------
        #       determine angle addition or subtraction and vector length
        # -----------------------------------------------------------------------

        A1 = np.pi / 2 + vp_angle(
            np.array(vc1), np.array([1, 0, 0]), np.array([0, 1, 0])
        )
        A2 = np.pi / 2 - vp_angle(
            np.array(vc1), np.array([1, 0, 0]), np.array([0, 1, 0])
        )
        A1n = 3 / 2.0 * np.pi - vp_angle(
            np.array(vc1), np.array([1, 0, 0]), np.array([0, 1, 0])
        )
        A2n = (
            vp_angle(np.array(vc1), np.array([1, 0, 0]), np.array([0, 1, 0]))
            - np.pi / 2
        )
        # -----------------------------------------------------------------------

        b = np.linalg.norm(vc1)
        c = np.linalg.norm([self.L_vects[0, :][0], self.L_vects[0, :][1], 0])
        a1 = (b**2 + c**2 - (2 * b * c * np.cos(A1))) ** 0.5  # law of cosines
        a2 = (b**2 + c**2 - (2 * b * c * np.cos(A2))) ** 0.5  # law of cosines
        a1n = (b**2 + c**2 - (2 * b * c * np.cos(A1n))) ** 0.5  # law of cosines
        a2n = (b**2 + c**2 - (2 * b * c * np.cos(A2n))) ** 0.5  # law of cosines
        theta_c_angle_offset1 = np.arccos((c**2 - a1**2 - b**2) / (-2 * a1 * b))
        theta_c_angle_offset2 = np.arccos((c**2 - a2**2 - b**2) / (-2 * a2 * b))
        theta_c_angle_offset1n = np.arccos((c**2 - a1n**2 - b**2) / (-2 * a1n * b))
        theta_c_angle_offset2n = np.arccos((c**2 - a2n**2 - b**2) / (-2 * a2n * b))

        theta0check = np.arctan2(vc1[1], vc1[0])
        print("theta0check = " + str(theta0check * 180 / np.pi))
        num_checks = 8
        keep_index = np.zeros((8, 2))
        for ii in list(range(num_checks)):
            if ii == 0 or ii == 4:
                if vc1[-1] > 0:
                    vc1n = a2
                    theta_c_angle_offset = theta_c_angle_offset2
                else:
                    vc1n = a2n
                    theta_c_angle_offset = -theta_c_angle_offset2n

                theta0 = theta0check
                theta1 = (
                    np.arccos((L1**2 + vc1n**2 - L2**2) / (2 * L1 * vc1n))
                    + theta_c_angle_offset
                )  # law of cosines
                theta2 = np.pi - np.arccos(
                    (L1**2 + L2**2 - vc1n**2) / (2 * L1 * L2)
                )  # law of cosines
                theta2 = theta2 - (
                    vp_angle((L_vects[3, :] + L_vects[2, :]), [1, 0, 0], [0, 1, 0])
                )
                theta1 = -theta1 + (vp_angle(vc1, [1, 0, 0], [0, 1, 0]))

            elif ii == 1 or ii == 5:
                if vc1[-1] > 0:
                    vc1n = a1
                    theta_c_angle_offset = theta_c_angle_offset1
                else:
                    vc1n = a1n
                    theta_c_angle_offset = -theta_c_angle_offset1n

                theta0 = theta0check + np.pi
                theta1 = (
                    np.arccos((L1**2 + vc1n**2 - L2**2) / (2 * L1 * vc1n))
                    + theta_c_angle_offset
                )  # law of cosines
                theta2 = np.pi - np.arccos(
                    (L1**2 + L2**2 - vc1n**2) / (2 * L1 * L2)
                )  # law of cosines
                theta2 = theta2 - (
                    vp_angle((L_vects[3, :] + L_vects[2, :]), [1, 0, 0], [0, 1, 0])
                )
                theta1 = -theta1 - (vp_angle(vc1, [1, 0, 0], [0, 1, 0]))

            elif ii == 2 or ii == 6:
                if vc1[-1] > 0:
                    vc1n = a2
                    theta_c_angle_offset = theta_c_angle_offset2
                else:
                    vc1n = a2n
                    theta_c_angle_offset = -theta_c_angle_offset2n

                theta0 = theta0check
                theta1 = (
                    -np.arccos((L1**2 + vc1n**2 - L2**2) / (2 * L1 * vc1n))
                    + theta_c_angle_offset
                )  # law of cosines
                theta2 = -(
                    np.pi - np.arccos((L1**2 + L2**2 - vc1n**2) / (2 * L1 * L2))
                )  # law of cosines
                theta2 = theta2 - (
                    vp_angle((L_vects[3, :] + L_vects[2, :]), [1, 0, 0], [0, 1, 0])
                )
                theta1 = -theta1 + (vp_angle(vc1, [1, 0, 0], [0, 1, 0]))

            elif ii == 3 or ii == 7:
                if vc1[-1] > 0:
                    vc1n = a1
                    theta_c_angle_offset = theta_c_angle_offset1
                else:
                    vc1n = a1n
                    theta_c_angle_offset = -theta_c_angle_offset1n

                theta0 = theta0check + np.pi
                theta1 = (
                    -np.arccos((L1**2 + vc1n**2 - L2**2) / (2 * L1 * vc1n))
                    + theta_c_angle_offset
                )  # law of cosines
                theta2 = -(
                    np.pi - np.arccos((L1**2 + L2**2 - vc1n**2) / (2 * L1 * L2))
                )  # law of cosines
                theta2 = theta2 - (
                    vp_angle((L_vects[3, :] + L_vects[2, :]), [1, 0, 0], [0, 1, 0])
                )
                theta1 = -theta1 - (vp_angle(vc1, [1, 0, 0], [0, 1, 0]))

            print("theta0 ii " + str(theta0 * 180 / np.pi) + " " + str(ii))
            # -------------------------------------------------------------------------------------------#
            #           theta0 theta1 and theta2 determine position of Lvect origin
            # -------------------------------------------------------------------------------------------#
            vec3 = rotxyz(
                np.array([L_vects[3, :]]),
                np.array([self.axis_vects[2, :]]),
                theta2 * 180 / np.pi,
            )
            vec3 = rotxyz(vec3, self.axis_vects[1, :], theta1 * 180 / np.pi)
            vec3 = rotxyz(vec3, self.axis_vects[0, :], theta0 * 180 / np.pi)

            av3 = rotxyz(
                np.array([self.axis_vects[4, :]]),
                np.array([self.axis_vects[2, :]]),
                theta2 * 180 / np.pi,
            )
            av3 = rotxyz(av3, self.axis_vects[1, :], theta1 * 180 / np.pi)
            av3 = rotxyz(av3, self.axis_vects[0, :], theta0 * 180 / np.pi)

            if (
                np.abs(np.dot(np.array(av3)[0], v3)) > 0.0001
            ):  # To check that av3 is not already orthoganol to v3
                theta3i = vp_angle(np.array(av3)[0], np.array(v3), np.array(vec3)[0])
                if ii < 4:
                    theta3 = vp_angle(np.array(av3)[0], np.array(v3), np.array(vec3)[0])
                elif theta3i > np.pi / 2:
                    theta3 = -(
                        vp_angle(np.array(av3)[0], np.array(vec3)[0], np.array(v3))
                    )
            else:
                theta3 = 0

            theta3 = -np.sign(np.dot(np.array(av3)[0], np.array(v3))) * theta3
            vec4 = rotxyz(
                np.array([L_vects[4, :]]),
                np.array([self.axis_vects[3, :]]),
                theta3 * 180 / np.pi,
            )
            vec4 = rotxyz(vec4, self.axis_vects[2, :], theta2 * 180 / np.pi)
            vec4 = rotxyz(vec4, self.axis_vects[1, :], theta1 * 180 / np.pi)
            vec4 = rotxyz(vec4, self.axis_vects[0, :], theta0 * 180 / np.pi)
            theta4 = vanglev(v3, np.array(vec4)[0])

            vec5 = rotxyz(
                np.array([L_vects[5, :]]),
                np.array([self.axis_vects[4, :]]),
                theta4 * 180 / np.pi,
            )
            vec5 = rotxyz(vec5, self.axis_vects[3, :], theta3 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[2, :], theta2 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[1, :], theta1 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[0, :], theta0 * 180 / np.pi)

            theta4_check = np.abs(vanglev(v3, np.array(vec5)[0]) - np.pi / 2)
            if theta4_check > 0.01:
                theta4 = -vanglev(v3, np.array(vec4)[0])

            vec5 = rotxyz(
                np.array([L_vects[5, :]]),
                np.array([self.axis_vects[4, :]]),
                theta4 * 180 / np.pi,
            )
            vec5 = rotxyz(vec5, self.axis_vects[3, :], theta3 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[2, :], theta2 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[1, :], theta1 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[0, :], theta0 * 180 / np.pi)
            theta5 = -vanglev(v1, np.array(vec5)[0])

            vec5 = rotxyz(
                np.array([L_vects[5, :]]),
                np.array([self.axis_vects[5, :]]),
                theta5 * 180 / np.pi,
            )
            vec5 = rotxyz(vec5, self.axis_vects[4, :], theta4 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[3, :], theta3 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[2, :], theta2 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[1, :], theta1 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[0, :], theta0 * 180 / np.pi)

            if np.abs(vanglev(v1, np.array(vec5)[0])) > 0.01:
                theta5 = -theta5

            vec5 = rotxyz(
                np.array([L_vects[5, :]]),
                np.array([self.axis_vects[5, :]]),
                theta5 * 180 / np.pi,
            )
            vec5 = rotxyz(vec5, self.axis_vects[4, :], theta4 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[3, :], theta3 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[2, :], theta2 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[1, :], theta1 * 180 / np.pi)
            vec5 = rotxyz(vec5, self.axis_vects[0, :], theta0 * 180 / np.pi)
            if np.abs(vanglev(v1, np.array(vec5)[0])) > 0.01:
                theta5 = vanglev(v1, np.array(vec5)[0]) + np.pi

            if np.isnan(theta5):
                theta5 = 0
            # set angular range between -180 and 180
            theta0 = np.mod(theta0 + np.pi, 2 * np.pi) - np.pi
            theta1 = np.mod(theta1 + np.pi, 2 * np.pi) - np.pi
            theta2 = np.mod(theta2 + np.pi, 2 * np.pi) - np.pi
            theta3 = np.mod(theta3 + np.pi, 2 * np.pi) - np.pi
            theta4 = np.mod(theta4 + np.pi, 2 * np.pi) - np.pi
            theta5 = np.mod(theta5 + np.pi, 2 * np.pi) - np.pi
            output = np.array(
                [
                    theta0 * 180 / np.pi,
                    theta1 * 180 / np.pi,
                    theta2 * 180 / np.pi,
                    theta3 * 180 / np.pi,
                    theta4 * 180 / np.pi,
                    theta5 * 180 / np.pi,
                ]
            )

            solutions = np.vstack([solutions, output])

        solutions = solutions - self.motor_offsets

        print("------------------------------------------------------")
        print("solutions = \n" + str(solutions))
        print("------------------------------------------------------")

        #        print('motor_limits = \n'+str(self.motor_limits))
        # ----------------------------------------------------------------------#
        #      Check all motors are within their respective limits
        # ----------------------------------------------------------------------#

        for iii in list(range(int(num_checks))):
            if (
                np.where(self.motor_limits.T[0, :] <= solutions[iii, :])[0].shape[0]
                == 6
            ):
                keep_index[iii, 0] = 1
            if (
                np.where(self.motor_limits.T[1, :] >= solutions[iii, :])[0].shape[0]
                == 6
            ):
                keep_index[iii, 1] = 1

        for iii in list(range(num_checks)):
            if keep_index[iii, 0] * keep_index[iii, 1] == 1:
                valid_solutions = np.vstack([valid_solutions, solutions[iii, :]])

        if valid_solutions.shape[0] < 1:
            best_solution = np.array([np.nan, np.nan, np.nan, np.nan, np.nan, np.nan])
        #            print('No solution within limits')

        else:
            # ------------------------------------------------------------------#
            #                      Solution strategy
            # -------------------------------------------------------------------

            if self.strategy == "minimum_movement":
                comparator = np.apply_along_axis(
                    np.sum, 1, np.abs(valid_solutions - self.motor_pos)
                )
                best_solution = valid_solutions[np.argmin(comparator)]

            elif self.strategy == "minimum_movement_weighted":
                comparator = np.apply_along_axis(
                    np.sum,
                    1,
                    np.abs(valid_solutions - self.motor_pos) * self.weighting,
                )
                best_solution = valid_solutions[np.argmin(comparator)]

            elif self.strategy == "comfortable_limits":
                limit_centres = np.mean(self.motor_limits, 1)
                comparator = np.abs(
                    np.apply_along_axis(
                        np.sum, 1, np.abs(limit_centres - valid_solutions)
                    )
                )
                best_solution = valid_solutions[np.argmin(comparator)]

        # final check to make sure the solutions is consistent with the target value
        forward_check = self.f_kinematics(best_solution)
        check_target = forward_check - self.target[0, :]
        comparator = np.abs(np.apply_along_axis(np.sum, 1, (check_target)))

        if np.any(comparator < 2.0e-3):
            pass
        else:
            best_solution = np.array([np.nan, np.nan, np.nan, np.nan, np.nan, np.nan])
        return best_solution


# ------------------------------------------------------------------------------#
#                     Robot Description Meca 500
# ------------------------------------------------------------------------------#

# L5 from pivot to end effector is 70 mm
# L4 from pivot to pivot is 60 mm
# L3 [38,60] (38**2+60**2)**0.5 = 71.0211236 mm
# L2 135 mm
# L1 including base is 135 mm

# units below are in meters
v0 = np.array([0, 0.0, 0.135])
v1 = np.array([0, 0.0, 0.135 * 2])
v2 = np.array([0, 0, 0.34102])
v3 = np.array([0.03210312, 0, 0.3917102])
v4 = np.array([0.03210312, 0, 0.3917102 + 0.07])
v5 = np.array([1, 0, 0])
v6 = np.array([0, 1, 0])
v7 = np.array([0, 0, 1])

L_vects = np.array([v0, (v1 - v0), (v2 - v1), (v3 - v2), (v4 - v3), v5, v6, v7])
ax3 = v3 - v2
axis_vects = np.array(
    [[0, 0, 1], [0, 1, 0], [0, 1, 0], ax3, [0, 1, 0], [0, 0, 1]]
)  # make sure v4 is consistent with ax4 rotation offset
motor_offsets = (0, 0, 57.6525565, 0, 32.347444, 0)
centre_offset = [0, 0, 0]
motor_limits = np.array(
    [[-175, 175], [-70, 90], [-135, 70], [-170, 170], [-115, 115], [-3600, 3600]]
)
tool_offset = [0, 0, -0.016]
L3_angle_offset = 32
strategy = "minimum_movement"
# strategy = 'minimum_movement_weighted'
# strategy ='comfortable_limits'
weighting = [6, 5, 4, 3, 2, 1]
initial_rotations = np.array(
    [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 32.347444 * np.pi / 180, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
)

MECA_500 = [
    axis_vects,
    L_vects,
    motor_limits,
    motor_offsets,
    centre_offset,
    tool_offset,
    strategy,
    weighting,
]
