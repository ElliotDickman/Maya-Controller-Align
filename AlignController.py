import maya.cmds as cmds

# Get selection
sel = cmds.ls( orderedSelection=True )
targetCtrl = sel[0]
targetJoint = sel[1]

cmds.parent(targetCtrl, targetJoint)

cmds.xform(targetCtrl, translation=[0,0,0], rotation=[0,0,0])

cmds.parent(targetCtrl, world=True)

print "Aligned %s to %s\n" % (targetCtrl, targetJoint)