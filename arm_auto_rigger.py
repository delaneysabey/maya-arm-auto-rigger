import maya.cmds as cmds
import re
def create_line_attach_and_deform(selected_side, curve_name, joint_name):
   
    #curve_name = 'IK_elbow_CTRL_%s' % selected_side
    #joint_name = 'IK_elbow_JNT_%s' % selected_side
   
    # Create the line curve with two control vertices
    line_curve = cmds.curve(d=1, p=[(0, 0, 0), (1, 0, 0)])
    finger_name = get_finger_name(joint_name)
    if finger_name == "unknown":
        line_curve = cmds.rename(line_curve, "IK_elbow_VIZ_%s" % selected_side)
    else:
        line_curve = cmds.rename(line_curve, "IK_%s_knuckle_VIZ_%s" % (finger_name, selected_side))
    
    BLUE_1 = [0.264, 0.623, 1]
    BLUE_2 = [0.053, 0.352, 1]
    RED_1 = [1.0, 0.399, 0.325]
    RED_2 = [1.0, 0.132, 0.084]
    color_1 = 0
    color_2 = 0
    
    # Color the skeleton
    if selected_side == 'L':
        color_1, color_2 = BLUE_1, BLUE_2
    else:
        color_1, color_2 = RED_1, RED_2
        
    set_color(line_curve, color_1, color_2)
        
   
    # Attach one control vertex to the curve
    attached_point = cmds.pointOnCurve(curve_name, pr=0.5, position=True)
    cmds.move(attached_point[0], attached_point[1], attached_point[2], line_curve + ".cv[0]", absolute=True)
   
    # Attach the other control vertex to the joint
    joint_position = cmds.xform(joint_name, query=True, translation=True, worldSpace=True)
    cmds.move(joint_position[0], joint_position[1], joint_position[2], line_curve + ".cv[1]", absolute=True)
   
    cluster_handle_01_name = line_curve + "_cluster_01_"
    cluster_handle_02_name = line_curve + "_cluster_02_"
    # Create a cluster deformer on the joint-attached control vertex
    cluster_handle_01 = cmds.cluster(line_curve + ".cv[1]", n=cluster_handle_01_name)[1]
   
    # Create a cluster deformer on the joint-attached control vertex
    cluster_handle_02 = cmds.cluster(line_curve + ".cv[0]", n=cluster_handle_02_name)[0]
    cluster_handle_01_name = line_curve + "_cluster_01_Handle"
    cluster_handle_02_name = line_curve + "_cluster_02_Handle"
    # Parent constrain the cluster handle to the joint
    parent_constraint = cmds.parentConstraint(joint_name, cluster_handle_01_name, maintainOffset=True)[0]
    parent_constraint = cmds.parentConstraint(curve_name, cluster_handle_02_name, maintainOffset=True)
    
    VIZ_group_name = "GRP_VIZ_%s_%s" % (line_curve, selected_side)
    VIZ_group = cmds.group(empty=True, name=VIZ_group_name)
    
    cmds.parent(cluster_handle_01_name, VIZ_group)
    cmds.parent(cluster_handle_02_name, VIZ_group)
    cmds.parent(line_curve, VIZ_group)
    cmds.setAttr(line_curve + '.inheritsTransform', 0)
    
    cmds.hide(cluster_handle_01_name)
    cmds.hide(cluster_handle_02_name)
    #cmds.select(cluster_handle)
    
    return VIZ_group_name

def reduce_joint_radius(joint_name):
    # Get the original radius of the specified joint
    original_radius = cmds.getAttr(joint_name + '.radius')
   
    # Calculate the new radius as half of the original radius
    new_radius = original_radius * 0.5
   
    # Set the new radius of the specified joint
    cmds.joint(joint_name, edit=True, radius=new_radius)
   
    # Get all the children of the joint
    children = cmds.listRelatives(joint_name, allDescendents=True, type='joint')
   
    # Set the new radius of each child joint
    if children:
        for child in children:
            cmds.joint(child, edit=True, radius=new_radius)
           
def parent_constraint_corresponding_joints():
    source_prefix = "TRG_"
    target_prefix = "BIND_"
    joint_list = cmds.ls(type="joint")

    for source_joint in joint_list:
        if source_joint.startswith(source_prefix):
            target_joint = target_prefix + source_joint[len(source_prefix):]

            if cmds.objExists(target_joint):
                cmds.parentConstraint(source_joint, target_joint, mo=True)

def create_new_skeleton(root_joint, prefix, selected_side):
    # Duplicate the root joint
    duplicate_root = cmds.duplicate(root_joint, renameChildren=True)[0]
    BLUE_1 = [0.264, 0.623, 1]
    BLUE_2 = [0.053, 0.352, 1]
    RED_1 = [1.0, 0.399, 0.325]
    RED_2 = [1.0, 0.132, 0.084]
    color_1 = 0
    color_2 = 0
    # Color the skeleton
    if prefix == 'IK':
        color_1, color_2 = BLUE_1, BLUE_2
    else:
        color_1, color_2 = RED_1, RED_2
     
    # Get all the children of the joint and recursively color them
    set_color(duplicate_root, color_1, color_2)
    children = cmds.listRelatives(duplicate_root, allDescendents=True, type='joint')
    if children:
        for child in children:
            set_color(child, color_1, color_2)
           
       
    # Reduce the radius
    reduce_joint_radius(duplicate_root)

    # Rename and store the duplicate root
    new_skeleton_root = duplicate_root.replace("BIND", prefix)[:-1]
    cmds.rename(duplicate_root, new_skeleton_root)
   
    # Rename the duplicated joints
    duplicate_joints = cmds.listRelatives(new_skeleton_root, allDescendents=True, type='joint')
   
    for joint in duplicate_joints:
        new_name = joint.replace("BIND", prefix)[:-1]
        cmds.rename(joint, new_name)
       

    return new_skeleton_root
   
def set_color(input, color1, color2):
    cmds.setAttr(input + '.useOutlinerColor', 1)
    cmds.setAttr(input + '.outlinerColor', color1[0], color1[1], color1[2])
    cmds.setAttr(input + '.overrideEnabled', True)
    cmds.setAttr(input + '.overrideRGBColors', 1)
    cmds.setAttr(input + '.overrideColorRGB', color2[0], color2[1], color2[2])
   
