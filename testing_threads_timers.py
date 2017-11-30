# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 13:54:25 2017

@author: smirnovm
"""

import threading
import time

tLock = threading.Lock()


def timer(name, delay, repeat):
    print("timer: " +name + " started")
    tLock.acquire()
    print(name + " has acquired the lock")
    while repeat > 0:
        time.sleep(delay)
        print(name, ": ", str(time.ctime(time.time())))
        repeat -=1
    print(name + " is releasing the lock")
    tLock.release()
    print("Timer :" + name + " Completed")
    
def main():
    t1 = threading.Thread(target = timer, args = ("Timer1", 1, 5))
    t2 = threading.Thread(target = timer, args = ("Timer2", 2, 5))
    t1.start()
    t2.start()
    
    print("Main Complete")
    
if __name__ == '__main__':
    main()