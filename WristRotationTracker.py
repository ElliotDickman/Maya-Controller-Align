### Joint rotation extractor - gets relative x rotation of wrist joint and assigns fractional rotation up the joint chain
### Wrist should be parented directly to elbow, at same level in hierarchy as the first forearm joint
### Select end (wrist), base (elbow), then each joint you want to apply rotation to (optional) and run script
### Select Verify Joints to only run script if selection contains only joints
### Select Apply Rotation to apply rotation to selected joints, select Enable Rotation Weighting to allow adjustable wiehgt falloff on joint rotation
### Created by Elliot Dickman - 2020 - Maya 2018

# Import the Maya commands library
from maya import cmds
import functools

def applyCallback(primAxis, applyRot, verifyJoints, enableRemap, *pArgs):
    
    primAxis = cmds.radioCollection(primAxis, query=True, select=True)
    applyRot = cmds.checkBox(applyRot, query=True, value=True)
    verifyJoints = cmds.checkBox(verifyJoints, query=True, value=True)
    enableRemap = cmds.checkBox(enableRemap, query=True, value=True)
    
    # Get selection
    sel = cmds.ls( orderedSelection=True )
    
    if len(sel) < 2:
        cmds.error("Must select at least two joints", noContext=True)
        return 1
    
    # Verify selection if enabled
    if verifyJoints:
        for j in sel:
            if cmds.objectType(j, isType='joint') == False:
                cmds.error("Selection must contain only joints", noContext=True)
                return 1
    
    wrist = sel[0]
    elbow = sel[1]
    
    wristLoc = wrist + "_loc"
    elbowLoc = elbow + "_loc"
    
    # Create locators
    cmds.spaceLocator(name=wristLoc)
    cmds.spaceLocator(name=elbowLoc)
    
    cmds.parent(wristLoc, wrist)
    cmds.parent(elbowLoc, elbow)
    
    cmds.xform([wristLoc, elbowLoc], translation=[0,0,0], rotation=[0,0,0])
    
    # Create matrix multiplication node
    multMatrixWrist = cmds.shadingNode('multMatrix', asUtility=True)
    
    # Multiply wrist matrix by elbow inverse matrix
    cmds.connectAttr(wristLoc+".worldMatrix[0]", multMatrixWrist+".matrixIn[0]", force=True) 
    cmds.connectAttr(elbowLoc+".worldInverseMatrix[0]", multMatrixWrist+".matrixIn[1]", force=True) 
    
    # Matrix sum to decompose
    decompMatrix = cmds.shadingNode('decomposeMatrix', asUtility=True)
    
    cmds.connectAttr(multMatrixWrist+".matrixSum", decompMatrix+".inputMatrix", force=True)
    
    # Quaternion rotation to Euler angle
    convertQuat = cmds.shadingNode('quatToEuler', asUtility=True)
    
    if primAxis == 'jointExtractX':
        cmds.connectAttr(decompMatrix+".outputQuatX", convertQuat+".inputQuatX", force=True)
    elif primAxis == 'jointExtractY':
        cmds.connectAttr(decompMatrix+".outputQuatY", convertQuat+".inputQuatY", force=True)
    elif primAxis == 'jointExtractZ':
        cmds.connectAttr(decompMatrix+".outputQuatZ", convertQuat+".inputQuatZ", force=True)    
    cmds.connectAttr(decompMatrix+".outputQuatW", convertQuat+".inputQuatW", force=True)
    
    ### Assign fractional rotation up the joint chain
    
    if(applyRot):
        # Get joints in hierarchy between elbow and wrist
        
        armJoints = sel[2:]
        
        numJoints = len(armJoints)+1
        
        # Get frational rotation
        divNode = cmds.shadingNode('multiplyDivide', asUtility=True)
        cmds.setAttr(divNode+".operation", 2)
        
        ### Set up multiple-output remap nodes
        if(enableRemap):
            remapMaster = cmds.shadingNode('remapValue', name="rotationFalloffControl", asUtility=True)
            cmds.setAttr(remapMaster+".inputMax", len(armJoints)-1)
            cmds.setAttr(remapMaster+".outputMax", 2)
            
            cmds.setAttr(remapMaster+".value[0].value_Position", 0)
            cmds.setAttr(remapMaster+".value[0].value_FloatValue", 0.5)
            cmds.setAttr(remapMaster+".value[1].value_Position", 1)
            cmds.setAttr(remapMaster+".value[1].value_FloatValue", 0.5)
            cmds.setAttr(remapMaster+".value[0].value_Interp", 1)
            cmds.setAttr(remapMaster+".value[1].value_Interp", 1)
            
            jointsRemapDict = {}
            remapMultDict = {}
            
            # Create remaps for each output position
            for i in range(len(armJoints)):
                jointsRemapDict[i] = cmds.shadingNode('remapValue', asUtility=True)
                
                cmds.connectAttr(remapMaster+".outputMax", jointsRemapDict[i]+".outputMax", force=True)
                cmds.connectAttr(remapMaster+".inputMax", jointsRemapDict[i]+".inputMax", force=True)
                cmds.setAttr(jointsRemapDict[i]+".inputValue", i)
                
                cmds.connectAttr(remapMaster+".value[0]", jointsRemapDict[i]+".value[0]", force=True)
                cmds.connectAttr(remapMaster+".value[1]", jointsRemapDict[i]+".value[1]", force=True)
                
                remapMultDict[i] = cmds.shadingNode('multiplyDivide', asUtility=True)
                cmds.connectAttr(jointsRemapDict[i]+".outValue", remapMultDict[i]+".input1X", force=True)
            
        
        ### Check primary axis and apply rotation
        
        if primAxis == "jointExtractX":
            cmds.connectAttr(convertQuat+".outputRotateX", divNode+".input1X", force=True)
            cmds.setAttr(divNode+".input2X", numJoints)
            
            # Assign rotation to joints
            for j in range(len(armJoints)):
                if(enableRemap):
                    cmds.connectAttr(divNode+".outputX", remapMultDict[j]+".input2X", force=True)
                    cmds.connectAttr(remapMultDict[j]+".outputX", armJoints[j]+".rotateX")
                else:
                    cmds.connectAttr(divNode+".outputX", armJoints[j]+".rotateX")
        
        if primAxis == "jointExtractY":
            cmds.connectAttr(convertQuat+".outputRotateY", divNode+".input1Y", force=True)
            cmds.setAttr(divNode+".input2Y", numJoints)
            
            # Assign rotation to joints
            for j in range(len(armJoints)):
                if(enableRemap):
                    cmds.connectAttr(divNode+".outputY", remapMultDict[j]+".input2X", force=True)
                    cmds.connectAttr(remapMultDict[j]+".outputX", armJoints[j]+".rotateY")
                else:
                    cmds.connectAttr(divNode+".outputY", armJoints[j]+".rotateY")
                
        if primAxis == "jointExtractZ":
            cmds.connectAttr(convertQuat+".outputRotateZ", divNode+".input1Z", force=True)
            cmds.setAttr(divNode+".input2Z", numJoints)
            
            # Assign rotation to joints
            for j in range(len(armJoints)):
                if(enableRemap):
                    cmds.connectAttr(divNode+".outputZ", remapMultDict[j]+".input2X", force=True)
                    cmds.connectAttr(remapMultDict[j]+".outputX", armJoints[j]+".rotateZ")
                else:
                    cmds.connectAttr(divNode+".outputZ", armJoints[j]+".rotateZ")
    
        if(enableRemap):
            cmds.select(remapMaster)
                
    # Message to console
    print "Extracted rotation from %s to %s" % (elbow, wrist)
    if(applyRot):
        print "Applied rotation to: ",
        for j in range(len(armJoints) - 1):
            print "%s, " % (armJoints[j]),
        print "%s" % (armJoints[-1])
    else:
        if(enableRemap):
            print "WARNING: Remap nodes not generated when apply rotation is deselected."
        print "Rotation not applied. Access rotation in QuatToEuler node."
    
    if cmds.window("jointExtractWin", exists=True):
        cmds.deleteUI("jointExtractWin")


    
