#Author-Patrick Rainsberry
#Description-Save and retrieve display conditions of the model



import adsk.core, adsk.fusion, traceback

from xml.etree import ElementTree
from xml.etree.ElementTree import SubElement

from os.path import expanduser
import os

# global event handlers referenced for the duration of the command
handlers = []

menu_panel = 'InspectPanel'
commandResources = './resources'

commandId = 'configSave'
commandName = 'Config Saver'
commandDescription = 'Manage Suppression of Parts'

CS_CmdId = 'CS_CmdId'
cmdIds = [CS_CmdId]

def commandDefinitionById(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandDefinition id is not specified')
        return None
    commandDefinitions_ = ui.commandDefinitions
    commandDefinition_ = commandDefinitions_.itemById(id)
    return commandDefinition_

def commandControlByIdForNav(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandControl id is not specified')
        return None
    toolbars_ = ui.toolbars
    toolbarNav_ = toolbars_.itemById('NavToolbar')
    toolbarControls_ = toolbarNav_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

def commandControlByIdForPanel(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandControl id is not specified')
        return None
    workspaces_ = ui.workspaces
    modelingWorkspace_ = workspaces_.itemById('FusionSolidEnvironment')
    toolbarPanels_ = modelingWorkspace_.toolbarPanels
    toolbarPanel_ = toolbarPanels_.item(0)
    toolbarControls_ = toolbarPanel_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

def destroyObject(uiObj, tobeDeleteObj):
    if uiObj and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            uiObj.messageBox('tobeDeleteObj is not a valid object')
                    
def writeXML(tree, newState, fileName, dims):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    ui = app.userInterface
    
    # Get XML Root node
    root = tree.getroot()
    
    # Create a new State in the file
    state = SubElement( root, 'state', name=newState )
      
    # Get All components in design
    allComponents = design.allComponents
    for comp in allComponents:
        
        # Get All features inside the component
        allFeatures = comp.features
        for feature in allFeatures:
            
            # Record feature suppression state
            if feature is not None:               
                if feature.timelineObject.isSuppressed:                               
                    # ui.messageBox(str(feature.name) + " Is Suppressed")
                    SubElement( state, 'feature', component=comp.name, name=feature.name, suppress = 'suppressed')
                else:
                    # ui.messageBox(str(feature.name) + " Is Unsuppressed")
                    SubElement( state, 'feature', component=comp.name, name=feature.name, suppress = 'unSuppressed')
    
    if dims:
        # Get All parameters in design
        allParams = design.allParameters
        for param in allParams:
            ui.messageBox(str(param.name) + "  " + str(param.value))
            # Record feature suppression state
            if param is not None:               
                SubElement( state, 'parameter', value=str(param.value), name=param.name)

    tree.write(fileName)

def openXML(tree, state):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    # ui = app.userInterface

    # Get XML Root node
    root = tree.getroot()

    # Get All components in design
    allComponents = design.allComponents
    for comp in allComponents:
        
        # Get All features inside the component
        allFeatures = comp.features
        for feature in allFeatures:
            
            # Find feature saved state and set value
            if feature is not None:
                test = root.find("state[@name='%s']/feature[@name='%s'][@component='%s']" % (state, feature.name, comp.name))
                if test is not None:
                    if test.get('suppress') == 'suppressed':
                        # ui.messageBox(str(feature.name) + " Is Suppressed")
                        feature.timelineObject.isSuppressed = True
                    else:
                        # ui.messageBox(str(feature.name) + " Is Unsuppressed")
                        feature.timelineObject.isSuppressed = False

    # Get All parameters in design
    allParams = design.allParameters
    for param in allParams:

        # Apply Saved dimension info
        if param is not None:                       
            test = root.find("state[@name='%s']/parameter[@name='%s']" % (state, feature.name))
            if test is not None:
                param.value = float(test.get('value'))

def getFileName():
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        doc = app.activeDocument
        
        home = expanduser("~")
        home += '/configSaver/'
        
        if not os.path.exists(home):
            os.makedirs(home)
        
        fileName = home  + doc.name[0:doc.name.rfind(' v')] + '.xml'
        if not os.path.isfile(fileName):
            new_file = open( fileName, 'w' )                        
            new_file.write( '<?xml version="1.0"?>' )
            new_file.write( "<configSaves /> ")
            new_file.close()
        
        return fileName
    
    except:
        if ui:
            ui.messageBox('File Creation failed:\n{}'
            .format(traceback.format_exc()))
def unsuppressAll():

    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)

    # Get All components in design
    allComponents = design.allComponents
    for comp in allComponents:
        
        # Get All features inside the component
        allFeatures = comp.features
        for feature in allFeatures:
            
            # Unsuppress feature
            if feature is not None:
                feature.timelineObject.isSuppressed = False

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        class DS_InputChangedHandler(adsk.core.InputChangedEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    if inputs.itemById('all').value:
                        inputs.itemById('currentState').isVisible = False
                        inputs.itemById('newName').isVisible = False
                        inputs.itemById('save').isVisible = False
                        inputs.itemById('dims').isVisible = False
                    
                    elif inputs.itemById('save').value:
                        inputs.itemById('currentState').isVisible = False
                        inputs.itemById('newName').isEnabled = True
                        inputs.itemById('dims').isEnabled = True
                    else:
                        inputs.itemById('currentState').isVisible = True
                        inputs.itemById('newName').isVisible = True
                        inputs.itemById('dims').isVisible = True
                        inputs.itemById('dims').isEnabled = False
                        inputs.itemById('newName').isEnabled = False
                        inputs.itemById('save').isVisible = True

                except:
                    if ui:
                        ui.messageBox('Input changed event failed: {}').format(traceback.format_exc())
        
        # Handle the input changed event.        
        class DS_executePreviewHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                app = adsk.core.Application.get()
                ui  = app.userInterface
                try:
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    state = inputs.itemById('currentState').selectedItem.name
                    
                    if inputs.itemById('all').value:
                        unsuppressAll()
                    
                    elif state != 'Current' and not inputs.itemById('save').value and not inputs.itemById('all').value:
                        fileName = getFileName()                    
                        tree = ElementTree.parse(fileName)
                        openXML(tree, state)
                    
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))                
        class DS_CreatedHandler(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    cmd = args.command
                    onExecute = DS_ExecuteHandler()
                    cmd.execute.add(onExecute)
                    onChange = DS_InputChangedHandler()
                    cmd.inputChanged.add(onChange)
                    onUpdate = DS_executePreviewHandler()
                    cmd.executePreview.add(onUpdate)
                    
                    # keep the handler referenced beyond this function
                    handlers.append(onExecute)  
                    handlers.append(onChange)
                    handlers.append(onUpdate)
                    
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    root = tree.getroot()
                    
                    inputs = cmd.commandInputs
                    
                    dropDown = inputs.addDropDownCommandInput('currentState', 'Select Saved Config:', adsk.core.DropDownStyles.TextListDropDownStyle)
                    dropDownItems = dropDown.listItems
                    
                    dropDownItems.add('Current', True)
                    
                    for state in root.findall('state'):
                        dropDownItems.add(state.get('name'), False,)
                        
                    inputs.addBoolValueInput('save', 'Save current suppression condition?', True)
                    inputs.addStringValueInput('newName', 'New Config Name:', 'New Config')        
                    inputs.addBoolValueInput('dims', 'Save DImension Information also?', True)
                    inputs.addBoolValueInput('all', 'Unsuppress all features?', True)
                    inputs.itemById('newName').isEnabled = False
                    inputs.itemById('newName').isVisible = False
                        
                except:
                    if ui:
                        ui.messageBox('Panel command created failed:\n{}'
                        .format(traceback.format_exc()))     

        class DS_ExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:  
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    state = inputs.itemById('currentState').selectedItem.name
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    
                    if inputs.itemById('all').value:
                        unsuppressAll()
                    elif inputs.itemById('save').value:
                        writeXML(tree, inputs.itemById('newName').value, fileName, inputs.itemById('dims').value)
                    else:
                        openXML(tree, state)  
                    
                    
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))   
                                              
        # Get the UserInterface object and the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        #global showAllBodiesCmdId
        #otherCmdDefs = [showAllCompsCmdId, showHiddenBodiesCmdId, showHiddenCompsCmdId]
        # add a command button on Quick Access Toolbar
        toolbars_ = ui.toolbars
        navBar = toolbars_.itemById('NavToolbar')
        toolbarControlsNAV = navBar.controls
        
        DS_Control = toolbarControlsNAV.itemById(CS_CmdId)
        if not DS_Control:
            DS_cmdDef = cmdDefs.itemById(CS_CmdId)
            if not DS_cmdDef:
                # commandDefinitionNAV = cmdDefs.addSplitButton(showAllBodiesCmdId, otherCmdDefs, True)
                DS_cmdDef = cmdDefs.addButtonDefinition(CS_CmdId, 'Config Saver', 'Save Suppresion State of Features',commandResources)
            onCommandCreated = DS_CreatedHandler()
            DS_cmdDef.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            DS_Control = toolbarControlsNAV.addCommand(DS_cmdDef)
            DS_Control.isVisible = True

        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        objArrayNav = []
        
        for cmdId in cmdIds:
            commandControlNav_ = commandControlByIdForNav(cmdId)
            if commandControlNav_:
                objArrayNav.append(commandControlNav_)
    
            commandDefinitionNav_ = commandDefinitionById(cmdId)
            if commandDefinitionNav_:
                objArrayNav.append(commandDefinitionNav_)
            
        for obj in objArrayNav:
            destroyObject(ui, obj)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