def blend_between_skeletons(root_joint):
    # Get the direct child of the joint
    root_joint = cmds.listRelatives(root_joint, c=True, type='joint')[0]
     
    # Get the names of the IK and FK joints
    IK_joint = root_joint.replace("TRG_", "IK_")
    print("IK_joint ", IK_joint)
    FK_joint = root_joint.replace("TRG_", "FK_")
    print("FK joint ", FK_joint)
    # Select the IK, FK, and TRG joints
    cmds.select(IK_joint, FK_joint, root_joint, replace=True)

    # Apply parent constraint with maintain offset off
    cmds.parentConstraint(mo=False)

    # Get all the children joints of the root joint
    children_joints = cmds.listRelatives(root_joint, allDescendents=True, type='joint')

    if children_joints:
        # Iterate over the children joints and apply parent constraints
        for child_joint in children_joints:
            # Get the names of the IK and FK joints for the child joint
            child_IK_joint = child_joint.replace("TRG_", "IK_")
            child_FK_joint = child_joint.replace("TRG_", "FK_")

            # Apply parent constraint between the child joint's IK, FK, and TRG joints
            cmds.select(child_IK_joint, child_FK_joint, child_joint, replace=True)
            cmds.parentConstraint(mo=False)

    # Print the result
    print("Parent constraints applied between corresponding joints.")
   
def create_FK_chain(joint_list, selected_side):      
    # Create a list to store all the children
    #children_chain = [root_joint]
   
    # Recursively get all the children joints
    #get_children_chain(root_joint, children_chain)
   
    # Create a list to store the control names
    control_chain = []
    offset_groups = []
   
    # Create a control for each joint in the list
    for child in joint_list:
        # Create a control
        control_name = child.replace("JNT", "CTRL")
        control = 0
       
        # If this is the arm, create a circle control
        if 'shoulder' in joint_list[0]:
            control = cmds.circle(name=control_name, radius=5.0)
            cmds.rotate(0,90,0)
           
        # If this is a finger, create a pin conrol
        else:
            control = cmds.curve(d= 1 , p=[(0.0, 0.0, 0.0), (0.0, 2.0, 0.0), (0.0, 3.0, 1.0), (0.0, 4.0, 0.0), (0.0, 3.0, -1.0), (0, 2, 0)], k= [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], n=control_name)

        #cmds.makeIdentity(control, a=True)
        # Color the control according to the selected side    
        if selected_side == 'L':
            BLUE_1 = [0.264, 0.623, 1]
            BLUE_2 = [0.053, 0.352, 1]
            set_color(control_name, BLUE_1, BLUE_2)
        else:
            RED_1 = [1.0, 0.399, 0.325]
            RED_2 = [1.0, 0.132, 0.084]
            set_color(control_name, RED_1, RED_2)

        # Create an offset group for the control
        FK_control_offset_group_name = control_name + "_offset"
        FK_control_offset_group = cmds.group(empty=True, name=FK_control_offset_group_name)
       
        # Add the offset group to the offset_groups list
        offset_groups.append(FK_control_offset_group)
       
        # Parent the control under the offset group
        cmds.parent(control, FK_control_offset_group)
       
        # Match pivot of the offset group to the pivot of the control
        cmds.matchTransform(FK_control_offset_group, control, pivots=True)
       
        # Get the position of the joint
        joint_position = cmds.xform(child, query=True, translation=True, worldSpace=True)
       
        # Set the position of the offset_group to match the joint
        cmds.xform(FK_control_offset_group, translation=joint_position, worldSpace=True)
       
        # Get the orientation of the joint
        joint_orientation = cmds.xform(child, query=True, rotation=True, worldSpace=True)
       
        # Set the orientation of the offset_group to match the joint
        #cmds.xform(FK_control_offset_group, rotation=joint_orientation, worldSpace=False)
        cmds.select(FK_control_offset_group)
        cmds.select(child, add=True)
        cmds.matchTransform()
        
        if selected_side == 'L':
                #if get_finger_name(child) != 'Thumb':
            if 'shoulder' not in joint_list[0]:
                cmds.select(control)
                cmds.rotate(-90,0,0, r=True)
                #cmds.rotate(-90,0,-90)
        else:
                #if get_finger_name(child) != 'Thumb':
            if 'shoulder' not in joint_list[0]:
                cmds.select(control)
                cmds.rotate(90,0,0, r=True)
     
        # Add the control name to the control_chain list
        control_chain.append(control_name)
   
        # Freeze the transforms of the control and offset group
        cmds.makeIdentity(control_name, apply=True, translate=True, rotate=True, scale=True)
        cmds.makeIdentity(FK_control_offset_group, apply=True, translate=True, rotate=False, scale=True)

        # Parent constraint the control to the child joint
        cmds.parentConstraint(control, child, maintainOffset=True)
       
        if joint_list.index(child) == 0 and get_finger_name(child) != 'Arm':
            # Parent the corresponding joint under the control
            cmds.parentConstraint(control, child.replace('FK', 'IK'), maintainOffset=True)
   
    # Parent the controls to create a hierarchy
    for i in range(len(control_chain) - 1):
        cmds.parent(offset_groups[i + 1], control_chain[i])        
   
    # Return the first two so that we can also access the hand_knuckle
    return offset_groups[0], offset_groups[1]

def get_children_chain(joint, children_chain):
    children = cmds.listRelatives(joint, children=True, type='joint')
    if children:
        children_chain.extend(children)
        for child in children:
            get_children_chain(child, children_chain)
    return children_chain
           
