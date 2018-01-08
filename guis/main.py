# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 14:36:57 2017

@author: smirnovm
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
from scipy import ndimage
from skimage import io, transform
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure
import matplotlib.animation as animation
from matplotlib import style
import matplotlib.gridspec as gridspec
from matplotlib import patches
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
import matplotlib.colorbar as colorbar
from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
import pickle
import os
import threading
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from queue import Queue
import cv2
from PIL import Image, ImageTk, ImageOps, ImageMath
import math
import inspect
import timeit

#Program running as simulation, without host imaging program
simulation = True
verbose = True

LARGE_FONT = ("Verdana", 12)
style.use("ggplot")
fig_dpi = 100
## figures
f_timeline = Figure(figsize = (5,2), dpi = fig_dpi)
f_timeline.set_tight_layout(True)
a_timeline = f_timeline.add_subplot(111)

f_positions = Figure(figsize = (3,3), dpi = fig_dpi)
#f_positions.subplots_adjust(left = .2, right = .8,  bottom = .2, top = .8)
f_positions.subplots_adjust(left = 0, right = 1,  bottom = 0, top = 1)
f_positions.set_tight_layout(True)


initDirectory = "../iniFiles/"

#create/refresh log file
log_file = open('log.txt','w')

def round_math(n, ndigits = 0):
    part = n * 10 ** ndigits
    delta = part - int(part)
    # always round "away from 0"
    if delta >= 0.5 or -0.5 < delta <= 0:
        part = math.ceil(part)
    else:
        part = math.floor(part)
    return part / (10 ** ndigits)

def fitFigToCanvas(fig, canv):
    h = canv.get_tk_widget().winfo_height()
    w = canv.get_tk_widget().winfo_width()
    fig.set_size_inches(w/fig_dpi,h/fig_dpi)

def floatOrNone(x):
    if x =="":
        y = None
    else:
        y = float(x)
    return y

def floatOrZero(x):
    if x =="":
        y = 0.0
    else:
        y = float(x)
    return y

def focusMeasure(image):
     # Gaussian derivative (Geusebroek2000)     
     Wsize = 15
     N = np.floor(Wsize/2)
     sig = N/2.5
     r = np.arange(-N.astype(int),N.astype(int)+1)
     x,y = np.meshgrid(r,r)
     G = np.exp(-(x**2+y**2)/(2*sig**2))/(2*np.pi*sig)
     Gx = -x*G/(sig**2)
     Gx = Gx/np.sum(Gx,1)
     Gy = -y*G/(sig**2)
     Gy = Gy/np.sum(Gy)
     Ry = ndimage.convolve(image.astype(float), Gx , mode = 'nearest')
     Rx = ndimage.convolve(image.astype(float), Gy , mode = 'nearest')
     FM = Rx**2+Ry**2
     FM = np.mean(FM)
     return FM
 
def remove_keymap_conflicts(new_keys_set):
    for prop in plt.rcParams:
        if prop.startswith('keymap.'):
            keys = plt.rcParams[prop]
            remove_list = set(keys) & new_keys_set
            for key in remove_list:
                keys.remove(key)
                
def printStatus(followingString):
    if verbose:
        # followingString is a string to add after the function. something like Started or Finished
        string = '\nFunction {0} {1}\n'.format(inspect.stack()[1][3],followingString)
        print(string)
        log_file.write(string)
        
        
#output is directional shift [x,y] in pixels. based on Sugar et al (2014) paper
def computeDrift(imgref,img):
    h,w = imgref.shape
    fft_ref = np.fft.fft2(imgref)  
    fft_img = np.fft.fft2(img)
    centery = h/2
    centerx = w/2
    prod = fft_ref * np.conj(fft_img)
    cc = np.fft.ifft2(prod)
    maxy,maxx = np.nonzero(np.fft.fftshift(cc) == np.max(cc))
    shifty = maxy - centery
    shiftx = maxx - centerx
    #Checks to see if there is an ambiguity problem with FFT because of the
    #periodic boundary in FFT (not sure why or if this is necessary but I'm
                               #keeping it around for now)
    if np.abs(shifty) > h/2:
        shifty = shifty-np.sign(shifty)*h
    if np.abs(shiftx) > h/2:
        shiftx = shiftx-np.sign(shiftx)*w
    
    return{'shiftx':shiftx[0],'shifty':shifty[0]}
    
def initializeInitDirectory():
    directory = os.path.dirname(initDirectory)
    try: 
        os.stat(directory)
    except:
        os.mkdir(directory)
        
           
