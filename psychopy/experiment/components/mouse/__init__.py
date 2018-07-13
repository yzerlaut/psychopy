#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from os import path
from psychopy.experiment.components import BaseComponent, Param, _translate
import re

# the absolute path to the folder containing this path
thisFolder = path.abspath(path.dirname(__file__))
iconFile = path.join(thisFolder, 'mouse.png')
tooltip = _translate('Mouse: query mouse position and buttons')

# only use _localized values for label values, nothing functional:
_localized = {'saveMouseState': _translate('Save mouse state'),
              'forceEndRoutineOnPress': _translate('End Routine on press'),
              'timeRelativeTo': _translate('Time relative to'),
              'Clickable stimuli': _translate('Clickable stimuli'),
              'Store params for clicked': _translate('Store params for clicked'),
              'New clicks only': _translate('New clicks only')}


class MouseComponent(BaseComponent):
    """An event class for checking the mouse location and buttons
    at given timepoints
    """
    categories = ['Responses']
    targets = ['PsychoPy', 'PsychoJS']

    def __init__(self, exp, parentName, name='mouse',
                 startType='time (s)', startVal=0.0,
                 stopType='duration (s)', stopVal=1.0,
                 startEstim='', durationEstim='',
                 save='final', forceEndRoutineOnPress="any click",
                 timeRelativeTo='routine'):
        super(MouseComponent, self).__init__(
            exp, parentName, name=name,
            startType=startType, startVal=startVal,
            stopType=stopType, stopVal=stopVal,
            startEstim=startEstim, durationEstim=durationEstim)

        self.type = 'Mouse'
        self.url = "http://www.psychopy.org/builder/components/mouse.html"
        self.exp.requirePsychopyLibs(['event'])
        self.categories = ['Inputs']

        self.order += [
            'forceEndRoutineOnPress',
            'saveMouseState', 'timeRelativeTo',
            'newClicksOnly', 'clickable', 'saveParamsClickable']

        # params
        msg = _translate(
            "How often should the mouse state (x,y,buttons) be stored? "
            "On every video frame, every click or just at the end of the "
            "Routine?")
        self.params['saveMouseState'] = Param(
            save, valType='str',
            allowedVals=['final', 'on click', 'every frame', 'never'],
            hint=msg,
            label=_localized['saveMouseState'])

        msg = _translate("Should a button press force the end of the routine"
                         " (e.g end the trial)?")
        if forceEndRoutineOnPress is True:
            forceEndRoutineOnPress = 'any click'
        elif forceEndRoutineOnPress is False:
            forceEndRoutineOnPress = 'never'
        self.params['forceEndRoutineOnPress'] = Param(
            forceEndRoutineOnPress, valType='str',
            allowedVals=['never', 'any click', 'valid click'],
            updates='constant',
            hint=msg,
            label=_localized['forceEndRoutineOnPress'])

        msg = _translate("What should the values of mouse.time should be "
                         "relative to?")
        self.params['timeRelativeTo'] = Param(
            timeRelativeTo, valType='str',
            allowedVals=['experiment', 'routine'],
            updates='constant',
            hint=msg,
            label=_localized['timeRelativeTo'])


        msg = _translate('If the mouse button is already down when we start'
                         'checking then wait for it to be released before'
                         'recording as a new click.'
                         )
        self.params['newClicksOnly'] = Param(
            True, valType='bool',
            updates='constant',
            hint=msg,
            label=_localized['New clicks only'])
        msg = _translate('A comma-separated list of your stimulus names that '
                         'can be "clicked" by the participant. '
                         'e.g. target, foil'
                         )
        self.params['clickable'] = Param(
            '', valType='code',
            updates='constant',
            hint=msg,
            label=_localized['Clickable stimuli'])

        msg = _translate('The params (e.g. name, text), for which you want '
                         'to store the current value, for the stimulus that was'
                         '"clicked" by the mouse. Make sure that all the '
                         'clickable objects have all these params.'
                         )
        self.params['saveParamsClickable'] = Param(
            'name,', valType='code',
            updates='constant', allowedUpdates=[],
            hint=msg,
            label=_localized['Store params for clicked'])


    @property
    def _clickableParamsList(self):
        # convert clickableParams (str) to a list
        params = self.params['saveParamsClickable'].val
        paramsList = re.findall(r"[\w']+", params)
        return paramsList or ['name']

    def _writeClickableObjectsCode(self, buff):
        # code to check if clickable objects were clicked
        code = (
            "# check if the mouse was inside our 'clickable' objects\n"
            "for obj in [%(clickable)s]:\n"
            "    if obj.contains(%(name)s):\n"
            "        gotValidClick = True\n")
        buff.writeIndentedLines(code % self.params)

        buff.setIndentLevel(+2, relative=True)
        code = ''
        for paramName in self._clickableParamsList:
            code += "%s.clicked_%s.append(obj.%s)\n" %(self.params['name'],
                                                     paramName, paramName)
        buff.writeIndentedLines(code % self.params)
        buff.setIndentLevel(-2, relative=True)

    def _writeClickableObjectsCodeJS(self, buff):
        # code to check if clickable objects were clicked
        code = (
            "// check if the mouse was inside our 'clickable' objects\n"
            "for (const obj of [{clickable}])\n"
            "  if (obj.contains({name})) {{\n"
            "    console.log('INSIDE ' + obj.name);\n"
            "    {name}.clicked_name.push(obj.name);\n"
            "  }}\n"
            "}}\n")
        buff.writeIndentedLines(code.format(name=self.params['name'],
                                            clickable=self.params['clickable']))
        buff.setIndentLevel(-1, relative=True)
        buff.writeIndentedLines("}\n")


    def writeInitCode(self, buff):
        code = ("%(name)s = event.Mouse(win=win)\n"
                "x, y = [None, None]\n")
        buff.writeIndentedLines(code % self.params)

    def writeInitCodeJS(self, buff):
        code = ("%(name)s = new Mouse({\n"
        "  win: my.window,\n"
        "});\n")
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCode(self, buff):
        """Write the code that will be called at the start of the routine
        """
        # create some lists to store recorded values positions and events if
        # we need more than one
        code = ("# setup some python lists for storing info about the "
                "%(name)s\n")

        if self.params['saveMouseState'].val in ['every frame', 'on click']:
            code += ("%(name)s.x = []\n"
                     "%(name)s.y = []\n"
                     "%(name)s.leftButton = []\n"
                     "%(name)s.midButton = []\n"
                     "%(name)s.rightButton = []\n"
                     "%(name)s.time = []\n")
        if self.params['clickable'].val:
            for clickableObjParam in self._clickableParamsList:
                code += "%(name)s.clicked_{} = []\n".format(clickableObjParam)

        code += "gotValidClick = False  # until a click is received\n"
        buff.writeIndentedLines(code % self.params)

    def writeRoutineStartCodeJS(self, buff):
        """Write the code that will be called at the start of the routine"""
        code = ("// setup some python lists for storing info about the %(name)s\n")
        if self.params['saveMouseState'].val in ['every frame', 'on click']:
            code += ("// current position of the mouse:\n"
                     "%(name)s.x = [];\n"
                     "%(name)s.y = [];\n"
                     "%(name)s.leftButton = [];\n"
                     "%(name)s.midButton = [];\n"
                     "%(name)s.rightButton = [];\n"
                     "%(name)s.time = [];\n")

        if self.params['clickable'].val:
            for clickableObjParam in self._clickableParamsList:
                code += "my.%s.clicked_%s = [];\n" % (self.params['name'].val, clickableObjParam)
        code += "my.gotValidClick = false; // until a click is received\n"
        buff.writeIndentedLines(code % self.params)

    def writeFrameCode(self, buff):
        """Write the code that will be called every frame"""
        forceEnd = self.params['forceEndRoutineOnPress'].val
        routineClockName = self.exp.flow._currentRoutine._clockName

        # get a clock for timing
        if self.params['timeRelativeTo'].val == 'experiment':
            self.clockStr = 'globalClock'
        elif self.params['timeRelativeTo'].val == 'routine':
            self.clockStr = routineClockName

        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveMouseState'].val not in
                ['every frame', 'on click'] and forceEnd=='never'):
            return

        buff.writeIndented("# *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        self.writeStartTestCode(buff)
        code = "%(name)s.status = STARTED\n"

        if self.params['newClicksOnly']:
            code += (
                "prevButtonState = %(name)s.getPressed()"
                "  # if button is down already this ISN'T a new click\n")
        else:
            code += (
                "prevButtonState = [0, 0, 0]"
                "  # if now button is down we will treat as 'new' click\n")
        buff.writeIndentedLines(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCode(buff)
            buff.writeIndented("%(name)s.status = STOPPED\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # if STARTED and not STOPPED!
        code = ("if %(name)s.status == STARTED:  "
                "# only update if started and not stopped!\n") % self.params
        buff.writeIndented(code)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        # write param checking code
        if (self.params['saveMouseState'].val == 'on click'
            or forceEnd in ['any click', 'valid click']):
            code = ("buttons = %(name)s.getPressed()\n"
                    "if buttons != prevButtonState:  # button state changed?")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1
            buff.writeIndented("prevButtonState = buttons\n")
            code = ("if sum(buttons) > 0:  # state changed to a new click\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1

        elif self.params['saveMouseState'].val == 'every frame':
            code = "buttons = %(name)s.getPressed()\n" % self.params
            buff.writeIndented(code)

        # only do this if buttons were pressed
        if self.params['saveMouseState'].val in ['on click', 'every frame']:
            code = ("x, y = %(name)s.getPos()\n"
                    "%(name)s.x.append(x)\n"
                    "%(name)s.y.append(y)\n"
                    "%(name)s.leftButton.append(buttons[0])\n"
                    "%(name)s.midButton.append(buttons[1])\n"
                    "%(name)s.rightButton.append(buttons[2])\n"%
                    self.params)
            code += ("%s.time.append(%s.getTime())\n" %
                     (self.params['name'], self.clockStr))
            buff.writeIndentedLines(code)

        # also write code about clicked objects if needed.
        if self.params['clickable'].val:
            self._writeClickableObjectsCode(buff)

        # does the response end the trial?
        if forceEnd == 'any click':
            code = ("# abort routine on response\n"
                    "continueRoutine = False\n")
            buff.writeIndentedLines(code)

        elif forceEnd == 'valid click':
            code = ("if gotValidClick:  # abort routine on response\n"
                    "    continueRoutine = False\n")
            buff.writeIndentedLines(code)
        else:
            pass # forceEnd == 'never'
        # 'if' statement of the time test and button check
        buff.setIndentLevel(-dedentAtEnd, relative=True)

    def writeFrameCodeJS(self, buff):
        """Write the code that will be called every frame"""
        forceEnd = self.params['forceEndRoutineOnPress'].val

        # get a clock for timing
        if self.params['timeRelativeTo'].val == 'experiment':
            self.clockStr = 'globalClock'
        elif self.params['timeRelativeTo'].val == 'routine':
            self.clockStr = 'routineTimer'

        # only write code for cases where we are storing data as we go (each
        # frame or each click)

        # might not be saving clicks, but want it to force end of trial
        if (self.params['saveMouseState'].val not in
                ['every frame', 'on click'] and forceEnd == 'never'):
            return
        buff.writeIndented("// *%s* updates\n" % self.params['name'])

        # writes an if statement to determine whether to draw etc
        self.writeStartTestCodeJS(buff)
        code = "%(name)s.status = PsychoJS.Status.STARTED;\n"

        if self.params['newClicksOnly']:
            code += (
                "my.prevButtonState = %(name)s.getPressed();"
                "  // if button is down already this ISN'T a new click\n}")
        else:
            code += (
                "let prevButtonState = [0, 0, 0];"
                "  // if now button is down we will treat as 'new' click\n}")
        buff.writeIndentedLines(code % self.params)

        # to get out of the if statement
        buff.setIndentLevel(-1, relative=True)

        # test for stop (only if there was some setting for duration or stop)
        if self.params['stopVal'].val not in ['', None, -1, 'None']:
            # writes an if statement to determine whether to draw etc
            self.writeStopTestCodeJS(buff)
            buff.writeIndented("%(name)s.status = PsychoJS.Status.STOPPED;\n"
                               "  }\n" % self.params)
            # to get out of the if statement
            buff.setIndentLevel(-1, relative=True)

        # if STARTED and not STOPPED!
        code = ("if (%(name)s.status === PsychoJS.Status.STARTED) {  "
                "// only update if started and not stopped!\n")
        buff.writeIndented(code % self.params)
        buff.setIndentLevel(1, relative=True)  # to get out of if statement
        dedentAtEnd = 1  # keep track of how far to dedent later

        # write param checking code
        if (self.params['saveMouseState'].val == 'on click'
                or forceEnd in ['any click', 'valid click']):
            code = ("my.buttons = %(name)s.getPressed();\n"
                    "if (my.buttons != my.prevButtonState) { // button state changed?")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            code = "if (!my.buttons.every( (e,i,) => (e == my.prevButtonState[i]) )) { // button state changed?\n"
            buff.writeIndented(code)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1
            buff.writeIndented("my.prevButtonState = my.buttons;\n")
            code = ("if (my.buttons.reduce( (e, acc) => (e+acc) ) > 0) { // state changed to a new click\n")
            buff.writeIndentedLines(code % self.params)
            buff.setIndentLevel(1, relative=True)
            dedentAtEnd += 1

        elif self.params['saveMouseState'].val == 'every frame':
            code = "my.buttons = %(name)s.getPressed();\n" % self.params
            buff.writeIndented(code)

        # only do this if buttons were pressed
        if self.params['saveMouseState'].val in ['on click', 'every frame']:
            code = ("let xys = %(name)s.getPos();\n"
                    "%(name)s.x.push(xys[0]);\n"
                    "%(name)s.y.push(xys[1]);\n"
                    "%(name)s.leftButton.push(my.buttons[0]);\n"
                    "%(name)s.midButton.push(my.buttons[1]);\n"
                    "%(name)s.rightButton.push(my.buttons[2]);\n" %
                    self.params)
            code += ("%s.time.push(my.%s.getTime());\n" % (self.params['name'], self.clockStr))
            buff.writeIndentedLines(code)

            # also write code about clicked objects if needed.
        if self.params['clickable'].val:
            self._writeClickableObjectsCodeJS(buff)

        buff.writeIndented("}\n")
            # does the response end the trial?
        if forceEnd == 'any click':
            code = ("// abort routine on response\n"
                    "let continueRoutine = false;\n")
            buff.writeIndentedLines(code)

        elif forceEnd == 'valid click':
            code = ("if (my.gotValidClick === true) { // abort routine on response\n"
                    "  let continueRoutine = false;\n"
                    "}\n")
            buff.writeIndentedLines(code)
        else:
            pass  # forceEnd == 'never'
            # 'if' statement of the time test and button check
        buff.setIndentLevel(-dedentAtEnd, relative=True)
        buff.writeIndentedLines('}')

    def writeRoutineEndCode(self, buff):
        # some shortcuts
        name = self.params['name']
        # do this because the param itself is not a string!
        store = self.params['saveMouseState'].val
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type == 'StairHandler':
            code = ("# NB PsychoPy doesn't handle a 'correct answer' for "
                    "mouse events so doesn't know how to handle mouse with "
                    "StairHandler\n")
        else:
            code = ("# store data for %s (%s)\n" %
                    (currLoop.params['name'], currLoop.type))

        buff.writeIndentedLines(code)
            
        if store == 'final':  # for the o
            # buff.writeIndented("# get info about the %(name)s\n"
            # %(self.params))
            code = ("x, y = %(name)s.getPos()\n"
                    "buttons = %(name)s.getPressed()\n" %
                    self.params)
            code += ("%s.time = %s.getTime()\n" %
                     (self.params['name'], self.clockStr))
            # also write code about clicked objects if needed.
            if self.params['clickable'].val:
                buff.writeIndented("if sum(buttons):\n")
                buff.setIndentLevel(+1, relative=True)
                self._writeClickableObjectsCode(buff)
                buff.setIndentLevel(-1, relative=True)

            if currLoop.type != 'StairHandler':
                code += (
                    "{loopName}.addData('{mouseName}.x', x)\n" 
                    "{loopName}.addData('{mouseName}.y', y)\n" 
                    "{loopName}.addData('{mouseName}.leftButton', buttons[0])\n" 
                    "{loopName}.addData('{mouseName}.midButton', buttons[1])\n" 
                    "{loopName}.addData('{mouseName}.rightButton', buttons[2])\n"
                )

                # then add `trials.addData('mouse.clicked_name',.....)`
                if self.params['clickable'].val:
                    for paramName in self._clickableParamsList:
                        code += (
                            "if len({mouseName}.clicked_{param}):\n"
                            "    {loopName}.addData('{mouseName}.clicked_{param}', " 
                            "{mouseName}.clicked_{param}[0])\n"
                        )
                    buff.writeIndentedLines(
                        code.format(loopName=currLoop.params['name'],
                                    mouseName=name,
                                    param=paramName))

        elif store != 'never':
            # buff.writeIndented("# save %(name)s data\n" %(self.params))
            mouseDataProps = ['x', 'y', 'leftButton', 'midButton',
                             'rightButton', 'time']
            # possibly add clicked params if we have clickable objects
            if self.params['clickable'].val:
                for paramName in self._clickableParamsList:
                    mouseDataProps.append("clicked_{}".format(paramName))
            # use that set of properties to create set of addData commands
            for property in mouseDataProps:
                if store == 'every frame' or forceEnd == "never":
                    code = ("%s.addData('%s.%s', %s.%s)\n" %
                            (currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)
                else:
                    # we only had one click so don't return a list
                    code = ("if len(%s.%s): %s.addData('%s.%s', %s.%s[0])\n" %
                            (name, property,
                             currLoop.params['name'], name,
                             property, name, property))
                    buff.writeIndented(code)

        if currLoop.params['name'].val == self.exp._expHandler.name:
            buff.writeIndented("%s.nextEntry()\n" % self.exp._expHandler.name)

    def writeRoutineEndCodeJS(self, buff):
        """Write code at end of routine"""
        # some shortcuts
        name = self.params['name']
        # do this because the param itself is not a string!
        store = self.params['saveMouseState'].val
        if store == 'nothing':
            return

        forceEnd = self.params['forceEndRoutineOnPress'].val
        if len(self.exp.flow._loopList):
            currLoop = self.exp.flow._loopList[-1]  # last (outer-most) loop
        else:
            currLoop = self.exp._expHandler

        if currLoop.type == 'StairHandler':
            code = ("/*NB PsychoPy doesn't handle a 'correct answer' for "
                    "mouse events so doesn't know how to handle mouse with "
                    "StairHandler*/\n")
        else:
            code = ("// store data for %s (%s)\n" %
                    (currLoop.params['name'], currLoop.type))

        buff.writeIndentedLines(code)

        if store == 'final':  # for the o
            # buff.writeIndented("# get info about the %(name)s\n"
            # %(self.params))
            code = ("let xys = %(name)s.getPos();\n"
                    "my.buttons = %(name)s.getPressed();\n" %
                    self.params)
            code += ("%s.time = %s.getTime();\n" %
                     (self.params['name'], self.clockStr))
            # also write code about clicked objects if needed.
            if self.params['clickable'].val:
                buff.writeIndented("if (my.buttons.reduce((a, b) => a + b, 0) > 0) {\n")
                buff.setIndentLevel(+1, relative=True)
                self._writeClickableObjectsCode(buff)
                buff.setIndentLevel(-1, relative=True)

            if currLoop.type != 'StairHandler':
                code += (
                    "psychoJS.experiment.addData('{mouseName}.x', xys[0]);\n"
                    "psychoJS.experiment.addData('{mouseName}.y', xys[1]);\n"
                    "psychoJS.experiment.addData('{mouseName}.leftButton', buttons[0]);\n"
                    "psychoJS.experiment.addData('{mouseName}.midButton', buttons[1]);\n"
                    "psychoJS.experiment.addData('{mouseName}.rightButton', buttons[2]);\n"
                )

                # then add `trials.addData('mouse.clicked_name',.....)`
                if self.params['clickable'].val:
                    for paramName in self._clickableParamsList:
                        code += (
                            "if {mouseName}.clicked_{param})\n"
                            "  psychoJS.experiment.addData('{mouseName}.clicked_{param}', "
                            "psychoJS.experiment.clicked_{param}[0]);\n"
                        )
                    buff.writeIndentedLines(
                        code.format(loopName=currLoop.params['name'],
                                    mouseName=name,
                                    param=paramName))

        elif store != 'never':
            # buff.writeIndented("# save %(name)s data\n" %(self.params))
            mouseDataProps = ['x', 'y', 'leftButton', 'midButton',
                              'rightButton', 'time']
            # possibly add clicked params if we have clickable objects
            if self.params['clickable'].val:
                for paramName in self._clickableParamsList:
                    mouseDataProps.append("clicked_{}".format(paramName))
            # use that set of properties to create set of addData commands
            for property in mouseDataProps:
                if store == 'every frame' or forceEnd == "never":
                    code = ("psychoJS.experiment.addData('%s.%s', %s.%s);\n" %
                            (name, property, name, property))
                    buff.writeIndented(code)
                else:
                    # we only had one click so don't return a list
                    code = ("if (%s.%s) {"
                            "  psychoJS.experiment.addData('%s.%s', %s.%s[0])};\n"
                            % (name, property, name, property, name, property))
                    buff.writeIndented(code)
            buff.writeIndentedLines("\n")