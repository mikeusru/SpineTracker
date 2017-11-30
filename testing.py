# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 13:54:25 2017

@author: smirnovm
"""

from threading import Thread
import time

def timer(name, delay, repeat):
    print("timer: " +name + " started")
    while repeat > 0:
        time.sleep(delay)
        print(name, ": ", str(time.ctime(time.time())))
        repeat -=1
    print("Timer :" + name + " Completed")
    
def main():
    t1 = Thread(target = timer, args = ("Timer1", 1, 5))
    t2 = Thread(target = timer, args = ("Timer2", 2, 5))
    t1.start()
    t2.start()
    
    print("Main Complete")
    
if __name__ == '__main__':
    main()
    
#################

from PIL import Image
im = Image.open('../images/crab.jpg')


####
img = app.acq['imageStack']
img = np.max(img,0)