def create_IK_handle(joint_list, selected_side):
   
    # Get the root joint
    root_joint = joint_list[0]
   
    if cmds.nodeType(root_joint) == 'joint':
        print("root_joint is a joint")
    else:
        print("root_joint is not a joint")
   
   
    print("root joint ", root_joint)
   
    # Get the last child joint
    last_child_joint = joint_list[-1]
       
    print("last_child_joint = ", last_child_joint)
   
    appendage = get_finger_name(root_joint)
    if appendage == 'unknown':
        appendage = 'Arm'
    handle_name = appendage + '_ikHandle_%s' % selected_side
    effector_name = appendage + '_effector_%s' % selected_side
    # Create an IK handle from root to last child and then hide it
    ik_handle, effector = cmds.ikHandle(startJoint=root_joint, endEffector=last_child_joint, solver="ikRPsolver", n = handle_name)
    cmds.hide(ik_handle)
    cmds.rename(effector, effector_name)
   
    # Create a square control for the IK handle
    control_name = last_child_joint.replace("JNT", "CTRL")
    control = cmds.curve(
        name=control_name,
        d=1,
        p=[(-1, 0, 1), (1, 0, 1), (1, 0, -1), (-1, 0, -1), (-1, 0, 1)],
        k=[0, 1, 2, 3, 4]
    )
   
    if selected_side == 'L':
        BLUE_1 = [0.264, 0.623, 1]
        BLUE_2 = [0.053, 0.352, 1]
        set_color(control_name, BLUE_1, BLUE_2)
    else:
        RED_1 = [1.0, 0.399, 0.325]
        RED_2 = [1.0, 0.132, 0.084]
        set_color(control_name, RED_1, RED_2)
   
    # Get the orientation of the joint
    joint_orientation = cmds.xform(last_child_joint, query=True, rotation=True, worldSpace=True)
    if 'shoulder' in root_joint:
        cmds.rotate(0,0,90, control)
    if 'finger' in root_joint:
        print("FINGER ROTATE")
        cmds.rotate(0,0,90,control)
    cmds.makeIdentity(control, apply=True, translate=True, rotate=True, scale=True)
    cmds.xform(control, rotation=joint_orientation, worldSpace=True)

    # If this control is for the arm, increase the scale
    if 'shoulder' in root_joint:
        cmds.scale(5, 5, 5, control)

    # Position the control at the same location as the last child joint
    joint_position = cmds.xform(last_child_joint, query=True, translation=True, worldSpace=True)
    cmds.xform(control, translation=joint_position, worldSpace=True)
   
   
    # Parent the IK handle under the control
    cmds.parent(ik_handle, control)
   
    # Create an offset group for the IK control
    IK_control_offset_group_name = control_name + '_offset'
    IK_control_offset_group = cmds.group(empty=True, name=IK_control_offset_group_name)
   
    # Parent the IK control under the IK offset group
    cmds.parent(control, IK_control_offset_group)
   
    # Create a pole vector control
    pole_vector_name = control_name.replace('_CTRL', '_knuckle_CTRL')
    if 'shoulder' in root_joint:
        pole_vector_name = control_name.replace('wrist', 'elbow')
    pole_vector = cmds.curve(
        name=pole_vector_name,
        d=1,
        p=[(0, 2, 0), (-1, 0, 0), (1, 0, 0), (0, 2, 0)],
        k=[0, 1, 2, 3]
    )
   
   
   
    if selected_side == 'L':
        BLUE_1 = [0.264, 0.623, 1]
        BLUE_2 = [0.053, 0.352, 1]
        set_color(pole_vector_name, BLUE_1, BLUE_2)
    else:
        RED_1 = [1.0, 0.399, 0.325]
        RED_2 = [1.0, 0.132, 0.084]
        set_color(pole_vector_name, RED_1, RED_2)
    # If this is the arm, increase the scale of the pole_vector and rotate -90 degrees
    if 'shoulder' in root_joint:
        cmds.scale(3, 3, 3, pole_vector)
        if selected_side == 'L':
            cmds.rotate(-90, 0, -90, pole_vector)
        else:
            cmds.rotate(90, 0, 90, pole_vector)
    else:
        cmds.rotate(-90, 0, 0, pole_vector)
        if selected_side == 'L':
            cmds.rotate(-90, 0, -90, pole_vector)
        else:
            cmds.rotate(90, 0, 90, pole_vector)

    # Create an offset group for the IK control
    PV_offset_group_name = pole_vector_name + '_offset'
    PV_offset_group = cmds.group(empty=True, name=PV_offset_group_name)

    # Position the pole vector control above the second joint in the joint list
    second_joint_position = cmds.xform(joint_list[1], query=True, translation=True, worldSpace=True)
   
    # If this is the arm, position the pole vector behind the elbow
    if 'shoulder' in joint_list[0]:
        pole_vector_position = [second_joint_position[0], second_joint_position[1], second_joint_position[2] - 10]
    # If this is a finger, position the pole vector above the finger knuckle
    else:
        pole_vector_position = [second_joint_position[0], second_joint_position[1], second_joint_position[2]]
    cmds.xform(pole_vector, translation=pole_vector_position, worldSpace=True)
   
    # Get the orientation of the joint
    joint_orientation = cmds.xform(last_child_joint, query=True, rotation=True, worldSpace=True)
    cmds.makeIdentity(pole_vector, apply=True, translate=True, rotate=True, scale=True)
    cmds.xform(pole_vector, rotation=joint_orientation, worldSpace=True)
   
    # Create a pole vector constraint between the pole vector and the IK handle
    pole_vector_constraint = cmds.poleVectorConstraint(pole_vector, ik_handle)

    # Parent the pole vector control under the offset group
    cmds.parent(pole_vector, PV_offset_group)
       
    # Freeze the transforms of the control and offset group
    cmds.makeIdentity(control, apply=True, translate=True, rotate=True, scale=True)
    cmds.makeIdentity(PV_offset_group, apply=True, translate=True, rotate=True, scale=True)
       
    # Center the pivot of the offset group
    cmds.xform(PV_offset_group, centerPivots=True)
   
    # parent constrain the IK wrist control to the IK wrist joint
    if 'shoulder' in root_joint:
        print("IK WRIST CONTOL NAME ", control)
        print("LAST_CHILD_JOINT = ", last_child_joint)
        cmds.orientConstraint(control, last_child_joint, mo=True)
   
    # Print the result
    print("IK handle created from", root_joint, "to", last_child_joint)
    print("Control created:", control_name)
   
    print("ik offset grp ", IK_control_offset_group)
    print("pv offset grp ", PV_offset_group)

    IK_elbow_VIZ = create_line_attach_and_deform(selected_side, pole_vector, joint_list[1])
    return IK_control_offset_group, PV_offset_group, IK_elbow_VIZ
   
def get_finger_name(string):
    match = re.search(r'[1-9]', string)
   
    if match:
        first_digit = int(match.group())
       
        if first_digit == 1:
            result = "Thumb"
        elif first_digit == 2:
            result = "Pointer"
        elif first_digit == 3:
            result = "Middle"
        elif first_digit == 4:
            result = "Ring"
        elif first_digit == 5:
            result = "Pinky"
        else:
            result = "unknown"
    else:
        result = "unknown"
   
    return result
   
