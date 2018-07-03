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

function grabOneButton_Callback(handle)
global state
disp('imaging...');
set(handle, 'String', 'ABORT');
pause(.5);
print('done imaging...');
[p,~,~] = mfilename('fullpath');
state.files.fullFileName = [p,'\..\..\..\test\test_image.tif'];
set(handle, 'String', 'GRAB');

