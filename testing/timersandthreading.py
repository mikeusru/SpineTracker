# -*- coding: utf-8 -*-
"""
Created on Wed Nov  1 13:31:09 2017

@author: smirnovm
"""

import threading
import time
import datetime

print_lock = threading.Lock()

def hello(step,posID):
    print_lock.acquire()
    time.sleep(.0001)
    if step['EX']:
        ex = 'Exclusive'
    else:
        ex = 'Non-Exclusive'
    
    print('{0} {1} Timer {2} running at {3}s '.format(ex, step['imaging_or_uncaging'], posID, datetime.datetime.now().second))
    time.sleep(.2)
#    print(name + ' has aquired the lock')
#    print('oh herro')
    print_lock.release()
#    print(name + ' has released lock')
#for i in range(0,10):
#    t = threading.Timer(i,hello,[i,'timer1'])
#    t2 = threading.Timer(i,hello,[i,'timer2'])
#    t.start()
#    t2.start()

#==============================================================================
#individualSteps = app.individual_timeline_steps
#==============================================================================


#==============================================================================
# 

#     
#==============================================================================
class PositionTimer(object):
    def __init__(self,steps,function,*args,**kwargs):
        self._timer     = None
        self.steps      = steps
        self.function   = function
        self.args       = args
        self.kwargs     = kwargs
        self.is_running = False
        self.stepCount  = 0
        
        self.runTimes = []
        for step in self.steps:
            self.runTimes.append(step['start_time'])

        self.start()
        
    def _run(self, stepCount):
        self.is_running = False
        if stepCount < len(self.runTimes):
            self.start() #starts next timer countdown before running function
        self.function(self.steps[stepCount],*self.args, **self.kwargs)

        
    def start(self):
        if not self.is_running:
            if self.stepCount == 0:
                prevTime = 0
            else:
                prevTime = self.runTimes[self.stepCount-1]
            interval = self.runTimes[self.stepCount] - prevTime
            stepCount = self.stepCount
            self.stepCount += 1
            self._timer = threading.Timer(interval,self._run,args=[stepCount])
            self._timer.start()
            self.is_running = True
            
    def stop(self):
        self._timer.cancel()
        self.is_running = False
          
posTimers = {}
for key in individualSteps:
    timerName = 'posTimer' + str(key)
    posTimers[key] = PositionTimer(individualSteps[key],hello,key)
    
try:
    time.sleep(20)
finally:
    for key in posTimers:
        posTimers[key].stop()