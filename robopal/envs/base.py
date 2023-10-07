import abc

import mujoco
import numpy as np

from robopal.commons.renderers import MjRenderer


class MujocoEnv:
    """ This environment is the base class.

    :param xml_path(str): Load xml file from xml_path to build the mujoco model.
    :param is_render(bool): Choose if use the renderer to render the scene or not.
    :param renderer(str): choose official renderer with "viewer",
    another renderer with "mujoco_viewer"
    :param control_freq(int): Upper-layer control frequency.
    Note that high frequency will cause high time-lag.
    :param enable_camera_viewer(bool): Use camera or not.
    :param cam_mode(str): Camera mode, "rgb" or "depth".
    """

    def __init__(self,
                 robot=None,
                 is_render=False,
                 renderer="viewer",
                 control_freq=1000,
                 enable_camera_viewer=False,
                 cam_mode='rgb'):

        self.robot = robot
        self.is_render = is_render
        self.control_freq = control_freq

        self.mj_model: mujoco.MjModel = self.robot.robot_model
        self.mj_data: mujoco.MjData = self.robot.robot_data

        self.cur_time = 0
        self.timestep = 0
        self.model_timestep = 0
        self.control_timestep = 0
        self.robot_dof = self.robot.jnt_num

        self.renderer = MjRenderer(self.mj_model, self.mj_data, self.is_render, renderer, enable_camera_viewer,
                                   cam_mode)

        self._initialize_time()
        self._set_init_pose()

    def step(self, action):
        """ 
        This method will be called with one-step in mujoco
        :param action: Input action
        :return: None
        """
        if self.renderer is not None and self.renderer.render_paused:
            self.cur_time += 1
            self.inner_step(action)
            mujoco.mj_forward(self.mj_model, self.mj_data)
            mujoco.mj_step(self.mj_model, self.mj_data)

    @abc.abstractmethod
    def inner_step(self, action):
        """  This method will be called with one-step in mujoco, before mujoco step.
        For example, you can use this method to update the robot's joint position.

        :param action: input actions
        :return: None
        """
        raise NotImplementedError

    def reset(self):
        """ Reset the simulate environment, in order to execute next episode. """
        self.robot.construct_mjcf_data()
        self.mj_model = self.robot.robot_model
        mujoco.mj_resetData(self.mj_model, self.mj_data)
        self._set_init_pose()
        mujoco.mj_step(self.mj_model, self.mj_data)

    def render(self, mode="human"):
        """ render mujoco """
        if self.is_render is True:
            self.renderer.render()

    def close(self):
        """ close the environment. """
        self.renderer.close()

    def _initialize_time(self):
        """ Initializes the time constants used for simulation.

        :param control_freq (float): Hz rate to run control loop at within the simulation
        """
        self.cur_time = 0
        self.timestep = 0
        self.model_timestep = self.mj_model.opt.timestep
        if self.model_timestep <= 0:
            raise ValueError("Invalid simulation timestep defined!")
        if self.control_freq <= 0:
            raise ValueError("Control frequency {} is invalid".format(self.control_freq))
        self.control_timestep = 1.0 / self.control_freq

    def _set_init_pose(self):
        """ Set or reset init joint position when called env reset func. """
        for i in range(len(self.robot.arm)):
            for j in range(len(self.robot.arm[i].joint_index)):
                self.mj_data.joint(self.robot.arm[i].joint_index[j]).qpos = self.robot.arm[i].init_pose[j]
        mujoco.mj_forward(self.mj_model, self.mj_data)

    def get_body_id(self, name: str):
        """ Get body id from body name.

        :param name: body name
        :return: body id
        """
        return mujoco.mj_name2id(self.mj_model, mujoco.mjtObj.mjOBJ_BODY, name)

    def get_body_jacp(self, name):
        """ Query the position jacobian of a mujoco body using a name string.

        :param name: The name of a mujoco body
        :return: The jacp value of the mujoco body
        """
        bid = self.get_body_id(name)
        jacp = np.zeros((3, self.mj_model.nv))
        mujoco.mj_jacBody(self.mj_model, self.mj_data, jacp, None, bid)
        return jacp

    def get_body_jacr(self, name):
        """ Query the rotation jacobian of a mujoco body using a name string.

        :param name: The name of a mujoco body
        :return: The jacr value of the mujoco body
        """
        bid = self.get_body_id(name)
        jacr = np.zeros((3, self.mj_model.nv))
        mujoco.mj_jacBody(self.mj_model, self.mj_data, None, jacr, bid)
        return jacr

    def get_body_pos(self, name: str):
        """ Get body position from body name.

        :param name: body name
        :return: body position
        """
        return self.mj_data.body(name).xpos.copy()

    def get_body_quat(self, name: str):
        """ Get body quaternion from body name.

        :param name: body name
        :return: body quaternion
        """
        return self.mj_data.body(name).xquat.copy()

    def get_body_rotm(self, name: str):
        """ Get body rotation matrix from body name.

        :param name: body name
        :return: body rotation matrix
        """
        return self.mj_data.body(name).xmat.copy().reshape(3, 3)

    def get_body_xvelp(self, name: str) -> np.ndarray:
        """ Get body velocity from body name.

        :param name: body name
        :return: translational velocity of the body
        """
        jacp = self.get_body_jacp(name)
        xvelp = np.dot(jacp, self.mj_data.qvel)
        return xvelp.copy()

    def get_body_xvelr(self, name: str) -> np.ndarray:
        """ Get body rotational velocity from body name.

        :param name: body name
        :return: rotational velocity of the body
        """
        jacr = self.get_body_jacr(name)
        xvelr = np.dot(jacr, self.mj_data.qvel)
        return xvelr.copy()

    def get_site_id(self, name: str):
        """ Get site id from site name.

        :param name: site name
        :return: site id
        """
        return mujoco.mj_name2id(self.mj_model, mujoco.mjtObj.mjOBJ_SITE, name)

    def get_site_jacp(self, name):
        """ Query the position jacobian of a mujoco site using a name string.

        :param name: The name of a mujoco site
        :return: The jacp value of the mujoco site
        """
        sid = self.get_site_id(name)
        jacp = np.zeros((3, self.mj_model.nv))
        mujoco.mj_jacSite(self.mj_model, self.mj_data, jacp, None, sid)
        return jacp

    def get_site_pos(self, name: str):
        """ Get body position from site name.

        :param name: site name
        :return: site position
        """
        return self.mj_data.site(name).xpos.copy()

    def get_site_xvelp(self, name: str) -> np.ndarray:
        """ Get site velocity from site name.

        :param name: site name
        :return: translational velocity of the site
        """
        jacp = self.get_site_jacp(name)
        xvelp = np.dot(jacp, self.mj_data.qvel)
        return xvelp.copy()