class SpineTracker(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        
        tk.Tk.__init__(self, *args, **kwargs) #initialize regular Tk stuff
        
        #set properties for main window
        tk.Tk.iconbitmap(self,default = "../images/crabIco.ico") #icon doesn't work
        tk.Tk.wm_title(self, "SpineTracker")
        tk.Tk.geometry(self, newGeometry = '1000x600+200+200')
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        #define container for what's in the window
        container = ttk.Notebook(self)
        container.pack(side="top", fill = "both", expand = True)       
        initializeInitDirectory()
        self.initializeTimelineSteps()
        self.initializePositions()
        self.loadSettings()
        self.frames = {}
        self.windows = {}
        self.acq = {}
        self.measure = {}
        self.stepRunning = False
        self.instructions = []
        self.instructions_in_queue = Queue()
        self.timerStepsQueue = Queue()
        self.outputFile = "../instructions_output.txt"
        self.inputFile = "../instructions_input.txt"
        self.sendCommands = sendCommandsClass(self, self.outputFile)
        self.getCommands = getCommandsClass(self, self.inputFile)
        self.listenToInstructionsFile()
        #define frames (windows) available which will appear in main window
        for F in (StartPage, DriftPage, PositionsPage, TimelinePage):
            frame = F(container, self)
            self.frames[F] = frame
            container.add(frame, text = F.name)
            
    def showMacroViewWindow(self):
        self.windows[MacroWindow] = MacroWindow(self)
            
    def on_exit(self):
        print('quitting')
        try:
            self.ins_thread.stop()
            print('Instruction listener closed')
        except:
            pass
        log_file.close()
        self.destroy()
        print('goodbye')

    def listenToInstructionsFile(self):
        path, filename = os.path.split(self.inputFile)
        with self.instructions_in_queue.mutex:
            self.instructions_in_queue.queue.clear()
        self.ins_thread = instructionThread(self, path, filename, self.getCommands.readNewInstructions)
        
        
    def initializePositions(self):
        try:
            self.positions = pickle.load(open(initDirectory+'positions.p','rb'))
        except:
            self.positions = {}       
            
    def initializeTimelineSteps(self):
        try:
            self.timelineSteps = pickle.load(open(initDirectory+'timelineSteps.p','rb'))
        except:
            self.timelineSteps = []
        
    def loadSettings(self):
        self.settings = {}
        with open('../iniFiles/settings.txt') as input_file:
            for line in input_file:
                key, sep, val = [x.strip() for x in line.split()]
                try:
                    val = eval(val)
                except:
                    pass
                self.settings[key] = val  
 
        #measure autofocus of image
    def loadTestImage(self,cont): #for testing purposes only
        image = io.imread("../testing/test_image.tif")
        image = image[np.arange(0,len(image),2)]
        self.acq['imageStack'] = image
        self.createFigureForAFImages()
#        return(image)
        
    def loadAcquiredImage(self):
        startTime = timeit.timeit()
        image = io.imread(self.imageFilePath)
        totalChan = int(self.frames[DriftPage].totalChannelsVar.get())
        driftChan = int(self.frames[DriftPage].driftCorrectionChannelVar.get())
        image = image[np.arange(driftChan -1,len(image),totalChan)]
        self.acq['imageStack'] = image
        endTime = timeit.timeit()
        elapsedTime = endTime - startTime
        printStatus('Done after {0}s'.format(elapsedTime))
        self.createFigureForAFImages()
    
    def loadTestRefImage(self,cont): #for testing purposes only
        imgref = io.imread("../testing/test_refimg.tif")
#        self.acq['imgref'] = imgref
        self.acq['imgref_imaging'] = imgref
        self.acq['imgref_ref'] = imgref
#        return(imgref)
                    
    def runXYZ_DriftCorrection(self, posID = None):
        if 'imageStack' not in self.acq:
            return
        startTime = timeit.timeit()
        if posID == None:
            posID = self.currentPosID
        shape = self.acq['imageStack'][0].shape
        self.acq['imgref_imaging'] = transform.resize(self.positions[posID]['refImg'],shape)
        self.acq['imgref_ref'] = transform.resize(self.positions[posID]['refImgZoomout'],shape)
        self.calcFocus()
        self.calcDrift()
        x,y,z = [self.positions[posID][key] for key in ['x','y','z']]
        shiftx,shifty = self.measure['shiftxy']
        shiftz = self.measure['shiftz']
        self.positions[posID]['x'] = x + shiftx
        self.positions[posID]['y'] = y + shifty
        self.positions[posID]['z'] = z + shiftz
        self.positions[posID]['xyzShift'] = self.positions[posID]['xyzShift'] + np.array([shiftx,shifty,shiftz])
        self.frames[StartPage].driftLabel.configure(text = 'Detected drift of {0}px in x and {1}px in y'.format(shiftx.item(),shifty.item()))
        end = timeit.timeit()
        elapsedTime = end-startTime
        printStatus('Done after {0}s'.format(elapsedTime))
        self.showNewImages()
        
    def showNewImages(self):
        image = self.acq['imageStack']
        i = 0
        a = self.AFImageAx
        #show images
        for im in image:
            a[i].clear()
            a[i].imshow(im)
            a[i].axis('equal')
            a[i].axis('off')
            i+=1
        #show best focused image
        maxInd = self.measure['FMlist'].argmax().item()
        siz = image[0].shape
        rect = patches.Rectangle((0,0),siz[0],siz[1], fill = False, linewidth = 5, edgecolor = 'r')
        a[maxInd].add_patch(rect)
        self.frames[StartPage].canvas['canvas_af'].draw_idle()
        
    def calcFocus(self):
        image = self.acq['imageStack']
        FM = np.array([])
        for im in image:
            FM = np.append(FM,(focusMeasure(im)))
        self.measure['shiftz'] = FM.argmax().item() - np.floor(len(image)/2) #this needs to be checked obviously, depending on how Z info is dealt with
        self.measure['FMlist'] = FM
        
        
    def calcDrift(self):
        image = np.max(self.acq['imageStack'],0)
        imgref = self.acq['imgref_imaging']
        shift = computeDrift(imgref,image)
        shiftx = shift['shiftx']
        shifty = shift['shifty']    
        self.measure['shiftxy'] = (shiftx,shifty)


    def createFigureForAFImages(self):
        if 'imageStack' not in self.acq:
            return
        image = self.acq['imageStack']
        subplotLength = len(image)
        f = self.AFImageFig
        a = self.AFImageAx
        for ax in a.copy():
            try:
                a.remove(ax)
                f.delaxes(ax)
            except:
                printStatus('axes delete not working')
        for i in range(subplotLength):
            a.append(f.add_subplot(1,subplotLength,i+1))
        
    def getCurrentPosition(self):
        if simulation:
            #simulate position for now. 
            #eventually, pull position from other program here
            x = np.random.randint(-100,100)
            y = np.random.randint(-100,100)
            z = np.random.randint(-100,100)
        else:
            self.getCommands.positionGrabDone = False
            self.sendCommands.getCurrentPosition()
            self.getCommands.waitForCurrentPosition()
            x,y,z = self.currentCoordinates
        return({'x':x,'y':y,'z':z})
    
    def createNewPos(self,xyz, refImages = None):
        #just starting with an empty dict for now
        if len(self.positions)==0:
            posID = 1
        else:
            posID = max(self.positions.keys())+1  
        self.positions[posID] = xyz
        if refImages is None:
            ##load sample ref images
            self.loadTestRefImage(self)
        else:
            self.acq['imgref_imaging'] = refImages['imaging']
            self.acq['imgref_ref'] = refImages['ref']
        self.positions[posID]['refImg'] = self.acq['imgref_imaging']
        self.positions[posID]['refImgZoomout'] = self.acq['imgref_ref']
        self.positions[posID]['xyzShift'] = np.array([0,0,0])
    
    def addPosition(self,cont,xyz = None, refImages = None):
        if xyz is None:
            xyz = self.getCurrentPosition()
        #add position to table
        self.createNewPos(xyz, refImages = refImages)
        cont.redrawPositionTable()        
        self.backupPositions()
        
    def clearPositions(self,cont):
        self.positions = {}
        cont.redrawPositionTable()
        
        
    def deletePosition(self,posID):
        del self.positions[posID]
        self.frames[PositionsPage].redrawPositionTable()    
        self.backupPositions()
        
    def updatePosition(self,posID):
        xyz = self.getCurrentPosition()
        self.positions[posID].update(xyz)
        self.frames[PositionsPage].redrawPositionTable()
        self.backupPositions()
        
       
    def addTimelineStep(self, stepDict, ind = None):
        print("step name: {0}, type: {1}, Period: {2}s, Duration: {3}min".format(
                stepDict['SN'], stepDict['IU'], stepDict['P'], stepDict['D']))
        if ind == None:
            self.timelineSteps.append(stepDict)
        else:
            self.timelineSteps.insert(ind,stepDict)
                
        self.frames[TimelinePage].drawTimelineSteps()
        
    def backupPositions(self):
        positions = self.positions
        pickle.dump(positions, open(initDirectory+'positions.p','wb'))
        
    def addStepToQueue(self,step,posID):
        step = step.copy()
        step.update(dict(posID = posID))
        self.timerStepsQueue.put(step)
        
    def runStepFromQueue(self):
        while self.imagingActive:
            # update() function on the GUI is necessary to keep it active
            self.update()
            if self.stepRunning: #make sure something isn't already running
                continue
            if not self.timerStepsQueue.empty():
                step = self.timerStepsQueue.get()
            else:
                continue
            self.stepRunning = True
            posID = step['posID']
            if step['EX']:
                ex = 'Exclusive'
            else:
                ex = 'Non-Exclusive'
            print('{0} {1} Timer {2} running at {3}s '.format(ex, step['IU'], posID, dt.datetime.now().second))
            
            #this should actually be set once data from position is received, because drift/af calculation will be done after that
            self.currentPosID = posID
#            #do the steps in threads so they don't freeze up the GUI
#            if step['IU'] == 'Image':
#                self.currentStepThread = threading.Thread(target = self.imageNewPosition, args = [step])
#            elif step['IU'] == 'Uncage':
#                self.currentStepThread = threading.Thread(target = self.uncageNewPosition, args = [step])
#            self.currentStepThread.daemon = True
#            self.currentStepThread.start()
        
            #we're already in a thread so maybe don't need another one here
            if step['IU'] == 'Image':
                self.imageNewPosition(step)
            elif step['IU'] == 'Uncage':
                self.uncageNewPosition(step)
            
        
    def imageNewPosition(self,step):
        posID, x, y, z = self.parseStep(step)
        self.moveStage(x,y,z)
        self.grabStack()
        self.stepRunning = False
        self.loadAcquiredImage()
        self.runXYZ_DriftCorrection(posID)
        
    def uncageNewPosition(self,step):
        posID, x, y, z = self.parseStep(step)
        self.moveStage(x,y,z)
        self.uncage()
        self.stepRunning = False

    def parseStep(self,step):
        posID = step['posID']
        x,y,z = [self.positions[posID][xyz] for xyz in ['x','y','z']]
        return(posID, x, y, z)


    def moveStage(self,x,y,z):
        self.getCommands.stageMoveDone = False
        self.sendCommands.moveStage(x,y,z)
        self.getCommands.waitForStageMoveDone()
        
    def grabStack(self):
        self.getCommands.grabOneStackDone = False
        self.sendCommands.grabOneStack()
        self.getCommands.waitForGrabDone()
        
    def uncage(self):
        self.getCommands.uncagingDone = False
        self.sendCommands.doUncaging()
        self.getCommands.waitForUncagingDone()
        
class StartPage(ttk.Frame):
    
    name = 'Main'
    
    def __init__(self,parent,controller):
        ttk.Frame.__init__(self,parent)
        self.controller = controller
        self.bind("<Visibility>", self.on_visibility)
        frame_leftButtons = ttk.Frame(self)
        frame_leftButtons.grid(row = 0, column = 0, rowspan = 2, sticky = 'nw')
        button = ttk.Button(frame_leftButtons,text = "Load Test Image", command = 
                            lambda: controller.loadTestImage(self))
        button.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = 'nw')
        button1 = ttk.Button(frame_leftButtons,text = "Load Test Ref Image", command = 
                            lambda: controller.loadTestRefImage(self))
        button1.grid(row = 1, column = 0, padx = 10, pady = 10, sticky = 'nw')
        button2 = ttk.Button(frame_leftButtons,text = "Run Drift Correction", command = 
                            lambda: controller.runXYZ_DriftCorrection(1))
        button2.grid(row = 2, column = 0, padx = 10, pady = 10, sticky = 'nw')        
        button_start = ttk.Button(frame_leftButtons,text = "Start Imaging", command = 
                                  lambda:self.startImaging())
        button_start.grid(row = 3, column = 0, padx = 10, pady = 10, sticky = 'nw')
        button_end = ttk.Button(frame_leftButtons,text = "Stop Imaging", command = 
                                  lambda:self.stopImaging())
        button_end.grid(row = 4, column = 0, padx = 10, pady = 10, sticky = 'nw')