def create_switch_control(selected_side):
    print("selected side is ", selected_side)
    # Find the wrist joint
    wrist_joint = None
    joints = cmds.ls(type='joint')
    for joint in joints:
        #print("joint[-1] = ", joint[-1])
        if 'BIND' in joint and 'wrist' in joint:
            if joint[-1] == selected_side:
                wrist_joint = joint
                print("found wrist joint ", wrist_joint)
                break
   
    if not wrist_joint:
        print("Wrist joint not found.")
        return
       
    # Create the switch control
    switch_control_name = 'SWITCH_ARM_CTRL_%s' % selected_side
    switch_control = cmds.curve(d=1, p=[(-5, 0.0, -5), (0, 0.0, -5), (0, 0.0, -10), (5, 0.0, -10), (5, 0.0, -15), (0.0, 0, -15), (0, 0.0, -20), (-5, 0.0, -20), (-5, 0, -15), (-10, 0.0, -15), (-10, 0.0, -10), (-5, 0.0, -10), (-5, 0.0, -5)],
    name=switch_control_name)
   
    if selected_side == 'L':
        BLUE_1 = [0.264, 0.623, 1]
        BLUE_2 = [0.053, 0.352, 1]
        set_color(switch_control_name, BLUE_1, BLUE_2)
    else:
        RED_1 = [1.0, 0.399, 0.325]
        RED_2 = [1.0, 0.132, 0.084]
        set_color(switch_control_name, RED_1, RED_2)
   
    # Rotate the control 90 degrees in the  direction
    cmds.rotate(90,0,0, switch_control, r=True)
   
    # Position the switch control at the wrist joint
    wrist_joint_position = cmds.xform(wrist_joint, query=True, translation=True, worldSpace=True)
    cmds.xform(switch_control, translation=wrist_joint_position, worldSpace=True)

    # Freeze the transforms on the control
    cmds.makeIdentity(switch_control, apply=True, translate=True, rotate=True, scale=True)
   
    # Create an offset group for the control
    offset_group_name = switch_control_name + '_offset'
    offset_group = cmds.group(empty=True, name=offset_group_name)
   
    # Parent the switch control to the offset group
    cmds.parent(switch_control, offset_group)
   
    # Center the pivot of the offset group
    cmds.xform(offset_group, centerPivots=True)
   
    return switch_control, offset_group
    
def add_switch_attributes(switch_control, joint_list, FK_root_offset_group, IK_offset_group, pole_vector_offset_group, IK_elbow_VIZ, selected_side):
   
    # Use the root joint to find which appendage it is
    root_joint = joint_list[0]
   
    # Find which finger it is based on the first non-zero number in the name
    # If it is the shoulder, then we don't need to find the finger number
    appendage_name = ""
    if 'shoulder' in root_joint:
        appendage_name = 'Arm'
    else:
        appendage_name = get_finger_name(root_joint)
        print("finger_name = ", appendage_name)
           
    # The name of the FK/IK switch attribute is the finger name + '_IK' so you can toggle IK on/off for each finger
    attribute_name = appendage_name + '_IK'
                       
    # Add "Pointer IK" attribute to the switch control
    cmds.addAttr(switch_control, longName= attribute_name, attributeType="bool", defaultValue=0, keyable=True)
       
    # Create a Reverse node to toggle on and off
    reverse_node = cmds.shadingNode('reverse', asUtility=True, name= appendage_name + 'FK_IK_switch_node')
               
    # Connect FK/IK attribute to visibility for the IK controls
    print("FK_root_offset_group ", FK_root_offset_group)
    cmds.connectAttr(switch_control + '.' + attribute_name, reverse_node + '.inputX')
    cmds.connectAttr(reverse_node + '.outputX', FK_root_offset_group + '.visibility', force = True)
    cmds.connectAttr(switch_control + '.' + attribute_name, IK_offset_group + '.visibility', force = True)
    cmds.connectAttr(switch_control + '.' + attribute_name, pole_vector_offset_group + '.visibility', force = True)
    cmds.connectAttr(switch_control + '.' + attribute_name, IK_elbow_VIZ + '.visibility', force = True)
    cmds.connectAttr(switch_control + '.Arm_IK', 'IK_shoulder_CTRL_%s.visibility' % selected_side, force = True)
   
   
    #if appendage_name == 'Arm':
    for child_joint in joint_list:
        # Connect FK/IK attribute to the parent constraints between TRG, IK, and FK
        parent_constraint = child_joint + '_parentConstraint1.'
        cmds.connectAttr(switch_control + '.' + attribute_name, parent_constraint + child_joint.replace('TRG', 'IK') + 'W0', force = True)
        cmds.connectAttr(reverse_node + '.outputX', parent_constraint + child_joint.replace('TRG', 'FK') + 'W1', force = True)
        
    # Create a Reverse node to toggle on and off
    reverse_node = cmds.shadingNode('reverse', asUtility=True, name= 'Wrist_to_Switch_Constraint_FK_IK_switch_node')
    cmds.connectAttr(switch_control + '.' + 'Arm_IK', reverse_node + '.inputX')
    #parent_constraint = switch_control + '_parentConstraint1.'
    cmds.connectAttr(switch_control + '.' + 'Arm_IK', 'SWITCH_ARM_CTRL_%s_parentConstraint1.IK_wrist_CTRL_%sW1' % (selected_side, selected_side), force = True)
    cmds.connectAttr(switch_control + '.' + 'Arm_IK', 'IK_shoulder_JNT_%s_parentConstraint1.IK_shoulder_CTRL_%sW0' % (selected_side, selected_side), force = True)
    cmds.connectAttr(reverse_node + '.outputX', 'SWITCH_ARM_CTRL_%s_parentConstraint1.FK_wrist_CTRL_%sW0' % (selected_side, selected_side), force = True)
       
def constrain_wrist_to_items(group_name, selected_side):
    # Get all the items within the group
    #items = cmds.listRelatives(group_name, children=True, fullPath=True) or []
   
    # Find the wrist control in the outliner
    substring = 'TRG_wrist_JNT_%s' % selected_side
    wrist_joint = None
    wrist_joint = cmds.ls('*%s*' % substring, type='transform')[0]
    print("wrist_joint = ", wrist_joint)

   
    # If the wrist joint is found, apply a parent constraint
    cmds.parentConstraint(wrist_joint, group_name, maintainOffset=True)
   
    # Find the wrist control in the outliner
    substring = 'IK_wrist_CTRL_%s' % selected_side
    wrist_control = None
    wrist_control = cmds.ls('*%s*' % substring, type='transform')[0]
    print("wrist_control = ", wrist_control)
    #cmds.parentConstraint(wrist_control, wrist_joint, maintainOffset=True)
   
def set_rotate_order_recursive(node, rotate_order):
    cmds.setAttr(node + '.rotateOrder', rotate_order)
   
    children = cmds.listRelatives(node, children=True, type='transform') or []
    for child in children:
        set_rotate_order_recursive(child, rotate_order)
