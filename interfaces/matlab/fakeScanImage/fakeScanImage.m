function fakeScanImage()
%fakeScanImage runs to provide output data to SpineTracker as a testing
%environment

global state

[p,~,~] = fileparts(mfilename('fullpath'));
addpath(p);

state.acq.scanAngleMultiplierFast = 1;
state.acq.scanAngleMultiplierSlow = 1;
state.init.scanAngularRangeReferenceFast = 15;
state.init.scanAngularRangeReferenceSlow = 15;
state.motor.lastPositionRead = [0,0,0];
state.acq.scanShiftFast = 0;
state.acq.scanShiftSlow = 0;
state.acq.pixelsPerLine = 128;
state.acq.linesPerFrame = 128;
state.files.fullFileName = [p,'\..\..\..\test\test_image'];

createDummyGui;
createDummyRois;

function createDummyGui()
mainControls();

function createDummyRois()
global gh state
gh.yphys.figure.yphys_roi = [];
f1 = figure;
state.internal.axis = [];
state.internal.axis(1) = subplot(1,4,1, 'parent', f1, 'xlim', [0,128], 'ylim', [0,128]);
state.internal.axis(2) = subplot(1,4,2, 'parent', f1, 'xlim', [0,128], 'ylim', [0,128]);
state.internal.maxaxis(1) = subplot(1,4,3, 'parent', f1, 'xlim', [0,128], 'ylim', [0,128]);
state.internal.maxaxis(2) = subplot(1,4,4, 'parent', f1, 'xlim', [0,128], 'ylim', [0,128]);