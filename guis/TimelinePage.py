import tkinter as tk
from tkinter import ttk
import matplotlib
import numpy as np
from utilities.helper_functions import fitFigToCanvas
from utilities.math_helpers import floatOrZero, floatOrNone
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import patches
import pickle
matplotlib.use("TkAgg")

class TimelinePage(ttk.Frame):
    name = 'Timeline'

    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.bind("<Visibility>", self.on_visibility)
        self.controller = controller
        tFrame = TimelineStepsFrame(self, controller)
        tFrame.grid(row=0, column=0, columnspan=1)
        canvas1 = FigureCanvasTkAgg(controller.f_timeline, self)
        canvas1.get_tk_widget().config(borderwidth=1, background='gray', highlightcolor='gray',
                                       highlightbackground='gray')
        canvas1.show()
        canvas1.get_tk_widget().grid(row=2, column=0, columnspan=2,
                                     padx=10, pady=10, sticky='nsew')
        self.canvas_timeline = canvas1
        self.tFrame = tFrame

        timelineTableFrame = ttk.Frame(self)
        timelineTableFrame.grid(row=0, column=1, padx=10, pady=10)
        self.createTimelineTable(timelineTableFrame)
        self.drawTimelineSteps()

    def createTimelineTable(self, container):
        tree = ttk.Treeview(container)
        tree["columns"] = ("sn", "iu", 'ex', "p", "d")
        tree.column("#0", width=30)
        tree.column("sn", width=120)
        tree.column("iu", width=60)
        tree.column("ex", width=60)
        tree.column("p", width=60)
        tree.column("d", width=75)
        tree.heading("#0", text='#')
        tree.heading("sn", text="Step")
        tree.heading("iu", text="Type")
        tree.heading("ex", text="Exclusive")
        tree.heading("p", text="Period (s)")
        tree.heading("d", text="Duration (m)")
        tree.bind("<Button-3>", self.onTimelineTableRightClick)
        tree.bind("<<TreeviewSelect>>", self.onTimelineTableSelect)
        tree.grid(row=0, column=0, sticky='nsew')
        scroll = ttk.Scrollbar(container, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky='nse', pady=10)
        tree.configure(yscrollcommand=scroll.set)
        self.timelineTree = tree

    def on_visibility(self, event):
        fitFigToCanvas(self.controller.f_timeline, self.canvas_timeline, self.controller.get_app_param('fig_dpi'))
        #        h = self.canvas_timeline.get_tk_widget().winfo_height()
        #        w = self.canvas_timeline.get_tk_widget().winfo_width()
        #        f_timeline.set_size_inches(w/fig_dpi,h/fig_dpi)
        self.canvas_timeline.draw_idle()
        self.create_timeline_chart()

    def create_timeline_chart(self, *args):
        timelineSteps = self.controller.timelineSteps
        positions = self.controller.positions
        stagger = floatOrZero(self.tFrame.staggerEntryVar.get())

        if len(timelineSteps) == 0:
            return
        if len(positions) == 0:
            positions = {1: [], 2: [], 3: [], 4: [], 5: []}
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
                    P = D * 60
                stepStartTimes = np.arange(startTime, startTime + D, P / 60)
                stepEndTimes = stepStartTimes + P / 60
                stepStartEnd = np.array([stepStartTimes, stepEndTimes])
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
                startEnd = pos_timeline[pos][0][0][:, 0]  # figure out which thing is set to start next
                posInd = list(posIDs).index(pos)
                S = max(startEnd[0], minTime[posInd])
                E = S + startEnd[1] - startEnd[0]
                EX = timelineSteps[timelineIndex[pos]]['EX']
                if S < startTime or (
                        S == startTime and EX):  # figure out if this is the earliest step, or exclusive step that starts the same time as others
                    startTime = S
                    endTime = E
                    firstPos = pos  # save which position runs first
            posInd = list(posIDs).index(firstPos)
            EX = timelineSteps[timelineIndex[firstPos]]['EX']

            individualSteps[firstPos].append({'startTime': startTime,
                                              'endTime': endTime,
                                              'EX': EX,
                                              'IU': timelineSteps[timelineIndex[firstPos]]['IU']})
            # delete added position
            pos_timeline[firstPos][0] = np.array([np.delete(pos_timeline[firstPos][0][0], 0, 1)])
            if EX:
                minTime[minTime < endTime] = endTime
            else:
                minTime[posInd] = max(minTime[posInd], endTime)
                minTime[minTime < startTime] = startTime

            # if this step is done, move to next step
            if pos_timeline[firstPos][0].size == 0:
                timelineIndex[firstPos] += 1
                del (pos_timeline[firstPos][0])
            # if this position is done, remove it
            if len(pos_timeline[firstPos]) == 0:
                del (pos_timeline[firstPos])
            if len(pos_timeline) == 0:
                break
            backup += 1
            if backup > 100000:  # make sure loop doesn't run forever while testing
                print('loop running too long')
                break

        self.controller.a_timeline.clear()
        yInd = 0
        for key in individualSteps:
            yrange = (yInd - .4, 0.8)
            xranges = []
            c = []
            yInd += 1
            for step in individualSteps[key]:
                xranges.append((step['startTime'], step['endTime'] - step['startTime']))
                if not step['EX']:
                    c.append('blue')  # regular imaging
                elif step['EX'] and step['IU'] == 'Image':
                    c.append('green')  # exclusive imaging
                else:
                    c.append('red')  # uncaging
            self.controller.a_timeline.broken_barh(xranges, yrange, color=c, edgecolor='black')
        self.controller.a_timeline.set_yticks(list(range(len(posIDs))))
        self.controller.a_timeline.set_yticklabels(ylabels1)
        self.controller.a_timeline.axis('tight')
        self.controller.a_timeline.set_ylim(auto=True)
        self.controller.a_timeline.grid(color='k', linestyle=':')
        y1, y2 = self.controller.a_timeline.get_ylim()
        if y2 > y1:
            self.controller.a_timeline.invert_yaxis()
        legendPatchRed = patches.Patch(color='red', label='Uncaging')
        legendPatchBlue = patches.Patch(color='blue', label='Imaging')
        legendPatchGreen = patches.Patch(color='green', label='Exclusive Imaging')
        self.controller.a_timeline.legend(handles=[legendPatchRed, legendPatchBlue, legendPatchGreen])
        self.controller.individualTimelineSteps = individualSteps
        self.canvas_timeline.draw_idle()

    #        app.frames[TimelinePage].canvas.draw_idle()

    def onTimelineTableRightClick(self, event):
        tree = self.timelineTree
        iid = tree.identify_row(event.y)
        if iid:
            # mouse over item
            tree.selection_set(iid)
        for item in tree.selection():
            item_text = tree.item(item, "text")
            item_number = tree.index(item)
            print(item_text)
            print(item_number)
        if len(tree.selection()) == 0:
            return
        self.popup = tk.Menu(self, tearoff=0)
        self.popup.add_command(label="Insert Step", command=lambda: self.insertTimelineStep(item_number))
        self.popup.add_command(label="Delete Step", command=lambda: self.deleteTimelineStep(item_number))
        self.popup.post(event.x_root, event.y_root)

    def insertTimelineStep(self, ind):
        self.tFrame.addStepCallback(self.controller, ind)
        self.drawTimelineSteps()
        self.backupTimeline()

    def deleteTimelineStep(self, ind):
        del self.controller.timelineSteps[ind]
        self.drawTimelineSteps()
        self.backupTimeline()

    def onTimelineTableSelect(self, event):
        pass

    def drawTimelineSteps(self):
        tree = self.timelineTree
        timelineSteps = self.controller.timelineSteps
        # clear table first
        for i in tree.get_children():
            tree.delete(i)
        # add values to table
        ii = 1
        for stepDist in timelineSteps:
            SN = stepDist['SN']
            P = stepDist['P']
            D = stepDist['D']
            IU = stepDist['IU']
            EX = stepDist['EX']
            tree.insert("", ii, text=str(ii), values=(SN, IU, EX, P, D))
            ii += 1

        self.create_timeline_chart()

    def backupTimeline(self):
        timelineSteps = self.controller.timelineSteps
        pickle.dump(timelineSteps, open(self.controller.get_app_param('initDirectory') + 'timelineSteps.p', 'wb'))