def create_roll_joints(selected_side):
    # Duplicate bind shoulder joint, delete children, and rename
    bind_shoulder_joint = 'BIND_shoulder_JNT_%s' % selected_side
    roll_shoulder_joint = cmds.duplicate(bind_shoulder_joint, rr=True)[0]
    children = cmds.listRelatives(roll_shoulder_joint, c=True, f=True)
    if children:
        cmds.delete(children)
    cmds.rename(roll_shoulder_joint, 'ROLL_shoulder_JNT_%s' % selected_side)
    cmds.setAttr('ROLL_shoulder_JNT_%s.radius' % selected_side, cmds.getAttr('ROLL_shoulder_JNT_%s.radius' % selected_side) + 1)
   
    # Duplicate roll shoulder joint and rename
    roll_shoulder_joint = 'ROLL_shoulder_JNT_%s' % selected_side
    roll_bicep_joint = cmds.duplicate(roll_shoulder_joint, rr=True)[0]
    cmds.rename(roll_bicep_joint, 'ROLL_bicep_JNT_%s' % selected_side)
   
    # Create Parent Constraint between bind shoulder and bind elbow joints
    bind_elbow_joint = 'BIND_elbow_JNT_%s' % selected_side
    roll_bicep_joint = 'ROLL_bicep_JNT_%s' % selected_side
    parent_constraint = cmds.parentConstraint(bind_shoulder_joint, bind_elbow_joint, roll_bicep_joint, mo=False, sr=['x', 'y', 'z'])[0]
    cmds.delete(parent_constraint)
 
    # Parent bicep roll under the shoulder roll joint
    cmds.parent(roll_bicep_joint, roll_shoulder_joint)
   
    # Parent shoulder roll under the bind shoulder joint
    cmds.parent(roll_shoulder_joint, bind_shoulder_joint)
   
    # Create and configure locator
    aim_locator = cmds.spaceLocator(name='LOC_shoulder_roll_aim_%s' % selected_side)[0]
   
    # Create Parent Constraint between locator and bind shoulder joint
    parent_constraint = cmds.parentConstraint(bind_shoulder_joint, aim_locator, mo=False)[0]
    cmds.delete(parent_constraint)

    # Move the locator back 5 in the Z direction
    if selected_side == 'L':
        cmds.move(0, 0, -25, aim_locator, r=True, os=True)
    else:
        cmds.move(0, 0, 25, aim_locator, r=True, os=True)
   
    # Select the bind_elbow joint and shoulder_roll joint
    cmds.select(bind_elbow_joint, roll_shoulder_joint)
   
    # Create an Aim constraint
    aim_constraint = cmds.aimConstraint(mo = True, aim=[1, 0, 0], u=[0, 0, -1], wut='object', wuo=aim_locator)
   
    # Duplicate roll_shoulder_joint and move it back 5 in the Z direction
    follow_shoulder_joint = cmds.duplicate(roll_shoulder_joint, rr=True)[0]
    follow_shoulder_joint = cmds.rename(follow_shoulder_joint, 'FOLLOW_shoulder_JNT_%s' % selected_side)
    is_right = -1
    if selected_side == 'R':
        is_right = 1
    cmds.move(0, 0, (5 * is_right), follow_shoulder_joint, r=True, os=True)

    # Remove duplicated joint from the hierarchy
    cmds.parent(follow_shoulder_joint, w=True)
    follow_bicep_joint = cmds.listRelatives(follow_shoulder_joint, c=True, f=True)[0]
    follow_bicep_joint = cmds.rename(follow_bicep_joint, 'FOLLOW_bicep_JNT_%s' % selected_side)
   

    # Delete duplicate parent constraint
    constraints = cmds.ls(follow_shoulder_joint, type='aimConstraint', dag=True)
    if constraints:
        cmds.delete(constraints)
   

    # Parent the locator under the new follow_shoulder_joint
    cmds.parent(aim_locator, follow_shoulder_joint)
   
    # Create an IK handle (Rotate Plane Solver)
    ik_handle, end_effector = cmds.ikHandle(sj=follow_shoulder_joint, ee=follow_bicep_joint, sol='ikRPsolver', n = 'FOLLOW_shoulder_ikHandle_%s' % selected_side)
    cmds.rename(end_effector, 'FOLLOW_shoulder_effector_%s' % selected_side)
    
   
    # Parent the IK handle under the bind_elbow_joint
    cmds.parent(ik_handle, bind_elbow_joint)

    # Snap the end of the handle to the BIND_elbow_joint (Hold down V)
    elbow_joint_position = cmds.xform(bind_elbow_joint, q=True, ws=True, t=True)
    cmds.xform(ik_handle, ws=True, t=elbow_joint_position)
   
    # Set the pole vector attributes of the IK handle to [0, 0, 0]
    cmds.setAttr(ik_handle + '.poleVectorX', 0)
    cmds.setAttr(ik_handle + '.poleVectorY', 0)
    cmds.setAttr(ik_handle + '.poleVectorZ', 0)
   
    # Create multiplyDivide node and set its attributes
    multiply_divide_node = cmds.createNode('multiplyDivide', name='arm_roll_multi_%s' % selected_side)
    cmds.setAttr(multiply_divide_node + '.input2X', -0.5)
   
    # Connect bind_elbow_joint.rotateY to multiplyDivide.input1X
    cmds.connectAttr(roll_shoulder_joint + '.rotateX', multiply_divide_node + '.input1X')
   
    # Connect multiplyDivide.outputX to bicep_roll_joint.rotateY
    cmds.connectAttr(multiply_divide_node + '.outputX', roll_bicep_joint + '.rotateX')

    # Set rotate order for the specified joints and their hierarchies
    rotate_order = 1 #YZX
    set_rotate_order_recursive(roll_shoulder_joint, rotate_order)
    set_rotate_order_recursive(bind_shoulder_joint, rotate_order)
   
    # Duplicate the bind_elbow_joint and delete its children
    roll_elbow_joint = cmds.duplicate(bind_elbow_joint, rr=True)[0]
    children = cmds.listRelatives(roll_elbow_joint, c=True, f=True)
    if children:
        cmds.delete(children)
    roll_elbow_joint = cmds.rename(roll_elbow_joint, 'ROLL_elbow_JNT_%s' % selected_side)
   
    # Duplicate roll_elbow_joint to create roll_wrist_joint
    roll_wrist_joint = cmds.duplicate(roll_elbow_joint, rr=True)[0]
    roll_wrist_joint = cmds.rename(roll_wrist_joint, 'ROLL_wrist_JNT_%s' % selected_side)
    cmds.setAttr(roll_wrist_joint + '.radius', cmds.getAttr(roll_elbow_joint + '.radius') + 1)
    cmds.setAttr(roll_wrist_joint + '.radius', cmds.getAttr(roll_wrist_joint + '.radius') + 1)
   
    # Create parent constraint to match roll_wrist_joint's position to bind_wrist_joint and delete it
    bind_wrist_joint = 'BIND_wrist_JNT_%s' % selected_side
    parent_constraint = cmds.parentConstraint(bind_wrist_joint, roll_wrist_joint, mo=False)[0]
    cmds.delete(parent_constraint)

    # Create parent constraint between bind_wrist_joint, bind_elbow_joint, and roll_elbow_joint
    parent_constraint = cmds.parentConstraint(bind_wrist_joint, bind_elbow_joint, roll_elbow_joint, mo=False, sr=['x', 'y', 'z'])
    cmds.delete(parent_constraint)
   
    # Parent roll_wrist_joint and roll_elbow_joint under bind_elbow_joint
    cmds.parent(roll_wrist_joint, roll_elbow_joint, bind_elbow_joint)
   
    # Duplicate old locator and rename it to l_wrist_roll_aim
    wrist_locator = cmds.duplicate(aim_locator, name='LOC_wrist_roll_aim_%s' % selected_side)[0]
   
    # Create parent constraint between roll_wrist_joint and wrist locator and delete it
    wrist_pc = cmds.parentConstraint(roll_wrist_joint, wrist_locator, mo=False)[0]
    cmds.delete(wrist_pc)
   
    # Move the wrist locator back in the Z direction by 5
    if selected_side == 'L':
        cmds.move(0, 0, -5, wrist_locator, r=True, os=True)
    else:
        cmds.move(0, 0, 5, wrist_locator, r=True, os=True)
   
    # Parent wrist locator under bind_wrist_joint
    cmds.parent(wrist_locator, bind_wrist_joint)
   
    # Create an Aim constraint between bind_elbow_joint and roll_wrist_joint
    aim_constraint = cmds.aimConstraint(bind_elbow_joint, roll_wrist_joint, aim=[-1, 0, 0], u=[0, 0, -1], wut='object', wuo=wrist_locator)
   
    # Connect roll_wrist_joint.rotateX to multiplyDivide.input1X
    cmds.connectAttr(roll_wrist_joint + '.rotateX', multiply_divide_node + '.input1Y')
   
    # Connect multiplyDivide.outputX to roll_elbow_joint.rotateX
    cmds.connectAttr(multiply_divide_node + '.outputY', roll_elbow_joint + '.rotateX')
   
    # Change Input2Y on the multi node to 0.5
    cmds.setAttr(multiply_divide_node + '.input2Y', 0.5)
   
    # Create a parent constraint with maintain offset ON
    bind_rib_joint = 'BIND_ribs_JNT'
    cmds.parentConstraint(bind_rib_joint, follow_shoulder_joint, mo=True)
   
    return follow_shoulder_joint
   
