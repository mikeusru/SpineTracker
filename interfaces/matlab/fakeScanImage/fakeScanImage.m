function fakeScanImage()
%fakeScanImage runs to provide output data to SpineTracker as a testing
%environment

global state

[p,~,~] = fileparts(mfilename('fullpath'));
addpath(p);

state.acq.scanAngleMultiplierFast = 15;
state.acq.scanAngleMultiplierSlow = 15;

