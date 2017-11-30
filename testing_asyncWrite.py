# -*- coding: utf-8 -*-
"""
Created on Wed Oct 18 14:07:17 2017

@author: smirnovm
"""

import threading
import time

class AsyncWrite(threading.Thread):
    def __init__(self, text, out):
        threading.Thread.__init__(self)
        self.text = text
        self.out = out
    
    def run(self):
        f = open(self.out, "a")
        f.write(self.text + '\n')
        f.close()
        time.sleep(2)
        print("Finished Background File Write To " + self.out)
        
def Main():
    message = input("enter a string to store:")
    background = AsyncWrite(message, 'out.txt')
    background.start()
    print("The program can continue to run while it writes in another thread")
    print(100+400)
    
    background.join() # wait until thread is finished while resuming
    print ("waited until thread was complete")
    
if __name__ == '__main__':
    Main()