def create_clavicle_control(selected_side):
   
    BLUE_1 = [0.264, 0.623, 1]
    BLUE_2 = [0.053, 0.352, 1]
    RED_1 = [1.0, 0.399, 0.325]
    RED_2 = [1.0, 0.132, 0.084]
    color_1 = RED_1
    color_2 = RED_2
    if selected_side == 'L':
        color_1 = BLUE_1
        color_2 = BLUE_2
   
    # Get the clavicle joint's name (you need to replace this with the actual joint name)
    clavicle_joint = "TRG_clavicle_JNT_%s" % selected_side

    # Create a circle curve
    circle = cmds.circle(normal=[1, 0, 0])[0]
   
    cmds.select(circle)
    cmds.rotate(0,0,90)
    cmds.scale(2.5,5,5)
   

   
    # Rename the control
    control_name = 'FK_clavicle_CTRL_%s' % selected_side
    clavicle_control = cmds.rename(circle, control_name)
   
    set_color(clavicle_control, color_1, color_2)
   
    # Create an offset group for the control
    clavicle_control_offset_group_name = control_name + "_offset"
    clavicle_control_offset_group = cmds.group(empty=True, name=clavicle_control_offset_group_name)
       
    # Parent the control under the offset group
    cmds.parent(clavicle_control, clavicle_control_offset_group)
       
    # Match pivot of the offset group to the pivot of the control
    cmds.matchTransform(clavicle_control_offset_group, clavicle_control, pivots=True)
       
    # Get the position of the joint
    joint_position = cmds.xform(clavicle_joint, query=True, translation=True, worldSpace=True)
       
    # Set the position of the offset_group to match the joint
    cmds.xform(clavicle_control_offset_group, translation=joint_position, worldSpace=True)
       
    # Get the orientation of the joint
    joint_orientation = cmds.xform(clavicle_joint, query=True, rotation=True, worldSpace=True)
       
    # Set the orientation of the offset_group to match the joint
    cmds.xform(clavicle_control_offset_group, rotation=joint_orientation, worldSpace=True)

    cmds.select(clavicle_control)
    cmds.scale(0.5, 1, 1)  
       
    # Freeze the transforms of the control and offset group
    cmds.makeIdentity(control_name, apply=True, translate=True, rotate=True, scale=True)
    cmds.makeIdentity(clavicle_control_offset_group, apply=True, translate=True, rotate=False, scale=True)
   


    # Parent constraint the shoulder pad control to the clavicle joint
    parent_constraint = cmds.parentConstraint(clavicle_control, clavicle_joint, mo=False)

    # Parent constraint the roll locator to the clavicle control
    parent_constraint = cmds.parentConstraint(clavicle_control,'LOC_shoulder_roll_aim_%s' % selected_side, mo=True)

    return clavicle_control_offset_group

def constrain_switch_to_wrist(switch_control, selected_side):
    cmds.parentConstraint('FK_wrist_CTRL_%s' % selected_side, switch_control, mo=True)
    cmds.parentConstraint('IK_wrist_CTRL_%s' % selected_side, switch_control, mo=True)
   
def create_offset_group(control):
    # Create an empty group (offset group) under the control
    offset_group = cmds.group(em=True, name=control + '_offset')

    # Match the offset group's transformation to the control
    cmds.matchTransform(offset_group, control, position=True, rotation=True)

    # Parent the control under the offset group
    cmds.parent(control, offset_group)

    # Freeze transformations (except rotations) on the offset group
    cmds.makeIdentity(offset_group, apply=True, t=True, r=False, s=False)

    # Center the pivot of the offset group
    cmds.xform(offset_group, cp=True) 
    