def cancelCallback(*pArgs):
    if cmds.window("jointExtractWin", exists=True):
        cmds.deleteUI("jointExtractWin")

def enableVerifyCallback(applyRot, verifyJoints, *pArgs):
    applyRot = cmds.checkBox(applyRot, query=True, value=True)
    cmds.checkBox(verifyJoints, edit=True, enable=applyRot)

### UI Window

if cmds.window("jointExtractWin", exists=True):
    cmds.deleteUI("jointExtractWin")

UIWindow = cmds.window("jointExtractWin", title="Extract Joint Rotation", sizeable=False, w=500, h=300 )
cmds.columnLayout( adj=True)
cmds.frameLayout( label='Primary axis' )
cmds.rowLayout(numberOfColumns=3)
collection1 = cmds.radioCollection()
aX = cmds.radioButton( 'jointExtractX', label='X' )
aY = cmds.radioButton( 'jointExtractY', label='Y' )
aZ = cmds.radioButton( 'jointExtractZ', label='Z' )
cmds.setParent( '..' )

cmds.rowLayout(numberOfColumns=1)
applyRot = cmds.checkBox( label='Apply rotation', v=True )
cmds.setParent( '..' )

cmds.rowLayout(numberOfColumns=1)
enableRemap = cmds.checkBox( label='Enable rotation weighting', v=True )
cmds.setParent( '..' )

cmds.rowLayout(numberOfColumns=1)
verifyJoints = cmds.checkBox( label='Verify joints', v=False )
cmds.setParent( '..' )

cmds.rowLayout(numberOfColumns=2)
cmds.button( label='Apply', command=functools.partial( applyCallback, collection1, applyRot, verifyJoints, enableRemap ) )
cmds.button( label='Cancel', command=cancelCallback)
cmds.setParent( '..' )

cmds.radioCollection( collection1, edit=True, select=aX )

cmds.showWindow(UIWindow)


