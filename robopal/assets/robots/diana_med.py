import os
import numpy as np

from robopal.assets.robots.base import *


class DianaMedBase(BaseArm):
    """ DianaMed robot base class. """

    def __init__(self,
                 scene='default',
                 gripper=None,
                 mount=None
                 ):
        super().__init__(
            name="diana_med",
            scene=scene,
            chassis=mount,
            manipulator='DianaMed',
            gripper=gripper,
            g2m_body=['0_link7'],
            urdf_path=os.path.join(os.path.dirname(__file__), "../models/manipulators/DianaMed/DianaMed.urdf"),
        )
        self.single_arm = self.PartArm(self, 'single')
        self.single_arm.joint_index = ['0_j1', '0_j2', '0_j3', '0_j4', '0_j5', '0_j6', '0_j7']
        self.single_arm.actuator_index = ['0_a1', '0_a2', '0_a3', '0_a4', '0_a5', '0_a6', '0_a7']
        self.single_arm.setArmInitPose(self.init_qpos)
        self.arm.append(self.single_arm)

        self.jnt_num = self.single_arm.jnt_num

    @property
    def init_qpos(self):
        """ Robot's init joint position. """
        return np.array([0.0, -np.pi / 4.0, 0.0, np.pi / 2.0, 0.00, np.pi / 4.0, 0.0])


class DianaMed(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='default',
                         gripper=None, )


class DianaAruco(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='default',
                         gripper='Swab_gripper', )

    def add_assets(self):
        self.mjcf_generator.add_texture('aruco', type='2d',
                                        file=os.path.join(os.path.dirname(__file__), '../textures/aruco.png'))
        self.mjcf_generator.add_material('aruco', texture='aruco', texrepeat='1 1', texuniform='false')
        self.mjcf_generator.add_body(node='worldbody', name='aruco')
        self.mjcf_generator.add_geom(node='aruco', name='aruco_box', pos='0.919 0 1.27', mass='0.001',
                                     euler="0 -1.57 0", size='0.05 0.05 0.001', type='box', material='aruco')
        self.mjcf_generator.add_joint(node='aruco', name='aruco_x', type='slide', axis='1 0 0')
        self.mjcf_generator.add_joint(node='aruco', name='aruco_y', type='slide', axis='0 1 0')
        self.mjcf_generator.add_joint(node='aruco', name='aruco_z', type='slide', axis='0 0 1')


class DianaGrasp(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='grasping',
                         gripper='rethink_gripper',
                         mount='top_point')

    def add_assets(self):
        self.mjcf_generator.add_node_from_xml('worldbody', os.path.dirname(__file__) + '/../objects/cube/green_cube.xml')
        self.mjcf_generator.set_node_attrib('green_block', {'pos': '0.5 0.0 0.46'})

        goal_site = """<site name="goal_site" pos="0.4 0.0 0.5" size="0.02 0.02 0.02" rgba="1 0 0 1" type="sphere" />"""
        self.mjcf_generator.add_node_from_str('worldbody', goal_site)

    @property
    def init_qpos(self):
        """ Robot's init joint position. """
        return np.array([0.02167871, -0.16747492, 0.00730963, 2.5573341, -0.00401727, -0.42203728, -0.01099269])


class DianaGraspMultiObjs(DianaGrasp):
    """ DianaMed robot class. """

    def add_assets(self):
        OBJ_NAMES = ['green_block', 'red_block', 'blue_block']

        self.mjcf_generator.add_node_from_xml('worldbody', os.path.dirname(__file__) + '/../objects/cube/green_cube.xml')
        self.mjcf_generator.set_node_attrib('green_block', {'pos': '0.5 0.0 0.46'})

        self.mjcf_generator.add_node_from_xml('worldbody', os.path.dirname(__file__) + '/../objects/cube/blue_cube.xml')
        self.mjcf_generator.set_node_attrib('blue_block', {'pos': '0.5 0.1 0.46'})

        self.mjcf_generator.add_node_from_xml('worldbody', os.path.dirname(__file__) + '/../objects/cube/red_cube.xml')
        self.mjcf_generator.set_node_attrib('red_block', {'pos': '0.5 -0.1 0.46'})

        goal_site = """<site name="goal_site" pos="0.4 0.0 0.5" size="0.02 0.02 0.02" rgba="1 0 0 1" type="sphere" />"""
        self.mjcf_generator.add_node_from_str('worldbody', goal_site)


