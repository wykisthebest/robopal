import numpy as np
import pinocchio as pin
import robopal.commons.transform as trans


class PinSolver:
    """ Pinocchio solver for kinematics and dynamics """

    def __init__(self, urdf_path: str):
        # Load the urdf model
        urdf_path = urdf_path
        self.model = pin.buildModelFromUrdf(urdf_path)

        # Create data required by the algorithms
        self.data = self.model.createData()

        self.JOINT_NUM = self.model.nq
        print(f"pinocchio model {self.model.name} init!")

    def fk(self, q: np.ndarray, rot_format: str = 'matrix'):
        """ Perform the forward kinematics over the kinematic tree

        :param q: joint position
        :param rot_format: 'matrix' or 'quat'
        :return: end's translation, rotation
        """
        pin.forwardKinematics(self.model, self.data, q)
        if rot_format == 'matrix':
            return self.data.oMi[-1].translation, self.data.oMi[-1].rotation
        elif rot_format == 'quat':
            return self.data.oMi[-1].translation, trans.mat_2_quat(self.data.oMi[-1].rotation)

    def ik(self, pos: np.ndarray, rot: np.ndarray, q_init: np.ndarray) -> np.ndarray:
        """ Position the end effector of a manipulator robot to a given pose (position and orientation)
            The method employs a simple Jacobian-based iterative algorithm, which is called closed-loop inverse kinematics (CLIK).

        :param pos: desired position
        :param rot: desired rotation
        :param q_init: initial joint position
        :return: joint position
        """
        oM_des = pin.SE3(rot, pos)
        q = q_init

        eps = 1e-4
        IT_MAX = 1000
        DT = 1e-1
        damp = 1e-12

        i = 0
        while True:
            pin.forwardKinematics(self.model, self.data, q)
            iMd = self.data.oMi[-1].actInv(oM_des)
            err = pin.log(iMd).vector  # in joint frame
            if np.linalg.norm(err) < eps:
                break
            if i >= IT_MAX:
                break
            J = self.get_jac(q)
            J = -np.dot(pin.Jlog6(iMd.inverse()), J)
            v = - J.T.dot(np.linalg.solve(J.dot(J.T) + damp * np.eye(6), err))
            q = pin.integrate(self.model, q, v * DT)
            i += 1

        return q.flatten()

    def get_inertia_mat(self, q: np.ndarray) -> np.ndarray:
        """ Computing the inertia matrix in the joint frame

        :param q: joint position
        :return: inertia matrix
        """
        return pin.crba(self.model, self.data, q)

    def get_coriolis_mat(self, q: np.ndarray, qdot: np.ndarray) -> np.ndarray:
        """ Computing the Coriolis matrix in the joint frame

        :param q: joint position
        :param qdot: joint velocity
        :return:
        """
        return pin.computeCoriolisMatrix(self.model, self.data, q, qdot)

    def get_gravity_mat(self, q: np.ndarray) -> np.ndarray:
        """ Computing the gravity matrix in the joint frame

        :param q: joint position
        :return: gravity matrix
        """
        return pin.computeGeneralizedGravity(self.model, self.data, q)

    def get_jac(self, q: np.ndarray) -> np.ndarray:
        """ Computing the Jacobian in the joint frame

        :param q: joint position
        :return: Jacobian
        """
        # return pin.computeJointJacobian(self.model, self.data, q, self.JOINT_NUM)
        return pin.computeJointJacobians(self.model, self.data, q)

    def get_jac_pinv(self, q: np.ndarray) -> np.ndarray:
        """ Computing the Jacobian_pinv in the joint frame

        :param q: joint position
        :return: Jacobian_pinv
        """
        return np.linalg.pinv(self.get_jac(q))

    def get_jac_dot(self, q: np.ndarray, v: np.ndarray) -> np.ndarray:
        """ Computing the Jacobian_dot in the joint frame

        :param q: joint position
        :param v: joint velocity
        :return: Jacobian_dot
        """
        pin.forwardKinematics(self.model, self.data, q)
        pin.computeAllTerms(self.model, self.data, q, v)
        return self.data.dJ
