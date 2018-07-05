function configurationControls(callback, handle)
if nargin==1
    feval(callback)
else
    feval(callback,handle)
end

function pixelsPerLine_Callback(handle)
global state
cellsOfStrings = get(handle, 'String');
state.acq.pixelsPerLine = str2double(cellsOfStrings{get(handle,'value')});

function linesPerFrame_Callback(handle)
global state
state.acq.linesPerFrame = str2double(get(handle, 'string'));

function pbApplyConfig_Callback()