function mainControls(callbackString,handle)
%UNTITLED3 Summary of this function goes here
%   Detailed explanation goes here
if nargin < 1
    createGui();
else
    feval(callbackString, handle);
end

function createGui()
global gh
f = figure('Name','Fake Scanimage', 'NumberTitle', 'off', 'menu', 'none');
gh.mainControls.grabOneButton = uicontrol('Parent', f, 'position', [5 5 50 50],'Style','Pushbutton', 'String', 'GRAB');
gh.motorControls.etNumberOfZSlices = uicontrol('Parent', f, 'position', [55 55 50 50], 'Style','Edit', 'String', '3');
gh.configurationControls.linesPerFrame = uicontrol('Parent', f, 'position', [110 165 50 50], 'Style','Edit', 'String', '128');
gh.configurationControls.pixelsPerLine = uicontrol('Parent', f, 'position', [110 110 50 50], 'Style','popup', 'String', {'64','128','512','1024'}, 'value', 2);

function grabOneButton_Callback(handle)
global state
disp('imaging...');
set(handle, 'String', 'ABORT');
pause(.5);
print('done imaging...');
[p,~,~] = fileparts(mfilename('fullpath'));
state.files.fullFileName = [p,'\..\..\..\test\test_image'];
set(handle, 'String', 'GRAB');

