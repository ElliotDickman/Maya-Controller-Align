### Select all controllers then all joints to align
### Created by Elliot Dickman - 2020 - Maya 2018

import maya.cmds as cmds

# Get selection
sel = cmds.ls( orderedSelection=True )
targetCtrl = []
targetJoint = []

for i in sel:
    if (cmds.objectType(i, isType="joint")):
        targetJoint.append(i)
    else:
        targetCtrl.append(i)

for j in range(len(targetJoint)):
    cmds.parent(targetCtrl[j], targetJoint[j])

    cmds.xform(targetCtrl[j], translation=[0,0,0], rotation=[0,0,0])

    cmds.parent(targetCtrl[j], world=True)

print "Aligned %s to %s\n" % (targetCtrl, targetJoint)
