# -*- coding: utf-8 -*-
"""
Created on Thu Dec 14 14:51:15 2017

@author: mikeu
"""

import tkinter as tk
from PIL import Image, ImageTk

class MacroWindow(tk.Tk):
    def __init__(self, controller=None, *args, **kwargs):      
        tk.Tk.__init__(self, *args, **kwargs) #initialize regular Tk stuff
        tk.Tk.wm_title(self, "Macro View")
        tk.Tk.geometry(self, newGeometry = '600x700+200+200')
#        holderFrame = tk.Frame(self)
#        holderFrame.grid(row = 0, column = 0)
        scrollCanvas = ScrolledCanvas(self)
        
class ScrolledCanvas(tk.Frame):
        def __init__(self, parent=None):
            tk.Frame.__init__(self, parent)
            self.pack(expand=tk.YES, fill=tk.BOTH)
            self.master.title("blah blah")
            canv = tk.Canvas(self, relief=tk.SUNKEN)
            canv.config(width=600, height=600)
            #canv.config(scrollregion=(0,0,1000, 1000))
            #canv.configure(scrollregion=canv.bbox('all'))
            canv.config(highlightthickness=0)
        
            sbarV = tk.Scrollbar(self, orient=tk.VERTICAL)
            sbarH = tk.Scrollbar(self, orient=tk.HORIZONTAL)
            
            sbarV.config(command=canv.yview)
            sbarH.config(command=canv.xview)
        
            canv.config(yscrollcommand=sbarV.set)
            canv.config(xscrollcommand=sbarH.set)
            
            sbarV.pack(side=tk.RIGHT, fill=tk.Y)
            sbarH.pack(side=tk.BOTTOM, fill=tk.X)
            
            canv.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH)
            self.im=Image.open("../test/macroImage.tif")
            self.im = self.im.resize((2000,2000))
            width,height=self.im.size
            canv.config(scrollregion=(0,0,width,height))
            self.im2=ImageTk.PhotoImage(master= canv, image = self.im)
            self.imgtag=canv.create_image(0,0,anchor="nw",image=self.im2)
            
app = MacroWindow()