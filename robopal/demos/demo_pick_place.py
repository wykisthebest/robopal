import numpy as np
import logging

from robopal.envs.task_ik_ctrl_env import PosCtrlEnv
import robopal.commons.transform as trans

logging.basicConfig(level=logging.INFO)


class PickAndPlaceEnv(PosCtrlEnv):
    """ Reference: https://robotics.farama.org/envs/fetch/pick_and_place/#
    The control frequency of the robot is of f = 20 Hz. This is achieved by applying the same action
    in 50 subsequent simulator step (with a time step of dt = 0.0005 s) before returning the control to the robot.
    """
    metadata = {"render_modes": ["human", "rgb_array"]}

    def __init__(self,
                 robot=None,
                 is_render=True,
                 renderer="viewer",
                 render_mode='human',
                 control_freq=200,
                 enable_camera_viewer=False,
                 cam_mode='rgb',
                 jnt_controller='IMPEDANCE',
                 is_interpolate=False,
                 is_pd=False,
                 ):
        super().__init__(
            robot=robot,
            is_render=is_render,
            renderer=renderer,
            control_freq=control_freq,
            enable_camera_viewer=enable_camera_viewer,
            cam_mode=cam_mode,
            jnt_controller=jnt_controller,
            is_interpolate=is_interpolate,
            is_pd=is_pd,
        )
        self.name = 'PickAndPlace-v1'

        self.obs_dim = (19,)
        self.goal_dim = (3,)
        self.action_dim = (4,)

        self.max_action = 1.0
        self.min_action = -1.0

        self.max_episode_steps = 50
        self._timestep = 0

        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode

    def step(self, action) -> tuple:
        """ Take one step in the environment.

        :param action:  The action space is 4-dimensional, with the first 3 dimensions corresponding to the desired
        position of the block in Cartesian coordinates, and the last dimension corresponding to the
        desired gripper opening (0 for closed, 1 for open).
        :return: obs, reward, terminated, truncated, info
        """
        self._timestep += 1
        # Map to target action space bounds
        pos_ctrl = (action[3] + 1) * (0.0115 - (-0.015)) / 2 + (-0.015)

        pos_offset = 0.05 * action[:3]
        actual_pos_action = self.kdl_solver.fk(self.robot.single_arm.arm_qpos)[0] + pos_offset

        pos_max_bound = np.array([0.6, 0.2, 0.4])
        pos_min_bound = np.array([0.3, -0.2, 0.14])
        actual_pos_action = actual_pos_action.clip(pos_min_bound, pos_max_bound)

        # take one step
        # self.gripper_ctrl('0_gripper_l_finger_joint', int(actual_action[3]))
        self.mj_data.joint('0_r_finger_joint').qpos[0] = pos_ctrl

        logging.debug(f'des_pos:{actual_pos_action[:3]}')
        super().step(actual_pos_action[:3])
        logging.debug(f'cur_pos:{self.kdl_solver.fk(self.robot.single_arm.arm_qpos)[0]}')

        obs = self._get_obs()
        achieved_goal = obs['achieved_goal']
        desired_goal = obs['desired_goal']
        reward = self.compute_rewards(achieved_goal, desired_goal)
        terminated = False
        truncated = False
        if self._timestep >= self.max_episode_steps:
            truncated = True
        info = self._get_info()

        if self.render_mode == 'human':
            self.render()

        return obs, reward, terminated, truncated, info

    def inner_step(self, action):
        super().inner_step(action)

    def compute_rewards(self, achieved_goal: np.ndarray, desired_goal: np.ndarray, info: dict=None):
        """ Sparse Reward: the returned reward can have two values: -1 if the block hasn’t reached its final
        target position, and 0 if the block is in the final target position (the block is considered to have
        reached the goal if the Euclidean distance between both is lower than 0.05 m).
        """
        assert achieved_goal.shape == desired_goal.shape
        dist = np.linalg.norm(achieved_goal - desired_goal, axis=-1)
        return -(dist > 0.05).astype(np.floating)

    def _get_obs(self) -> np.ndarray:
        """ The observation space is 16-dimensional, with the first 3 dimensions corresponding to the position
        of the block, the next 3 dimensions corresponding to the position of the goal, the next 3 dimensions
        corresponding to the position of the gripper, the next 3 dimensions corresponding to the vector
        between the block and the gripper, and the last dimension corresponding to the current gripper opening.
        """
        obs = np.zeros(self.obs_dim)

        obs[:3] = self.get_body_pos('green_block')
        obs[3:6] = self.get_body_pos('goal_site')
        obs[6:9] = self.kdl_solver.fk(self.robot.single_arm.arm_qpos)[0]
        obs[9:12] = obs[6:9] - obs[:3]  # vector between the block and the gripper
        obs[12] = self.mj_data.actuator("0_gripper_l_finger_joint").ctrl[0]
        obs[13:16] = trans.mat_2_euler(self.get_body_rotm('green_block'))
        obs[16:19] = self.kdl_solver.get_end_vel(self.robot.single_arm.arm_qpos, self.robot.single_arm.arm_qvel)[:3]

        return {
            'observation': obs.copy(),
            'achieved_goal': obs[:3].copy(),  # the current state of the block
            'desired_goal': obs[3:6].copy()
        }

    def _get_info(self) -> dict:
        return {}

    def reset(self, seed=None):
        super().reset()
        self._timestep = 0

        obs = self._get_obs()
        info = self._get_info()

        if self.render_mode == 'human':
            self.render()

        return obs, info


if __name__ == "__main__":
    from robopal.assets.robots.diana_med import DianaGrasp

    env = PickAndPlaceEnv(
        robot=DianaGrasp(),
        renderer="viewer",
        is_render=True,
        control_freq=10,
        is_interpolate=False,
        is_pd=False,
        jnt_controller='IMPEDANCE',
    )
    env.reset()

    for t in range(int(1e6)):
        action = np.random.uniform(env.min_action, env.max_action, env.action_dim)
        s_, r, terminated, truncated, _ = env.step(action)
        if truncated:
            env.reset()
