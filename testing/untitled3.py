# -*- coding: utf-8 -*-
"""
Created on Fri Oct 20 14:28:58 2017

@author: smirnovm
"""

"""
Creates a simple Gantt chart
Adapted from https://bitbucket.org/DBrent/phd/src/1d1c5444d2ba2ee3918e0dfd5e886eaeeee49eec/visualisation/plot_gantt.py
BHC 2014
"""
 
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.dates
from matplotlib.dates import MONTHLY, DateFormatter, rrulewrapper, RRuleLocator
 
from pylab import *
 
def create_date(month,year):
    """Creates the date"""
     
    date = dt.datetime(int(year), int(month), 1)
    mdate = matplotlib.dates.date2num(date)
     
    return mdate
 
# Data
 
pos = arange(0.5,5.5,0.5)
 
ylabels = []
ylabels.append('Hardware Design & Review')
ylabels.append('Hardware Construction')
ylabels.append('Integrate and Test Laser Source')
ylabels.append('Objective #1')
ylabels.append('Objective #2')
ylabels.append('Present at ASMS')
ylabels.append('Present Data at Gordon Conference')
ylabels.append('Manuscripts and Final Report')
 
effort = []
effort.append([0.2, 1.0])
effort.append([0.2, 1.0])
effort.append([0.2, 1.0])
effort.append([0.3, 0.75])
effort.append([0.25, 0.75])
effort.append([0.3, 0.75])
effort.append([0.5, 0.5])
effort.append([0.7, 0.4])
 
customDates = []
customDates.append([create_date(5,2014),create_date(6,2014)])
customDates.append([create_date(6,2014),create_date(8,2014),create_date(8,2014)])
customDates.append([create_date(7,2014),create_date(9,2014),create_date(9,2014)])
customDates.append([create_date(10,2014),create_date(3,2015),create_date(3,2015)])
customDates.append([create_date(2,2015),create_date(6,2015),create_date(6,2015)])
customDates.append([create_date(5,2015),create_date(6,2015),create_date(6,2015)])
customDates.append([create_date(6,2015),create_date(7,2015),create_date(7,2015)])
customDates.append([create_date(4,2015),create_date(8,2015),create_date(8,2015)])
 
task_dates = {}
for i,task in enumerate(ylabels):
    task_dates[task] = customDates[i]
# task_dates['Climatology'] = [create_date(5,2014),create_date(6,2014),create_date(10,2013)]
# task_dates['Structure'] = [create_date(10,2013),create_date(3,2014),create_date(5,2014)]
# task_dates['Impacts'] = [create_date(5,2014),create_date(12,2014),create_date(2,2015)]
# task_dates['Thesis'] = [create_date(2,2015),create_date(5,2015)]
 
# Initialise plot
 
fig = plt.figure()
# ax = fig.add_axes([0.15,0.2,0.75,0.3]) #[left,bottom,width,height]
ax = fig.add_subplot(111)
 
# Plot the data
 
start_date,end_date = task_dates[ylabels[0]]
ax.barh(0.5, end_date - start_date, left=start_date, height=0.3, align='center', color='blue', alpha = 0.75)
ax.barh(0.45, (end_date - start_date)*effort[0][0], left=start_date, height=0.1, align='center', color='red', alpha = 0.75, label = "PI Effort")
ax.barh(0.55, (end_date - start_date)*effort[0][1], left=start_date, height=0.1, align='center', color='yellow', alpha = 0.75, label = "Student Effort")
for i in range(0,len(ylabels)-1):
    labels = ['Analysis','Reporting'] if i == 1 else [None,None]
    start_date,mid_date,end_date = task_dates[ylabels[i+1]]
    piEffort, studentEffort = effort[i+1]
    ax.barh((i*0.5)+1.0, mid_date - start_date, left=start_date, height=0.3, align='center', color='blue', alpha = 0.75)
    ax.barh((i*0.5)+1.0-0.05, (mid_date - start_date)*piEffort, left=start_date, height=0.1, align='center', color='red', alpha = 0.75)
    ax.barh((i*0.5)+1.0+0.05, (mid_date - start_date)*studentEffort, left=start_date, height=0.1, align='center', color='yellow', alpha = 0.75)
# ax.barh((i*0.5)+1.0, end_date - mid_date, left=mid_date, height=0.3, align='center',label=labels[1], color='yellow')
 
# Format the y-axis
 
locsy, labelsy = yticks(pos,ylabels)
plt.setp(labelsy, fontsize = 14)
 
# Format the x-axis
 
ax.axis('tight')
ax.set_ylim(ymin = -0.1, ymax = 4.5)
ax.grid(color = 'g', linestyle = ':')
 
ax.xaxis_date() #Tell matplotlib that these are dates...
 
rule = rrulewrapper(MONTHLY, interval=1)
loc = RRuleLocator(rule)
formatter = DateFormatter("%b '%y")
 
ax.xaxis.set_major_locator(loc)
ax.xaxis.set_major_formatter(formatter)
labelsx = ax.get_xticklabels()
plt.setp(labelsx, rotation=30, fontsize=12)
 
# Format the legend
 
font = font_manager.FontProperties(size='small')
ax.legend(loc=1,prop=font)
 
# Finish up
ax.invert_yaxis()
fig.autofmt_xdate()
#plt.savefig('gantt.svg')
plt.show()