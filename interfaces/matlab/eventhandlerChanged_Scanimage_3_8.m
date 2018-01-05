%% This function runs every time the text file is changed
function eventhandlerChanged_Scanimage_3_8(source,arg)
% disp('TXT file changed')
readNewInstructions(arg.FullPath.char)
end

%% This functions reads the text file and adds new lines to the allCommands
function readNewInstructions(fullpath)
%%variable, and to the commandQueue
global allCommands commandQueue
fid = fopen(fullpath,'r');
ii = 0;
commandLen = length(allCommands);
while ~feof(fid)
    line_text = fgets(fid); %read line by line
    line_text = strtrim(line_text);
    if isempty(line_text)
        continue
    end
    ii = ii + 1;
    if ii <= commandLen
        continue
    end
    line_split = strsplit(line_text,',');
    allCommands{end+1} = line_split;
    commandQueue{end+1} = line_split;
end
fclose(fid);
translateNewCommands(); %this runs here so program doesn't wait to close file before running commands
end

function translateNewCommands()
%%This function takes commands out of the commandQueue variable and sends them
%to their appropriate functions
global commandQueue
while ~isempty(commandQueue)
    command = commandQueue{1};
    commandQueue(1)=[];
    argCount = length(command) - 1;
    switch lower(command{1})
        case 'movexyz'
            disp('movexyz')
            if checkArgCount([3,3],argCount)
                continue
            end
            x = str2double(command(2));
            y = str2double(command(3));
            z = str2double(command(4));
            moveXYZ(x,y,z);
        case 'grabonestack'
            disp('grabonestack')
            if checkArgCount([0,0],argCount)
                continue
            end
            grabOneStack();
        case 'setzoom'
            disp('setzoom');
            if checkArgCount([1,1],argCount)
                continue
            end
            zoom = command(2);
            setZoom(zoom);
        case 'rununcaging'
            disp('rununcaging')
            if checkArgCount([0,0],argCount)
                continue
            end
            runUncaging();
        case 'getcurrentposition'
            disp('getcurrentposition')
            if checkArgCount([0,0],argCount)
                continue
            end
            getCurrentPosition();
        case 'getfov_xy'
            disp('getfov_xy')
            if checkArgCount([0,0],argCount)
                continue
            end
            getFOV_xy();
        otherwise
            disp('COMMAND NOT UNDERSTOOD')
    end
end
end

function status = checkArgCount(low_high, amount)
% return status = 0 if correct number of arguments, otherwise return 1
if amount < low_high(1) || amount > low_high(2)
    status = 1;
else
    status = 0;
end
if status == 1
    disp('WRONG NUMBER OF ARGUMENTS READ');
end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Functions sent to imaging program

function moveXYZ(x,y,z)
% move to new XYZ position
global state
motorSetPositionAbsolute([str2double(x),str2double(y),str2double(z)],'verify');
% verify command makes it wait to read the position it moved to
% respond with StageMoveDone
[xyz] = state.motor.lastPositionSet;
rst('StageMoveDone',xyz(1),xyz(2),xyz(3))
end

function grabOneStack()
% Grab an image stack
global gh state
mainControls('grabOneButton_Callback',gh.mainControls.grabOneButton);
try
    %wait until grab is complete
    waitfor(gh.mainControls.grabOneButton,'String','GRAB'); 
catch ME
    disp('Warning - waiting for grab didn''t work correctly');
    disp(ME.message);
end
% respond with GrabOneStackDone
% should make sure that this filename is taken at the correct time. might
% need to be done before taking the image
rst('GrabOneStackDone',state.files.fullFileName);
end

function setZoom(zoom)
global state
% set zoom to new value
setZoomValue(str2double(zoom))
% respond with Zoom
rst('Zoom',state.acq.zoomFactor);
end

function runUncaging()
global gh
% initiate uncaging
% simulate uncaging button press
yphys_stimScope('start_Callback',gh.yphys.stimScope.start); 
% respond with UncagingDone
% UncagingDone is written by either yphys_stimScope or yphys_stimLoop
end

function getCurrentPosition()
global state
% request for current xyz position
motorGetPosition();
xyz = state.motor.lastPositionRead;
% respond with CurrentPosition
rst('CurrentPosition',xyz(1),xyz(2),xyz(3));
end

function getFOV_xy()
% request FOV size in µm, in x and y
% this should probably just be set in SpineTracker
% respond with fov_XY_um
rst('fov_XY_um',250,250);
end

%% Respond to SpineTracker
function rst(varargin)
%this function is just code shorthand
write_to_SpineTracker(varargin)
end