#        button_listen = ttk.Button(frame_leftButtons,text = "Listen For Instructions", command = 
#                                  lambda:controller.listenToInstructionsFile())
#        button_listen.grid(row = 5, column = 0, padx = 10, pady = 10, sticky = 'nw')
        
        
        driftLabel = tk.Label(self, text = "drift placeholder", 
                              font = LARGE_FONT)
        driftLabel.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = 'nw')
        frame_forCanvases = ttk.Frame(self)
        frame_forCanvases.grid(row = 1, column = 1, columnspan = 2, rowspan = 2)
        f = Figure(figsize = (5,2), dpi = fig_dpi)
#        f.set_tight_layout(True)
        f.subplots_adjust(left = 0, right = 1,  bottom = 0, wspace = 0.02, hspace = 0)
        a = [f.add_subplot(1,1,1)]
        controller.AFImageAx = a
        controller.AFImageFig = f
        canvas_af = FigureCanvasTkAgg(f,frame_forCanvases)
        canvas_af.show()
        canvas_af.get_tk_widget().config(borderwidth = 1, background='gray',  highlightcolor='gray', highlightbackground='gray')
        canvas_af.get_tk_widget().grid(row = 1, column = 0, padx = 10, pady = 10, sticky = 'nsew')
        self.driftLabel = driftLabel
        canvas_timeline = FigureCanvasTkAgg(f_timeline,frame_forCanvases)
        canvas_timeline.show()
        canvas_timeline.get_tk_widget().config(borderwidth = 1, background='gray',  highlightcolor='gray', highlightbackground='gray')
        canvas_timeline.get_tk_widget().grid(row = 0, column = 0, padx = 10, pady = 10, sticky = 'nsew')        
        canvas_positions = FigureCanvasTkAgg(f_positions,frame_forCanvases)
        canvas_positions.show()
        canvas_positions.get_tk_widget().config(borderwidth = 1, background='gray',  highlightcolor='gray', highlightbackground='gray')
        canvas_positions.get_tk_widget().grid(row = 0, column = 1, rowspan = 2, padx = 10, pady = 10, sticky = 'nsew')    
        self.canvas = dict(canvas_timeline = canvas_timeline, canvas_positions = canvas_positions, canvas_af = canvas_af)
    
    
    def on_visibility(self,event):
        fitFigToCanvas(f_timeline, self.canvas['canvas_timeline'])
        fitFigToCanvas(f_positions, self.canvas['canvas_positions'])
        for key in self.canvas:
                self.canvas[key].draw_idle()
            
    def startImaging(self):
        self.posTimers = {}
        with self.controller.timerStepsQueue.mutex:
            self.controller.timerStepsQueue.queue.clear()
        individualSteps = self.controller.individualTimelineSteps
        for posID in individualSteps:
             self.posTimers[posID] = PositionTimer(self.controller, individualSteps[posID], self.controller.addStepToQueue, posID)
        self.controller.imagingActive = True
        self.controller.queRun = threading.Thread(target = self.controller.runStepFromQueue)
        self.controller.queRun.daemon = True
        self.controller.queRun.start()
        
    def stopImaging(self):
        for posID in self.posTimers:
            self.posTimers[posID].stop()
        self.controller.imagingActive = False
                

class DriftPage(ttk.Frame):
    
    name = 'Drift Correction'
    
    def __init__(self,parent,controller):
        ttk.Frame.__init__(self,parent)
        self.controller = controller
        label = tk.Label(self, text = "Total Image Channels", font=LARGE_FONT)
        label.grid(row = 0, column = 0, sticky = 'nw', padx = 10, pady = 10)
        self.totalChannelsVar = tk.StringVar(self)
        entry_totalChannels = ttk.Entry(self, textvariable = self.totalChannelsVar)
        entry_totalChannels.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = 'nw')
        label2 = tk.Label(self, text = "Drift Correction Channel", font=LARGE_FONT)
        label2.grid(row = 1, column = 0, sticky = 'nw', padx = 10, pady = 10)
        self.driftCorrectionChannelVar = tk.StringVar(self)
        entry_driftChannel = ttk.Entry(self, textvariable = self.driftCorrectionChannelVar)
        entry_driftChannel.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = 'nw')
        self.setDefaultSettings()
        
    def setDefaultSettings(self):
        try:
            self.totalChannelsVar.set(self.controller.settings['totalChannels'])
        except:
            pass
        try:
            self.driftCorrectionChannelVar.set(self.controller.settings['driftCorrectionChannel'])
        except:
            pass
        
        
        
