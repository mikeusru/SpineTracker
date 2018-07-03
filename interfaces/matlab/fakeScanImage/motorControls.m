function motorControls(callback,handle)
%UNTITLED12 Summary of this function goes here
%   Detailed explanation goes here
feval(callback, handle);

function etNumberOfZSlices_Callback(handle)
global state
state.acq.numberOfZSlices = str2double(get(handle,'string'));