class TimelineStepsFrame(ttk.Frame):
    def __init__(self, parent, controller):
        ttk.Frame.__init__(self, parent)
        self.controller = controller
        label1 = ttk.Label(self, text='Step Name:', font=self.controller.get_app_param('large_font'))
        label1.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.stepName = tk.StringVar(self)
        stepNameEntry = ttk.Entry(self, width=30, textvariable=self.stepName)
        stepNameEntry.grid(row=0, column=1, sticky='nw', padx=10, pady=10)

        self.image_uncage = tk.StringVar(self)
        self.image_uncage.set("Image")
        self.image_uncage.trace('w', self.imageInFromFrame)

        placeHolderFrame = ttk.Frame(self)
        placeHolderFrame.grid(row=1, column=1, columnspan=1, sticky='nw', pady=10)
        imageInfoFrame = ttk.Frame(placeHolderFrame)
        imageInfoFrame.pack(side='left', anchor='w')

        rb1 = ttk.Radiobutton(self, text='Image', variable=self.image_uncage,
                              value='Image')
        rb1.grid(row=1, column=0, sticky='nw', pady=10, padx=10)

        periodLabel1 = ttk.Label(imageInfoFrame, text='  Period: ', font=self.controller.get_app_param('large_font'))
        periodLabel1.pack(anchor='w', side='left')
        self.periodEntryVar = tk.StringVar(self)
        periodEntry = ttk.Entry(imageInfoFrame, width=4, textvariable=self.periodEntryVar)
        periodEntry.pack(anchor='w', side='left')
        periodLabel2 = ttk.Label(imageInfoFrame, text='sec, ', font=self.controller.get_app_param('large_font'))
        periodLabel2.pack(anchor='w', side='left')
        durationLabel1 = ttk.Label(imageInfoFrame, text='Duration: ', font=self.controller.get_app_param('large_font'))
        durationLabel1.pack(anchor='w', side='left')
        self.durationEntryVar = tk.StringVar(self)
        durationEntry = ttk.Entry(imageInfoFrame, width=4, textvariable=self.durationEntryVar)
        durationEntry.pack(anchor='w', side='left')
        durationLabel2 = ttk.Label(imageInfoFrame, text='min', font=self.controller.get_app_param('large_font'))
        durationLabel2.pack(anchor='w', side='left')

        rb2 = ttk.Radiobutton(self, text='Uncage', variable=self.image_uncage,
                              value='Uncage')
        rb2.grid(row=2, column=0, sticky='nw', padx=10, pady=3)

        self.exclusiveVar = tk.BooleanVar(self)
        exclusiveCB = ttk.Checkbutton(self, text='Exclusive', variable=self.exclusiveVar)
        exclusiveCB.grid(row=2, column=1, sticky='nw', padx=10, pady=3)
        staggerFrame = ttk.Frame(self)
        staggerFrame.grid(row=4, column=0, sticky='nw', columnspan=2)
        staggerLabel1 = ttk.Label(staggerFrame, text='Stagger: ', font=self.controller.get_app_param('large_font'))
        staggerLabel1.grid(row=0, column=0, sticky='nw', padx=10, pady=10)
        self.staggerEntryVar = tk.StringVar(self)
        try:
            self.staggerEntryVar.set(controller.settings['stagger'])
        except:
            pass
        self.staggerEntryVar.trace('w', parent.create_timeline_chart)
        staggerEntry = ttk.Entry(staggerFrame, width=4, textvariable=self.staggerEntryVar)
        staggerEntry.grid(row=0, column=1, sticky='nw', padx=0, pady=10)
        staggerLabel2 = ttk.Label(staggerFrame, text='min', font=self.controller.get_app_param('large_font'))
        staggerLabel2.grid(row=0, column=2, sticky='nw', padx=0, pady=10)

        button = ttk.Button(self, text="Add Step",
                            command=lambda: self.addStepCallback(controller))
        button.grid(row=3, column=0, padx=10, pady=10, sticky='wn')
        self.imageInfoFrame = imageInfoFrame

    def addStepCallback(self, cont, ind=None):
        # get values
        SN = self.stepName.get()
        P = floatOrNone(self.periodEntryVar.get())
        D = floatOrNone(self.durationEntryVar.get())
        IU = self.image_uncage.get()
        EX = self.exclusiveVar.get()
        cont.add_timeline_step({'SN': SN, 'IU': IU, 'EX': EX, 'P': P, 'D': D}, ind)
        # reset values
        self.stepName.set('')
        self.periodEntryVar.set('')
        self.durationEntryVar.set('')
        cont.frames[TimelinePage].backupTimeline()

    def imageInFromFrame(self, *args):
        var = self.image_uncage.get()
        if var == "Image":
            self.imageInfoFrame.pack(side='left', anchor='w')
            self.exclusiveVar.set(False)
        else:
            self.imageInfoFrame.pack_forget()
            self.exclusiveVar.set(True)