class PositionsPage(ttk.Frame):
    
    name = 'Positions'
    
    def __init__(self,parent,controller):
        ttk.Frame.__init__(self,parent)
        self.bind("<Visibility>", self.on_visibility)
        self.controller = controller
        frame_forButtons = ttk.Frame(self)
        frame_forButtons.grid(column = 0, row = 0, sticky = 'nw')
        frame_forZoom = ttk.Frame(self)
        frame_forZoom.grid(column = 1, row = 3, sticky = 'ew', padx = 10, pady = 10)
        frame_forGraphics = ttk.Frame(self)
        frame_forGraphics.grid(column = 1, row = 0, sticky = 'nsew')
        button_addPosition = ttk.Button(frame_forButtons, text = "Add current position", 
                            command = lambda:controller.addPosition(self))
        button_addPosition.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = 'wn')
        button_clearPositions = ttk.Button(frame_forButtons, text = "Clear All Positions", 
                            command = lambda:controller.clearPositions(self))
        button_clearPositions.grid(row = 1, column = 0, padx = 10, 
                            pady = 10, sticky = 'wn')
        button_cellView = ttk.Button(frame_forButtons, text = "Macro View", 
                            command = lambda:controller.showMacroViewWindow())
        button_cellView.grid(row = 2, column = 0, padx = 10, 
                            pady = 10, sticky = 'wn')
        label_imagingZoom = tk.Label(frame_forZoom, text = "Imaging Zoom", font=LARGE_FONT)
        label_imagingZoom.grid(row = 0, column = 0, sticky = 'nw', padx = 10, pady = 10)
        self.imagingZoom= tk.StringVar(self)
        self.imagingZoom.set(30)
        entry_imagingZoom = ttk.Entry(frame_forZoom, textvariable = self.imagingZoom)
        entry_imagingZoom.grid(row = 0, column = 1, padx = 10, pady = 10, sticky = 'nw')
        label_refZoom = tk.Label(frame_forZoom, text = "Reference Zoom", font=LARGE_FONT)
        label_refZoom.grid(row = 0, column = 2, sticky = 'nw', padx = 10, pady = 10)
        self.refZoom = tk.StringVar(self)
        self.refZoom.set(15)
        entry_refZoom = ttk.Entry(frame_forZoom, textvariable = self.refZoom)
        entry_refZoom.grid(row = 0, column = 3, padx = 10, pady = 10, sticky = 'nw')
        
        label_imagingSlices = tk.Label(frame_forZoom, text = "Imaging Slices", font=LARGE_FONT)
        label_imagingSlices.grid(row = 1, column = 0, sticky = 'nw', padx = 10, pady = 10)
        self.imagingSlices= tk.StringVar(self)
        self.imagingSlices.set(3)
        entry_imagingSlices = ttk.Entry(frame_forZoom, textvariable = self.imagingSlices)
        entry_imagingSlices.grid(row = 1, column = 1, padx = 10, pady = 10, sticky = 'nw')
        label_refSlices = tk.Label(frame_forZoom, text = "Reference Slices", font=LARGE_FONT)
        label_refSlices.grid(row = 1, column = 2, sticky = 'nw', padx = 10, pady = 10)
        self.refSlices = tk.StringVar(self)
        self.refSlices.set(10)
        entry_refSlices = ttk.Entry(frame_forZoom, textvariable = self.refSlices)
        entry_refSlices.grid(row = 1, column = 3, padx = 10, pady = 10, sticky = 'nw')
        
        
        #treeview example given at http://knowpapa.com/ttk-treeview/
        positionsTableFrame = ttk.Frame(frame_forGraphics)
        positionsTableFrame.grid(row = 0, column = 0, sticky = 'nsew', padx = 10, pady = 10)
        self.createPositionsTable(positionsTableFrame)
        
        #create canvas for previewing reference images
        f1 = Figure(figsize = (4,2), dpi = fig_dpi)
        f1.subplots_adjust(left = 0, right = 1,  bottom = 0, top = 1, wspace = 0.02, hspace = 0)
        canvas_previewRefImages = FigureCanvasTkAgg(f1,frame_forGraphics)
        canvas_previewRefImages.get_tk_widget().config(borderwidth = 1, background='gray',  highlightcolor='gray', highlightbackground='gray')
        canvas_previewRefImages.show()
        canvas_previewRefImages.get_tk_widget().grid(row = 1, column = 0, padx = 10, sticky = 'nsew')
        a1=[]
        self.canvas_previewRefImages = canvas_previewRefImages
        for i in range(2):
            a1.append(f1.add_subplot(1,2,i+1))
        controller.refImgAx = a1
        controller.refImgFig = f1
        #relative positions figure
        f_positions.set_size_inches(4,4)
        canvas_positions = FigureCanvasTkAgg(f_positions,frame_forGraphics)
        canvas_positions.show()
        canvas_positions.get_tk_widget().config(borderwidth = 1, background='gray',  highlightcolor='gray', highlightbackground='gray')
        canvas_positions.get_tk_widget().grid(row = 0, column = 2, rowspan = 2, padx = 10, pady = 10, sticky = 'nsew')        
        a2 = f_positions.add_subplot(1,1,1)
        cAx,kw = colorbar.make_axes_gridspec(a2)
        self.canvas_positions = canvas_positions
        self.positionPreviewAxis = a2
        self.colorbarAxis = cAx
        self.previewPositionLocations()
        
    def createPositionsTable(self,container):
        tree = ttk.Treeview(container)
        tree["columns"] = ("x","y","z")
        tree.column("#0", width = 300)
        tree.column("x", width=30 )
        tree.column("y", width=30)
        tree.column("z", width=50)
        tree.heading("x", text="X")
        tree.heading("y", text="Y")
        tree.heading("z", text="Z")
        tree.bind("<Button-3>", self.onTreeRightClick)
        tree.bind("<<TreeviewSelect>>", self.onTreeSelect)
        tree.grid(row = 0, column = 0, sticky = 'nsew')
        scroll = ttk.Scrollbar(container,orient = "vertical", command = tree.yview)
        scroll.grid(row = 0, column = 1, pady = 10, sticky = 'nsw')
        tree.configure(yscrollcommand = scroll.set)
        self.tree = tree
        
    def previewPositionLocations(self):
        positions = self.controller.positions
        ax = self.positionPreviewAxis
        cAx = self.colorbarAxis
        w = 8
        h = 8
        ax.clear()
        cAx.clear()
        X = np.array([])
        Y = np.array([])
        Z = np.array([])
        for posID in positions:
            X = np.append(X, positions[posID]['x'])
            Y = np.append(Y, positions[posID]['y'])
            Z = np.append(Z, positions[posID]['z'])
        
        if len(positions)>0:
            vmin = Z.min()-1
            vmax = Z.max()+1
        else:
            vmin = -100
            vmax = 100
            
        posLabels = list(positions.keys())
        cmap = matplotlib.cm.jet
        norm = matplotlib.colors.Normalize(vmin = vmin,vmax = vmax)
        for x,y,z,p in zip(X,Y,Z,posLabels):
            ax.add_patch(patches.Rectangle(xy = (x,y), width = w, height = h,
                                           facecolor = cmap(norm(z))))
            ax.annotate(str(p),xy = (x,y), xytext = (x+w, y+h))
        cb1 = colorbar.ColorbarBase(ax = cAx, cmap = cmap, norm = norm)
        cb1.set_label('Z (µm)')
        ax.set_ylabel('Y (µm)')
        ax.set_xlabel('X (µm)')
        ax.axis('equal')
        cb1.ax.yaxis.label.set_size(8)
        ax.xaxis.label.set_size(8)
        ax.yaxis.label.set_size(8)
        ax.relim()
        xlim0, xlim1 = ax.get_xlim()
        ylim0, ylim1 = ax.get_ylim()
        clim0, clim1 = cb1.ax.get_ylim()
        ax.xaxis.set_ticks([int(xlim0), int(xlim1)])
        ax.yaxis.set_ticks([int(ylim0), int(ylim1)])
        cb1.ax.yaxis.set_ticks([int(clim0), int(clim1)])
        ax.autoscale_view()
        self.canvas_positions.draw_idle()

    def on_visibility(self,event):
        fitFigToCanvas(f_positions, self.canvas_positions)
        self.redrawPositionTable()
        self.canvas_previewRefImages.draw_idle()
        
    def onTreeRightClick(self,event):
        iid = self.tree.identify_row(event.y)
        if iid:
            #mouse over item
            self.tree.selection_set(iid)
        for item in self.tree.selection():
            item_text = self.tree.item(item,"text")
            print(item_text)
        if len(self.tree.selection())==0:
            return
        self.popup = tk.Menu(self, tearoff = 0)
        posID = int(item_text.split()[1])
        self.popup.add_command(label = "Update XYZ", command = lambda:self.controller.updatePosition(posID))
        self.popup.add_command(label = "Delete", command = lambda:self.controller.deletePosition(posID))
        self.popup.post(event.x_root,event.y_root)
        
    def onTreeSelect(self,event):
        for item in self.tree.selection():
            item_text = self.tree.item(item,"text")
            posID = int(item_text.split()[1])
        self.drawRefImages(posID)
        self.selectPositionInGraph(posID)

    def selectPositionInGraph(self,posID):
        positions = self.controller.positions
        ax = self.positionPreviewAxis
        x = positions[posID]['x']
        y = positions[posID]['y']
        arrowprops = dict(facecolor = 'black')
        arrow = ax.annotate("",xy = (x,y), xytext = (x-10,y-10),arrowprops = arrowprops)
        try:
            self.selectionArrow.remove()
        except:
            pass
        self.selectionArrow = arrow
        self.canvas_positions.draw_idle()
            
    def redrawPositionTable(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for posID in self.controller.positions:
            x = self.controller.positions[posID]['x']
            y = self.controller.positions[posID]['y']
            z = self.controller.positions[posID]['z']
            self.tree.insert("",posID, text = "Position {0}".format(posID), 
                   values = (x,y,z))
        self.previewPositionLocations()
        self.canvas_previewRefImages.draw_idle()

            
    def drawRefImages(self,posID):
        refs = [self.controller.positions[posID]['refImg'],self.controller.positions[posID]['refImgZoomout']]
        for ax,r in zip(self.controller.refImgAx,refs):
            ax.clear()
            ax.axis('off')
            ax.imshow(r)
        self.canvas_previewRefImages.draw_idle()
        

class TimelinePage(ttk.Frame):
    
    name = 'Timeline'
     
    def __init__(self,parent,controller):
        ttk.Frame.__init__(self,parent)
        self.bind("<Visibility>", self.on_visibility)
        self.controller = controller
        tFrame = timelineStepsFrame(self, controller)
        tFrame.grid(row = 0, column = 0, columnspan = 1)       
        canvas1 = FigureCanvasTkAgg(f_timeline,self)
        canvas1.get_tk_widget().config(borderwidth = 1, background='gray',  highlightcolor='gray', highlightbackground='gray')
        canvas1.show()
        canvas1.get_tk_widget().grid(row = 2, column = 0, columnspan = 2,
                             padx = 10, pady = 10, sticky = 'nsew')
        self.canvas_timeline = canvas1
        self.tFrame = tFrame
        
        timelineTableFrame = ttk.Frame(self)
        timelineTableFrame.grid(row = 0, column = 1, padx = 10, pady = 10)
        self.createTimelineTable(timelineTableFrame)
        self.drawTimelineSteps()
        
    def createTimelineTable(self, container):
        tree = ttk.Treeview(container)
        tree["columns"] = ("sn","iu",'ex',"p","d")
        tree.column("#0", width = 30)
        tree.column("sn", width = 120)
        tree.column("iu", width=60 )
        tree.column("ex", width=60 )
        tree.column("p", width=60 )
        tree.column("d", width=75)
        tree.heading("#0", text = '#')
        tree.heading("sn", text="Step")        
        tree.heading("iu", text="Type")
        tree.heading("ex", text="Exclusive")
        tree.heading("p", text="Period (s)")
        tree.heading("d", text="Duration (m)")
        tree.bind("<Button-3>", self.onTimelineTableRightClick)
        tree.bind("<<TreeviewSelect>>", self.onTimelineTableSelect)
        tree.grid(row = 0, column = 0, sticky = 'nsew')
        scroll = ttk.Scrollbar(container,orient = "vertical", command = tree.yview)
        scroll.grid(row = 0, column = 1, sticky = 'nse', pady = 10)
        tree.configure(yscrollcommand = scroll.set)
        self.timelineTree = tree
    
    def on_visibility(self,event):
        fitFigToCanvas(f_timeline, self.canvas_timeline)
#        h = self.canvas_timeline.get_tk_widget().winfo_height()
#        w = self.canvas_timeline.get_tk_widget().winfo_width()
#        f_timeline.set_size_inches(w/fig_dpi,h/fig_dpi)
        self.canvas_timeline.draw_idle()
        self.createTimelineChart()
    
    def createTimelineChart(self,*args):
        timelineSteps = self.controller.timelineSteps
        positions = self.controller.positions
        stagger = floatOrZero(self.tFrame.staggerEntryVar.get())

        if len(timelineSteps) == 0:
            return
        if len(positions)==0:
            positions = {1:[],2:[],3:[],4:[],5:[]}
#
#        positions = app.positions
#        timelineSteps = app.timelineSteps
#        stagger = 10
#            
        pos_timeline = {}
        ylabels1 = []
        ii = 0
        posIDs = positions.keys()
        for posID in posIDs:
            ylabels1.append('Position {0}'.format(posID))
            pos_timeline[posID] = []
            totalTime = 0
            firstStep = True
            for step in timelineSteps:
                if firstStep:
                    startTime = 0
#                    D = step['D'] + min(stagger, step['D']) * ii
                    D = step['D'] + stagger * ii
                    firstStep = False
                else:
#                    startTime = stagger * ii + totalTime
                    startTime = totalTime
                    D = step['D']
                P = step['P']
                if D == None or P == None:
                    D = 1
                    P = 60
                if step['EX']:
                    P = D*60
                stepStartTimes = np.arange(startTime,startTime+D,P/60)
                stepEndTimes = stepStartTimes + P/60
                stepStartEnd = np.array([stepStartTimes,stepEndTimes])
                pos_timeline[posID].append(np.array([stepStartEnd]))
                totalTime += D
            ii += 1
        
        backup = 0
        individualSteps = {}
        timelineIndex = {}
        for posID in posIDs:
            timelineIndex[posID] = 0
            individualSteps[posID] = []
        minTime = np.zeros(len(posIDs))
        while True:
            startTime = np.array([np.inf])
            for pos in pos_timeline:
                startEnd = pos_timeline[pos][0][0][:,0]#figure out which thing is set to start next
                posInd = list(posIDs).index(pos)
                S = max(startEnd[0],minTime[posInd])
                E = S + startEnd[1] - startEnd[0]
                EX = timelineSteps[timelineIndex[pos]]['EX']
                if S < startTime or (S == startTime and EX): #figure out if this is the earliest step, or exclusive step that starts the same time as others
                    startTime = S
                    endTime = E
                    firstPos = pos #save which position runs first                   
            posInd = list(posIDs).index(firstPos)
            EX = timelineSteps[timelineIndex[firstPos]]['EX']

            individualSteps[firstPos].append({'startTime':startTime,
                                    'endTime':endTime,
                                    'EX':EX,
                                    'IU':timelineSteps[timelineIndex[firstPos]]['IU']})
            #delete added position
            pos_timeline[firstPos][0] = np.array([np.delete(pos_timeline[firstPos][0][0],0,1)])
            if EX:
                minTime[minTime<endTime] =  endTime
            else:
                minTime[posInd]=max(minTime[posInd],endTime)
                minTime[minTime<startTime] =  startTime

            #if this step is done, move to next step
            if pos_timeline[firstPos][0].size == 0:
                    timelineIndex[firstPos] += 1
                    del(pos_timeline[firstPos][0])
            #if this position is done, remove it
            if len(pos_timeline[firstPos]) == 0:
                del(pos_timeline[firstPos])
            if len(pos_timeline)==0:
                break
            backup += 1
            if backup > 100000: #make sure loop doesn't run forever while testing
                print('loop running too long')
                break
        
        a_timeline.clear()
        yInd = 0
        for key in individualSteps:
            yrange = (yInd-.4, 0.8)
            xranges = []
            c = []
            yInd+=1
            for step in individualSteps[key]:
                xranges.append((step['startTime'],step['endTime']-step['startTime']))
                if not step['EX']:
                    c.append('blue') #regular imaging
                elif step['EX'] and step['IU'] == 'Image':
                    c.append('green') #exclusive imaging
                else:
                    c.append('red') #uncaging
            a_timeline.broken_barh(xranges,yrange, color = c,edgecolor = 'black')
        a_timeline.set_yticks(list(range(len(posIDs))))
        a_timeline.set_yticklabels(ylabels1)
        a_timeline.axis('tight')
        a_timeline.set_ylim(auto = True)
        a_timeline.grid(color = 'k', linestyle = ':')
        y1,y2 = a_timeline.get_ylim()
        if y2 > y1:
            a_timeline.invert_yaxis()
        legendPatchRed = patches.Patch(color = 'red', label = 'Uncaging')
        legendPatchBlue = patches.Patch(color = 'blue', label = 'Imaging')
        legendPatchGreen = patches.Patch(color = 'green', label = 'Exclusive Imaging')
        a_timeline.legend(handles = [legendPatchRed,legendPatchBlue,legendPatchGreen])
        self.controller.individualTimelineSteps = individualSteps
        self.canvas_timeline.draw_idle()
#        app.frames[TimelinePage].canvas.draw_idle()
        
    def onTimelineTableRightClick(self, event):
        tree = self.timelineTree
        iid = tree.identify_row(event.y)
        if iid:
            #mouse over item
            tree.selection_set(iid)
        for item in tree.selection():
            item_text = tree.item(item,"text")
            item_number = tree.index(item)
            print(item_text)
            print(item_number)
        if len(tree.selection())==0:
            return
        self.popup = tk.Menu(self, tearoff = 0)
        self.popup.add_command(label = "Insert Step", command = lambda:self.insertTimelineStep(item_number))
        self.popup.add_command(label = "Delete Step", command = lambda:self.deleteTimelineStep(item_number))
        self.popup.post(event.x_root,event.y_root)
    
    def insertTimelineStep(self,ind):
        self.tFrame.addStepCallback(self.controller,ind)
        self.drawTimelineSteps()
        self.backupTimeline()

        
    def deleteTimelineStep(self,ind):
        del self.controller.timelineSteps[ind]
        self.drawTimelineSteps()
        self.backupTimeline()

    def onTimelineTableSelect(self,event):
        pass
    
    def drawTimelineSteps(self):
        tree = self.timelineTree
        timelineSteps = self.controller.timelineSteps
        #clear table first
        for i in tree.get_children():
            tree.delete(i)
        #add values to table
        ii = 1
        for stepDist in timelineSteps:
            SN = stepDist['SN']
            P = stepDist['P']
            D = stepDist['D']
            IU = stepDist['IU']
            EX = stepDist['EX']
            tree.insert("",ii, text = str(ii), values = (SN,IU,EX,P,D))
            ii+=1
            
        self.createTimelineChart()
    
    def backupTimeline(self):
        timelineSteps = self.controller.timelineSteps
        pickle.dump(timelineSteps, open(initDirectory+'timelineSteps.p','wb'))

        
        
class timelineStepsFrame(ttk.Frame):
    def __init__(self,parent,controller):
        ttk.Frame.__init__(self,parent)
        self.controller = controller
        label1 = ttk.Label(self, text = 'Step Name:', font = LARGE_FONT)
        label1.grid(row = 0, column = 0, sticky = 'nw', padx = 10, pady = 10)
        self.stepName = tk.StringVar(self)
        stepNameEntry = ttk.Entry(self, width = 30, textvariable = self.stepName)
        stepNameEntry.grid(row = 0, column = 1, sticky = 'nw', padx = 10, pady = 10)

        #This stringvar callback thing isn't working
        self.image_uncage = tk.StringVar(self)
        self.image_uncage.set("Image")
        self.image_uncage.trace('w', self.imageInFromFrame)

        placeHolderFrame = ttk.Frame(self)
        placeHolderFrame.grid(row = 1, column = 1, columnspan = 1, sticky = 'nw', pady = 10)
        imageInfoFrame = ttk.Frame(placeHolderFrame)
        imageInfoFrame.pack(side = 'left', anchor = 'w')
        
        rb1 = ttk.Radiobutton(self, text = 'Image', variable = self.image_uncage,
        		value = 'Image')
        rb1.grid(row = 1, column = 0, sticky = 'nw', pady = 10, padx = 10)        
        
        periodLabel1 = ttk.Label(imageInfoFrame, text = '  Period: ', font = LARGE_FONT)
        periodLabel1.pack(anchor = 'w', side = 'left')
        self.periodEntryVar = tk.StringVar(self)
        periodEntry = ttk.Entry(imageInfoFrame,width = 4, textvariable = self.periodEntryVar)
        periodEntry.pack(anchor = 'w', side = 'left')
        periodLabel2 = ttk.Label(imageInfoFrame, text = 'sec, ', font = LARGE_FONT)
        periodLabel2.pack(anchor = 'w', side = 'left')
        durationLabel1 = ttk.Label(imageInfoFrame, text = 'Duration: ', font = LARGE_FONT)
        durationLabel1.pack(anchor = 'w', side = 'left')
        self.durationEntryVar = tk.StringVar(self)
        durationEntry = ttk.Entry(imageInfoFrame,width = 4, textvariable = self.durationEntryVar)
        durationEntry.pack(anchor = 'w', side = 'left')
        durationLabel2 = ttk.Label(imageInfoFrame, text = 'min', font = LARGE_FONT)
        durationLabel2.pack(anchor = 'w', side = 'left')
        
        rb2 = ttk.Radiobutton(self, text = 'Uncage', variable = self.image_uncage,
        		value = 'Uncage')
        rb2.grid(row = 2, column = 0, sticky ='nw', padx = 10, pady = 3)
        
        self.exclusiveVar = tk.BooleanVar(self)
        exclusiveCB = ttk.Checkbutton(self, text = 'Exclusive', variable = self.exclusiveVar)        
        exclusiveCB.grid(row = 2, column = 1, sticky = 'nw', padx = 10, pady = 3)
        staggerFrame = ttk.Frame(self)
        staggerFrame.grid(row = 4, column = 0, sticky = 'nw', columnspan = 2)
        staggerLabel1 = ttk.Label(staggerFrame, text = 'Stagger: ', font = LARGE_FONT)
        staggerLabel1.grid(row = 0, column = 0, sticky = 'nw', padx = 10, pady = 10)
        self.staggerEntryVar = tk.StringVar(self)
        try:
            self.staggerEntryVar.set(controller.settings['stagger'])
        except:
            pass
        self.staggerEntryVar.trace('w',parent.createTimelineChart)
        staggerEntry = ttk.Entry(staggerFrame, width = 4, textvariable = self.staggerEntryVar)
        staggerEntry.grid(row = 0, column = 1, sticky = 'nw', padx = 0, pady = 10)
        staggerLabel2 = ttk.Label(staggerFrame, text = 'min', font = LARGE_FONT)
        staggerLabel2.grid(row = 0, column = 2, sticky = 'nw', padx = 0, pady = 10)
        
        button = ttk.Button(self, text = "Add Step", 
                            command = lambda:self.addStepCallback(controller))
        button.grid(row = 3, column = 0, padx = 10, pady = 10, sticky = 'wn')    
        self.imageInfoFrame = imageInfoFrame      
        
        
    def addStepCallback(self, cont, ind = None):
        #get values
        SN = self.stepName.get()
        P = floatOrNone(self.periodEntryVar.get())
        D = floatOrNone(self.durationEntryVar.get())
        IU = self.image_uncage.get()
        EX = self.exclusiveVar.get()
        cont.addTimelineStep({'SN':SN, 'IU':IU, 'EX':EX, 'P':P, 'D':D}, ind)
        #reset values
        self.stepName.set('')
        self.periodEntryVar.set('')
        self.durationEntryVar.set('')
        cont.frames[TimelinePage].backupTimeline()

   
    def imageInFromFrame(self, *args):
        var = self.image_uncage.get()
        if var=="Image":
            self.imageInfoFrame.pack(side = 'left', anchor = 'w')
            self.exclusiveVar.set(False)            
        else:
            self.imageInfoFrame.pack_forget()
            self.exclusiveVar.set(True)
    
class PositionTimer(object):
    def __init__(self, controller, steps, function, *args, **kwargs):
        self.controller = controller
        self._timer     = None
        self.steps      = steps
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.stepCount  = 0
        
        self.runTimes = []
        for step in self.steps:
            self.runTimes.append(step['startTime'])

        self.start()
        
    def _run(self, stepCount):
        self.is_running = False
        self.start() #starts next timer countdown before running function
        self.function(self.steps[stepCount],*self.args, **self.kwargs)

        
    def start(self):
        if not self.is_running:
            if self.stepCount >= len(self.runTimes):
                return
            if self.stepCount == 0:
                prevTime = 0
            else:
                prevTime = self.runTimes[self.stepCount-1]
            interval = self.runTimes[self.stepCount] - prevTime
            stepCount = self.stepCount
            self.stepCount += 1
            # for now, interval is store in minutes. probably a good idea to change it to seconds.
            interval = interval * 60
            printStatus('\nTimer Interval = {0}'.format(interval))
            self._timer = threading.Timer(interval,self._run,args=[stepCount])
            self._timer.start()
            self.is_running = True
            
    def stop(self):
        self._timer.cancel()
        self.is_running = False
        
class instructionThread(object):
    def __init__(self,controller, path, filename, function, *args, **kwargs):
        self.controller = controller
        self.path       = path
        self.filename   = filename
        self.function   = function
        self.observer   = Observer()
        self.args =     args
        self.kwargs =   kwargs
        self.thread = threading.Thread(target = self.run, args = ())
        self.thread.daemon   = True
        self.thread.start()
        
    def run(self):
        """Method that runs forever"""
        self.event_handler = instructionHandler(self.controller, self.path, self.filename, self.function, self.args, self.kwargs)
        self.observer = Observer()
        self.observer.schedule(self.event_handler, path=self.path, recursive = False)
        self.observer.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
                
            
    def stop(self):
        self.observer.stop()
        self.observer.join()
    
class instructionHandler(FileSystemEventHandler):
    def __init__(self,controller,path, filename, function, *args, **kwargs):
        self.controller = controller
        self.path       = path
        self.filename   = filename
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
    
    def on_modified(self,event):
        if not event.is_directory and event.src_path.endswith(self.filename):
            self.function(self.args)
            
class sendCommandsClass(object):
    def __init__(self, controller, filepath, *args, **kwargs):
        self.controller = controller
        self.filepath   = filepath
        self.args       = args
        self.kwargs     = kwargs
        if not os.path.isfile(filepath):
            open(filepath, 'a').close()
        
    def moveStage(self, x,y,z):
        self.writeCommand('moveXYZ', x,y,z)
        
    def grabOneStack(self):
        self.writeCommand('grabOneStack')
        
    def setZoom(self,zoom):
        self.writeCommand('setZoom', zoom)
        
    def doUncaging(self):
        self.writeCommand('runUncaging')
        
    def getFOVsize(self):
        self.writeCommand('getFOV_xy')
        
    def writeCommand(self,*args):
        command = ",".join([str(x) for x in args])
        if verbose:
            print('\nWriting Command {0}\n'.format(command))
        with open(self.filepath, "a") as f:
            f.write('\n'+command)
            
    def getCurrentPosition(self):
        self.writeCommand('getCurrentPosition','xyz')

class getCommandsClass(object):
    def __init__(self, controller, filepath, *args, **kwargs):
        self.controller = controller
        self.instructions = controller.instructions
        self.filepath = filepath
        if not os.path.isfile(self.filepath):
            open(self.filepath, 'a').close()
    
    def readNewInstructions(self, *args, **kwargs):
        instLen = len(self.instructions)
        """read every line, see if there's new stuff to be had"""
        with open(self.filepath) as f:
            content = f.readlines()
            content = [x.strip() for x in content]
        ii = 0
        for line in content:
            if len(line) > 0:
                ii += 1
            if ii > instLen:
                if verbose:
                    print('\nnew line {0}\n'.format(ii))
                    print('\nnew instructions received\n')
                    print('\n{0}\n'.format(line))
                self.instructions.append(line)
                self.controller.instructions_in_queue.put(line) #add to queue to handle lots of stuff to do    
        """once file is read, run everything from queue"""
        """i guess i already have a second loop so this is redundant but whatever"""    
        while not self.controller.instructions_in_queue.empty():
            line = self.controller.instructions_in_queue.get()
            self.translateInputCode(line)    
                               
    def translateInputCode(self,line):

        def checkNumArgs(args,minArgs,maxArgs):
            if args == None:
                lenArgs = 0
            else:
                lenArgs = len(args)
            if minArgs <= lenArgs <= maxArgs:
                return(True)
            else:
                print('Error - Missing arguments. Expected between {0} and {1}. Got {2}'.format(minArgs,maxArgs,lenArgs))
                return(False)
        #split command and arguments by comma
        lineParts = line.split(',')
        command = lineParts[0]
        #make command lowercase to avoid errors
        command = command.lower()
        if len(lineParts) > 1:
            args = lineParts[1:]
        if command == 'grabfinished':
            """no args"""
            print('grabfinisheeddddd yeah')
        elif command == 'stagemovedone':
            self.stageMoveDone = True
            checkNumArgs(args,3,3)
            x,y,z = [float(args[xyz]) for xyz in [0,1,2]]
            if verbose:
                print('\nStage Moved to x= {0} , y = {1}, z = {2}\n'.format(x,y,z))
        elif command == 'grabonestackdone':
            self.grabOneStackDone = True
            #commands need to be separated by commas, not spaces, otherwise file paths will cause problems
            checkNumArgs(args,1,1)
            self.controller.imageFilePath = args[0]
        elif command == 'currentposition':
            checkNumArgs(args,3,3)
            x,y,z = [float(args[xyz]) for xyz in [0,1,2]]
            self.controller.currentCoordinates = [x,y,z]
            self.positionGrabDone = True
        elif command == 'uncagingdone':
            checkNumArgs(args,0,0)
            self.uncagingDone = True        
        elif command == 'fovXY_um':
            checkNumArgs(args,2,2)
            X,Y = [float(args[XY]) for XY in [0,1]]
            self.settings['fovXY'] = [X,Y]
        elif command == 'zoom':
            checkNumArgs(args,1,1)
            self.currentZoom = float(args[0])
        else:
            print("COMMAND NOT UNDERSTOOD")
            
        
        
    def waitForStageMoveDone(self):
        if verbose:
            print('\nWaiting for Stage Move Completion\n')
        while True:
#            time.sleep(.05)
            self.controller.update()
            if self.stageMoveDone:
                print('Stage Move Done')
                break
              
    def waitForGrabDone(self):
        if verbose:
            print('\nWaiting for Grab to be Finished\n')
        while True:
            self.controller.update()

#            time.sleep(.05)
            if self.grabOneStackDone:
                print('\nGrab One Stack Done\n')
                break
            
    def waitForCurrentPosition(self):
        if verbose:
            print('\nWaiting for Current Position\n')
        while True:
            self.controller.update()
#            time.sleep(.05)
            if self.positionGrabDone:
                print('\nGrab One Stack Done\n')
                break

    def waitForUncagingDone(self):
        if verbose:
            print('\nWaiting for Uncaging to be Complete\n')
        while True:
            self.controller.update()

#            time.sleep(.05)
            if self.uncagingDone:
                print('\nUncaging Done\n')
                break
            
            
class MacroWindow(tk.Tk):
    def __init__(self, controller, *args, **kwargs):      
        tk.Tk.__init__(self, *args, **kwargs) #initialize regular Tk stuff
        
        #set properties for main window
        tk.Tk.wm_title(self, "Macro View")
        tk.Tk.geometry(self, newGeometry = '700x700+200+200')
        #define container for what's in the window
        self.controller = controller
        self.addScrollingFigure()
        self.scale_z = tk.Scale(self.frame_canvas, orient = tk.VERTICAL)
        self.scale_z.grid(row = 0, column = 2, sticky = 'ns')
        frame_buttons = ttk.Frame(self)
        frame_buttons.grid(row = 1, column = 0, sticky = 'nsew')
        button_loadMacroImage = ttk.Button(frame_buttons,text = "Load Test Macro Image", command = 
                            lambda: self.loadMacroImage())
        button_loadMacroImage.grid(row = 0, column = 0, padx = 10, pady = 10, sticky = 'nw')
        label_macroZoom = tk.Label(frame_buttons, text = "Macro Zoom", font=LARGE_FONT)
        label_macroZoom.grid(row = 0, column = 1, sticky = 'nw', padx = 10, pady = 10)
        self.macroZoom= tk.StringVar(self)
        entry_macroZoom = ttk.Entry(frame_buttons, textvariable = self.macroZoom, width = 3)
        entry_macroZoom.grid(row = 0, column = 2, padx = 10, pady = 10, sticky = 'nw')             
        self.macroZoom.set(1)
        self.scale_zoom = tk.Scale(self, orient = tk.HORIZONTAL)
        self.scale_zoom.grid(row = 2, column = 0, sticky = 'ew')
        self.scale_zoom.config(command = self.changeSize, from_=.1, to=5, resolution = .1)
        self.scale_zoom.set(2)        
        
    def addScrollingFigure(self):
        self.frame_canvas = ttk.Frame(self)
        self.frame_canvas.grid(row = 0, column = 0, sticky = 'nsew')
        self.scrollingCanvas = ScrolledCanvas(self.frame_canvas, self, self.controller)

        
    def changeSize(self, *args):
        try:
            self.image
        except:
            return    
        self.scrollingCanvas.setImage()
        
    def loadMacroImage(self):
        if simulation:
            self.image=Image.open("../testing/macroImage.tif")
        self.multi_slice_viewer()
        
    def multi_slice_viewer(self):
        
        self.scale_z.config(command = self.scaleCallback, from_=0, to=self.image.n_frames-1)
        self.sliceIndex = self.image.n_frames//2
        self.scale_z.set(self.sliceIndex)
        self.scrollingCanvas.setImage()

    def scaleCallback(self,event):
        self.sliceIndex = self.scale_z.get()
        self.scrollingCanvas.setImage()
        
    def addPositionOnImageClick(self,x,y,z):
        # translate to normal coordinates
        fovX,fovY = self.controller.settings['fovXY']
        # xy currently originate from top left of image. 
        # translate them to coordinate plane directionality.
        # also, make them originate from center
        xyz_clicked = {'x':x, 'y':y, 'z':z}
        x = x - .5
        y = -y + .5
        #translate coordinates to µm
        x = x * fovX
        y = y * fovY
        #add coordinates to position table
        print('x, y, z = {0}, {1}, {2}'.format(x,y,z))
        xyz = {'x':x, 'y':y, 'z':z}
        self.getRefImageFromMacro(xyz_clicked)
        self.controller.addPosition(self.controller.frames[PositionsPage], xyz = xyz, refImages = self.refImages)
        
    def getRefImageFromMacro(self,xyz_clicked):
        macroZoom = float(self.macroZoom.get())
        imagingZoom = float(self.controller.frames[PositionsPage].imagingZoom.get())
        refZoom = float(self.controller.frames[PositionsPage].refZoom.get())
        imagingSlices = int(self.controller.frames[PositionsPage].imagingSlices.get())
        refSlices = int(self.controller.frames[PositionsPage].refSlices.get())
        
        frame = self.sliceIndex
        imagingSlices_ind = range(int(round_math(frame-imagingSlices/2)),int(round_math(frame+imagingSlices/2)))
        refSlices_ind = range(int(round_math(frame-refSlices/2)),int(round_math(frame+refSlices/2)))
        
        
        height, width = self.image.size
        boxX_imaging = width/imagingZoom*macroZoom
        boxY_imaging = height/imagingZoom*macroZoom
        boxX_ref = width/refZoom*macroZoom
        boxY_ref = height/refZoom*macroZoom
        x_clicked_pixel = width * xyz_clicked['x']
        y_clicked_pixel = height * xyz_clicked['y']
        xIndex_imaging = np.s_[int(round_math(x_clicked_pixel - boxX_imaging/2)) : int(round_math(x_clicked_pixel + boxX_imaging/2))] 
        yIndex_imaging = np.s_[int(round_math(y_clicked_pixel - boxY_imaging/2)) : int(round_math(y_clicked_pixel + boxY_imaging/2))] 
        xIndex_ref = np.s_[int(round_math(x_clicked_pixel - boxX_ref/2)) : int(round_math(x_clicked_pixel + boxX_ref/2))] 
        yIndex_ref = np.s_[int(round_math(y_clicked_pixel - boxY_ref/2)) : int(round_math(y_clicked_pixel + boxY_ref/2))] 

#        image = np.array(self.image.size)        
        #get maximum projection of image
        image = np.array(self.image)
        image_imaging_max = image[yIndex_imaging,xIndex_imaging]
        image_ref_max = image[yIndex_ref,xIndex_ref]
        for i in imagingSlices_ind:
            self.image.seek(i)
            image = np.array(self.image)
            image_imaging_max = np.max(np.dstack([image[yIndex_imaging,xIndex_imaging],image_imaging_max]), axis = 2)
        for i in refSlices_ind:
            self.image.seek(i)
            image = np.array(self.image)
            image_ref_max = np.max(np.dstack([image[yIndex_ref,xIndex_ref],image_ref_max]),axis = 2)
            
#        image_ref = image[yIndex_ref,xIndex_ref]


#        image_imaging = image[yIndex_imaging,xIndex_imaging]
#        image_ref = image[yIndex_ref,xIndex_ref]
        self.refImages = {'imaging':image_imaging_max, 'ref':image_ref_max}
        
class ScrolledCanvas(tk.Frame):
    def __init__(self, parent, master, controller):
        tk.Frame.__init__(self, parent)
        self.grid(row = 0, column = 0)
        self.parent = parent
        self.controller = controller
        self.master = master
        canv = tk.Canvas(self, relief=tk.SUNKEN)
        canv.bind('<Button-3>', func = self.canvasRightClick)
        canv.config(width=600, height=600)
        canv.config(highlightthickness=0)
    
        sbarV = tk.Scrollbar(self, orient=tk.VERTICAL)
        sbarH = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        
        sbarV.config(command=canv.yview)
        sbarH.config(command=canv.xview)
    
        canv.config(yscrollcommand=sbarV.set)
        canv.config(xscrollcommand=sbarH.set)
        
        sbarV.grid(row = 0, column = 1, sticky = 'ns')
        sbarH.grid(row = 1, column = 0, sticky = 'ew')
        
        canv.grid(row = 0, column = 0, sticky = 'nsew')
        self.canvas = canv
        
        
    def canvasRightClick(self,event):
        # Create popup menu
        w,h = self.master.image.size
        canvas = event.widget
        x = canvas.canvasx(event.x) / (w*self.master.scale_zoom.get())
        y = canvas.canvasy(event.y) / (h*self.master.scale_zoom.get())
        if x > 1 or y >1:
            return
        z = self.master.sliceIndex
#            print('eventx, eventy = {0}, {1}'.format(event.x,event.y))
#            print(canvas.find_closest(x,y))
        self.popup = tk.Menu(self, tearoff = 0)
        self.popup.add_command(label = 'Add Position', command = lambda:self.master.addPositionOnImageClick(x,y,z))          
        #display the popup menu
        self.popup.post(event.x_root,event.y_root)
         
    def setImage(self):
        im = self.master.image
        frame = self.master.sliceIndex
        zoom = self.master.scale_zoom.get()
        width,height=im.size
        width_r = round(width*zoom); height_r = round(height*zoom)
        im.seek(frame) #move to appropriate frame
        #rescale to uint8 for accurate display in TkInter
        im_max = np.array(im).max()
        im = ImageMath.eval("float(a)", a= im)
        im = ImageMath.eval("convert(a/a_m * 255, 'L')", a= im, a_m = im_max)
        self.im_r = im.resize((width_r, height_r))
        self.canvas.config(scrollregion=(0,0,width_r,height_r))
        self.im2=ImageTk.PhotoImage(master= self.canvas, image = self.im_r)
        self.imgtag=self.canvas.create_image(0,0,anchor="nw",image=self.im2)

###################

app = SpineTracker()
#ani = animation.FuncAnimation(app.AFImageFig, app.animate, interval = 1000)

app.mainloop()

###################
#s = sendCommandsClass(app, '../instructions_output.txt')