class DianaDrawer(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='grasping',
                         gripper='rethink_gripper',
                         mount='top_point')

    def add_assets(self):
        # add cupboard with fixed position
        self.mjcf_generator.add_mesh('cupboard', 'objects/cupboard/cupboard.stl', scale='0.001 0.001 0.001')
        self.mjcf_generator.add_mesh('drawer', 'objects/cupboard/drawer.stl', scale='0.001 0.001 0.001')
        self.mjcf_generator.add_node_from_xml('worldbody',
                                              os.path.dirname(__file__) + '/../objects/cupboard/cupboard.xml')
        self.mjcf_generator.set_node_attrib('cupboard', {'pos': '0.66 0.0 0.42'})

        # add goal site with random position
        goal_site = """<site name="goal_site" pos="0.56 0.0 0.478" size="0.01 0.01 0.01" rgba="1 0 0 1" type="sphere" />"""
        self.mjcf_generator.add_node_from_str('worldbody', goal_site)

    @property
    def init_qpos(self):
        """ Robot's init joint position. """
        return np.array([-0.51198529, -0.44737435, -0.50879166, 2.3063219, 0.46514545, -0.48916244, -0.37233289])


class DianaCabinet(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='grasping',
                         gripper='rethink_gripper',
                         mount='top_point')

    def add_assets(self):
        self.mjcf_generator.add_node_from_xml('worldbody', os.path.dirname(__file__) + '/../objects/cabinet/cabinet.xml')
        self.mjcf_generator.add_node_from_xml('worldbody', os.path.dirname(__file__) + '/../objects/cabinet/beam.xml')

        # add goal site with random position
        # goal_site = """<site name="goal_site" pos="0.56 0.0 0.478" size="0.01 0.01 0.01" rgba="1 0 0 1" type="sphere" />"""
        # self.mjcf_generator.add_node_from_str('worldbody', goal_site)

    @property
    def init_qpos(self):
        """ Robot's init joint position. """
        return np.array([-0.71325374, 0.07279728, -0.72080385, 2.5239552, -0.07686951, -0.67930021, 0.05372948])


class DianaDrawerCube(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='grasping',
                         gripper='rethink_gripper',
                         mount='top_point')

    def add_assets(self):
        self.mjcf_generator.add_mesh('cupboard', 'objects/cupboard/cupboard.stl', scale='0.001 0.001 0.001')
        self.mjcf_generator.add_mesh('drawer', 'objects/cupboard/drawer.stl', scale='0.001 0.001 0.001')
        cupboard_x_pos = 0.66
        cupboard_y_pos = 0.0
        self.mjcf_generator.add_node_from_xml('worldbody',
                                              os.path.dirname(__file__) + '/../objects/cupboard/cupboard.xml')
        self.mjcf_generator.set_node_attrib('cupboard', {'pos': f'{cupboard_x_pos} {cupboard_y_pos} {0.42}'})

        # add cube with random position
        self.mjcf_generator.add_node_from_xml('worldbody',
                                              os.path.dirname(__file__) + '/../objects/cube/green_cube.xml')
        self.mjcf_generator.set_node_attrib('green_block', {'pos': '0.5 0.0 0.46'})

        goal_site = """<site name="drawer_goal" pos="0.48 0.0 0.478" size="0.01 0.01 0.01" rgba="1 0 0 1" type="sphere" />"""
        self.mjcf_generator.add_node_from_str('worldbody', goal_site)

    @property
    def init_qpos(self):
        """ Robot's init joint position. """
        return np.array([-0.64551607, -0.29859465, -0.66478589, 2.3211311, 0.3205733, -0.61377277, -0.26366202])


class DianaPainting(DianaMedBase):
    """ DianaMed robot class. """

    def __init__(self):
        super().__init__(scene='grasping',
                         gripper='Swab_gripper',
                         mount='top_point')

    @property
    def init_qpos(self):
        """ Robot's init joint position. """
        return np.array([-0.51198529, -0.44737435, -0.50879166, 2.3063219, 0.46514545, -0.48916244, -0.37233289])
