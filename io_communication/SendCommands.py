import os

class SendCommands(object):
    def __init__(self, controller, filepath, *args, **kwargs):
        self.controller = controller
        self.filepath = filepath
        self.args = args
        self.kwargs = kwargs
        if not os.path.isfile(filepath):
            open(filepath, 'a').close()

    def moveStage(self, x, y, z):
        self.writeCommand('moveXYZ', x, y, z)

    def grabOneStack(self):
        self.writeCommand('grabOneStack')

    def setZoom(self, zoom):
        self.writeCommand('setZoom', zoom)

    def doUncaging(self, roi_x, roi_y):
        self.writeCommand('runUncaging', roi_x, roi_y)

    def getFOVsize(self):
        self.writeCommand('getFOV_xy')

    def getScanAngleXY(self):
        self.writeCommand('getScanAngleXY')

    def getScanAngleMultiplier(self):
        self.writeCommand('getScanAngleMultiplier')

    def getScanAngleRangeReference(self):
        self.writeCommand('getScanAngleRangeReference')

    def getCurrentPosition(self):
        self.writeCommand('getCurrentPosition', 'xyz')

    def setScanShift(self, scanShiftFast, scanShiftSlow):
        self.writeCommand('setScanAngleXY', scanShiftFast, scanShiftSlow)

    def setZSliceNum(self, z_slice_num):
        self.writeCommand('setZSliceNum', z_slice_num)

    def writeCommand(self, *args):
        command = ",".join([str(x) for x in args])
        self.controller.print_status('\nWriting Command {0}\n'.format(command))
        with open(self.filepath, "a") as f:
            f.write('\n' + command)