def create_IK_shoulder_control(selected_side):
    # Create IK shoulder control
    # Define the names of the joint, control, and parent constraint
    joint_name = 'IK_shoulder_JNT_%s' % selected_side
    control_name = 'IK_wrist_CTRL_%s' % selected_side
    parent_constraint_name = 'IK_shoulder_JNT_%s_parentConstraint1' % selected_side  # Replace with the actual constraint name
                
    # Delete the parent constraint attached to the joint
    if cmds.objExists(parent_constraint_name):
        cmds.delete(parent_constraint_name)
                
    # Duplicate the control
    duplicated_control = cmds.duplicate(control_name, name='IK_shoulder_CTRL_%s' % selected_side)[0]
                
    # Match the duplicated control's transformation to the joint
    cmds.matchTransform(duplicated_control, joint_name, position=True, rotation=True)
                
    # Create an offset group for the duplicated control
    create_offset_group(duplicated_control)
                
    # Parent constrain the control to the joint
    cmds.parentConstraint(duplicated_control, joint_name, maintainOffset=True)
class AutoRigUI(object):
    def __init__(self):
        # Create a window
        self.window_name = "Auto Rig"
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        self.window = cmds.window(self.window_name, title="Auto Rig", widthHeight=(300, 150))
       
        # Create layout
        self.layout = cmds.columnLayout(adjustableColumn=True)
       
       
        #Instructions
        cmds.text(label="1) Select the shoulder joint and hit 'Create Arm Switch Control'", font="boldLabelFont", align="center")
        cmds.separator(height=10, style="none")
       
        self.button = cmds.button(label="Create Arm Switch Control", command=self.auto_rig)
       
        cmds.text(label="2) Shift Select the metacarpal joints and hit 'Create Finger Switch Controls'", font="boldLabelFont", align="center")
        cmds.separator(height=10, style="none")
       
        self.button = cmds.button(label="Create Finger Switch Controls", command=self.auto_rig)
       
        self.radio_layout = cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 100), (2, 100)])
        cmds.radioCollection()
        self.left_radio = cmds.radioButton(label="Left", select=True, onCommand=self.set_left)
        self.right_radio = cmds.radioButton(label="Right", onCommand=self.set_right)
       
        # Show window
        cmds.showWindow(self.window)
       
        # Default to left hand
        self.is_left_hand = True
   
    def set_left(self, *args):
        self.is_left_hand = True
   
    def set_right(self, *args):
        self.is_left_hand = False
   
    def auto_rig(self, *args):
        # Use self.is_left_hand to determine which hand to rig
        selected_side = "L" if self.is_left_hand else "R"        
       
        # Implement your auto-rigging logic here
        cmds.confirmDialog(title="Success", message="Auto rigging complete for {} hand!".format(selected_side), button=["OK"])
       
        # Get the selected metacarpal joints
        selection = cmds.ls(selection=True)
           
        if not selection:
            print("No joint selected.")
           
        BIND_root_joints = selection
        print("TRG root joints = ", BIND_root_joints)
        BIND_root_joint = BIND_root_joints[0]
       
       
        if 'shoulder' in BIND_root_joint:    
            # Create a main CTRLS group
            CTRLS_group = cmds.group(empty=True, name='GRP_arm_CTRLS_%s' % selected_side)
            FK_CTRLS_group = cmds.group(empty=True, name='FK_CTRLS_%s' % selected_side)
            IK_CTRLS_group = cmds.group(empty=True, name='IK_CTRLS_%s' % selected_side)
            SWITCH_CTRLS_group = cmds.group(empty=True, name='SWITCH_CTRLS_%s' % selected_side)
            print("ik ctrl = ", IK_CTRLS_group)
            cmds.parent(FK_CTRLS_group, IK_CTRLS_group, SWITCH_CTRLS_group, CTRLS_group)
           
            # Create a main JNTS group
            JNTS_group = cmds.group(empty=True, name='GRP_arm_JNTS_%s' % selected_side)
            FK_JNTS_group = cmds.group(empty=True, name='FK_JNTS_%s' % selected_side)
            print("fk jnts = ", FK_JNTS_group)
            IK_JNTS_group = cmds.group(empty=True, name='IK_JNTS_%s' % selected_side)
            TRG_JNTS_group = cmds.group(empty=True, name='TRG_JNTS_%s' % selected_side)
            FOLLOW_JNTS_group = cmds.group(empty=True, name = 'FOLLOW_JNTS_%s' % selected_side)
            cmds.parent(FK_JNTS_group, IK_JNTS_group, TRG_JNTS_group, FOLLOW_JNTS_group, JNTS_group)
       
            BIND_arm_list = [BIND_root_joint]
            children_chain = []
            BIND_children = get_children_chain(BIND_root_joint, children_chain)
            print(BIND_children)
            for joint_name in BIND_children:
                if 'elbow' in joint_name:
                    BIND_arm_list.append(joint_name)
                if 'wrist' in joint_name:
                    BIND_arm_list.append(joint_name)
                   
            FK_arm_list = [name.replace('BIND', 'FK') for name in BIND_arm_list]
            IK_arm_list = [name.replace('BIND', 'IK') for name in BIND_arm_list]
            TRG_arm_list = [name.replace('BIND', 'TRG') for name in BIND_arm_list]
            print(BIND_arm_list)
            print(FK_arm_list)
            print(IK_arm_list)
           
            # Create a switch control that will hold all the IK/FK toggles for each finger
            switch_control, switch_offset_group = create_switch_control(selected_side)
           
            # Parent the switch control offset group under the switch control group
            cmds.parent(switch_offset_group, SWITCH_CTRLS_group)
           
            # Get the parent of the selected joint
            BIND_clavicle = cmds.listRelatives(BIND_root_joint, parent=True, type="joint")[0]
           
            # Create TRG skeleton
            TRG_root_joint = create_new_skeleton(BIND_clavicle, 'TRG', selected_side)
           
            # Parent constraint TRG to BIND
            parent_constraint_corresponding_joints()
           
            # Create FK skeleton
            FK_root_joint = create_new_skeleton(BIND_clavicle, 'FK', selected_side)
               
            # Create IK skeleton
            IK_root_joint = create_new_skeleton(BIND_clavicle, 'IK', selected_side)
           
            # Parent the skeletons under their respective JNT groups and hide them
            cmds.parent(FK_root_joint, FK_JNTS_group)
            cmds.parent(IK_root_joint, IK_JNTS_group)
            cmds.parent(TRG_root_joint, TRG_JNTS_group)
            cmds.hide(FK_JNTS_group, IK_JNTS_group, TRG_JNTS_group)
           
            # Have TRG blend between IK and FK skeletons
            blend_between_skeletons(TRG_root_joint)
               
            # Create FK Controls
            FK_root_control_offset, _ = create_FK_chain(FK_arm_list, selected_side)
           
            # Create IK Controls
            IK_control_offset, pole_vector_offset, IK_elbow_VIZ = create_IK_handle(IK_arm_list, selected_side)
            
            # Constraint switch to wrist controls
            constrain_switch_to_wrist(switch_control, selected_side)
            
            # Create IK shoulder control
            create_IK_shoulder_control(selected_side)
           
            # Add attribute to the switch control to toggle IK/FK for the arm
            add_switch_attributes(switch_control, TRG_arm_list, FK_root_control_offset, IK_control_offset, pole_vector_offset, IK_elbow_VIZ, selected_side)
           
            # Create FK arm group
            FK_arm_group = cmds.group(empty=True, name='GRP_FK_arm_CTRLS_%s' % selected_side)
   
            # Parent the objects under the group
            cmds.parent(FK_root_control_offset, FK_arm_group)
               
            # Create IK arm group
            IK_arm_group = cmds.group(empty=True, name='GRP_IK_arm_CTRLS_%s' % selected_side)
   
            # Parent the objects under the group
            cmds.parent(IK_control_offset, IK_arm_group)
            cmds.parent(pole_vector_offset, IK_arm_group)
            cmds.parent(IK_elbow_VIZ, IK_arm_group)
           
            # Parent the FK arm and IK arm group under their respective main groups
            cmds.parent(FK_arm_group, FK_CTRLS_group)
            cmds.parent(IK_arm_group, IK_CTRLS_group)
            # Set up twist joints
            follow_shoulder_joint = create_roll_joints(selected_side)    
            cmds.parent(follow_shoulder_joint, FOLLOW_JNTS_group)
             
            # Create a clavicle control
            clavicle_control = create_clavicle_control(selected_side)   
            cmds.parent(clavicle_control, FK_arm_group)
            
            # Parent constrain the shoulder control to the clavicle control
            cmds.parentConstraint('FK_clavicle_CTRL_%s' % selected_side, 'FK_shoulder_CTRL_%s_offset' % selected_side, mo = True) 
            
            # Parent constrain the IK shoulder offset group to the clavicle control
            cmds.parentConstraint('FK_clavicle_CTRL_%s' % selected_side, 'IK_shoulder_CTRL_%s_offset' % selected_side, mo = True)
            
            # Parent constraint the entire rig to the ribs joint
            cmds.parentConstraint('BIND_ribs_JNT', CTRLS_group, mo=True)
            
            # Create Side Rig group
            side_rig = cmds.group(empty=True, name='GRP_arm_RIG_%s' % selected_side)
            cmds.parent(CTRLS_group, side_rig)
            cmds.parent(JNTS_group, side_rig)
            
        else:
            # Create FK finger group
            FK_finger_group = cmds.group(empty=True, name='GRP_FK_finger_CTRLS_%s' % selected_side)
            IK_finger_group = cmds.group(empty=True, name='GRP_IK_finger_CTRLS_%s' % selected_side)
            switch_control = 'SWITCH_ARM_CTRL_%s' % selected_side
            for BIND_root_joint in BIND_root_joints:
               
                BIND_finger_list = [BIND_root_joint]
                children_chain = []
                BIND_children = get_children_chain(BIND_root_joint, children_chain)
                BIND_finger_list.extend(BIND_children)
                       
                FK_finger_list = [name.replace('BIND', 'FK') for name in BIND_finger_list]
                IK_finger_list = [name.replace('BIND', 'IK') for name in BIND_finger_list]
                TRG_finger_list = [name.replace('BIND', 'TRG') for name in BIND_finger_list]
               
                # Create FK Controls
                metacarpal, FK_root_control_offset = create_FK_chain(FK_finger_list[:-1], selected_side)
               
                # Create IK Controls (not including the metacarpal)
                IK_control_offset, pole_vector_offset, IK_knuckle_viz = create_IK_handle(IK_finger_list[1:], selected_side)
               
                # Add attribute to the switch control to toggle IK/FK for the arm
                add_switch_attributes(switch_control, TRG_finger_list, FK_root_control_offset, IK_control_offset, pole_vector_offset, IK_knuckle_viz, selected_side)
               
                # Parent the objects under the group
                cmds.parent(metacarpal, FK_finger_group)
                cmds.parent(IK_control_offset, IK_finger_group)
                cmds.parent(pole_vector_offset, IK_finger_group)
                cmds.parent(IK_knuckle_viz, IK_finger_group)
           
            # Connect finger controls to the wrist
            constrain_wrist_to_items(FK_finger_group, selected_side)
            constrain_wrist_to_items(IK_finger_group, selected_side)
           
            # Parent the finger groups under their respective main groups
            cmds.parent(FK_finger_group, 'FK_CTRLS_%s' % selected_side)
            cmds.parent(IK_finger_group, 'IK_CTRLS_%s' % selected_side)
           
            # Find the wrist control in the outliner
            substring = 'TRG_wrist_JNT_%s' % selected_side
            wrist_joint = None
            wrist_joint = cmds.ls('*%s*' % substring, type='transform')[0]
            print("wrist_joint = ", wrist_joint)
           
            # Create a reverse node
            reverse_node = cmds.shadingNode('reverse', asUtility=True)
           
            # Connect SWITCH_ARM_CTRL_L.Arm_IK to reverse1.inputX
            cmds.connectAttr('SWITCH_ARM_CTRL_%s.Arm_IK' % selected_side, reverse_node + '.inputX', force=True)
           
            # Connect reverse1.outputX to GRP_IK_finger_CTRLS_L_parentConstraint1.letty_TRG_wrist_JNT_LW0
            cmds.connectAttr(reverse_node + '.outputX', 'GRP_IK_finger_CTRLS_%s_parentConstraint1.%sW0' % (selected_side, wrist_joint), force=True)
            
            # Create Entire Rig group
            if not cmds.objExists('GRP_arms_RIG'):
                rig = cmds.group(empty=True, name='GRP_arms_RIG')
            if selected_side == 'L':
                cmds.parent('GRP_arm_RIG_L', 'GRP_arms_RIG')
            else:
                cmds.parent('GRP_arm_RIG_R', 'GRP_arms_RIG')
           
       
AutoRigUI()
