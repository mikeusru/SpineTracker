%% This function runs every time the text file is changed
function eventhandlerChanged_DUMMY(source,arg)
% disp('TXT file changed')
readNewInstructions(arg.FullPath.char)
end

%% This functions reads the text file and adds new lines to the allCommands
function readNewInstructions(fullpath)
%%variable, and to the commandQueue
global spineTracker
fid = fopen(fullpath,'r');
ii = 0;
commandLen = length(spineTracker.allCommands);
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
    spineTracker.allCommands{end+1} = line_split;
    spineTracker.commandQueue{end+1} = line_split;
end
fclose(fid);
translateNewCommands(); %this runs here so program doesn't wait to close file before running commands
end

function translateNewCommands()
%%This function takes commands out of the commandQueue variable and sends them
%to their appropriate functions
global spineTracker
while ~isempty(spineTracker.commandQueue)
    command = spineTracker.commandQueue{1};
    spineTracker.commandQueue(1)=[];
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
            if checkArgCount([2,2],argCount)
                continue
            end
            roi_x = command(2);
            roi_y = command(3);
            runUncaging(roi_x,roi_y);
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
        case 'getscananglexy'
            disp('getScanAngleXY')
            if checkArgCount([0,0],argCount)
                continue
            end
            getScanAngleXY();
        case 'setscananglexy'
            disp('setScanAngleXY')
            if checkArgCount([2,2],argCount)
                continue
            end
            scanShiftFast = str2double(command(2));
            scanShiftSlow = str2double(command(3));
            setScanAngleXY(scanShiftFast,scanShiftSlow);
        case 'getscananglemultiplier'
            disp('getScanAngleMultiplier')
            if checkArgCount([0,0],argCount)
                continue
            end
            getScanAngleMultiplier();
        case 'getscananglerangereference'
            disp('getScanAngleRangeReference')
            if checkArgCount([0,0],argCount)
                continue
            end
            getScanAngleRangeReference();
        case 'setzslicenum'
            disp('getScanAngleRangeReference')
            if checkArgCount([1,1],argCount)
                continue
            end
            z_slice_num = str2double(command(2));
            setZSliceNum(z_slice_num);
            
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
pause(.1)
write_to_SpineTracker('StageMoveDone',x,y,z)
end

function grabOneStack()
% Grab an image stack
% respond with GrabOneStackDone
pause(.1)
write_to_SpineTracker('GrabOneStackDone','C:\Users\mikeu\Documents\Python Scripts\SpineTracker\testing\test_image.tif');
end

function setZoom(zoom)
% set zoom to new value
% respond with Zoom
zoom = str2double(zoom);
pause(.1)
write_to_SpineTracker('Zoom',zoom);
end

function runUncaging(roi_x,roi_y)
% initiate uncaging
% respond with UncagingDone
pause(.1)
write_to_SpineTracker('UncagingDone');
end

function getCurrentPosition()
% request for current xyz position
% respond with CurrentPosition
pause(.1)
xyz = [randi(250)-125,randi(250)-125,randi(50)-25];
write_to_SpineTracker('CurrentPosition',xyz(1),xyz(2),xyz(3));
end

function getFOV_xy()
% request FOV size in µm, in x and y
% this should probably just be set in SpineTracker
% respond with fov_XY_um
pause(.1)
write_to_SpineTracker('fov_XY_um',250,250);
end

function setScanAngleXY(scanShiftFast,scanShiftSlow)
pause(.1);
%set Scan Angle to be set
%respond with ScanAngleXY
write_to_SpineTracker('ScanAngleXY',scanShiftFast,scanShiftSlow);
end

function getScanAngleXY()
pause(0.1)
% request Scan Angle measurements in X and Y
% respond with ScanAngleXY
write_to_SpineTracker('ScanAngleXY',0,0);
end

function getScanAngleMultiplier()
% Request Scan Angle Multiplier, slow and fast
% Respond with ScanAngleMultiplier
write_to_SpineTracker('ScanAngleMultiplier',1,1);
end

function getScanAngleRangeReference()
% request Scan Angle Range Reference, slow and fast
% respond with ScanAngleRangeReference
write_to_SpineTracker('ScanAngleRangeReference',15,15);
end

function setZSliceNum(z_slice_num)
% set number of Z slices to image when grabbig stack
% respond with ZSliceNum
write_to_SpineTracker('ZSliceNum',z_slice_num);
end

function setXYresolution(x,y)
global state gh
% set pixel resolution to image
% respond with x_y_resolution
write_to_SpineTracker('x_y_resolution',x,y);
end

function getXYresolution()
global state gh
% read pixel resolution to image
% respond with x_y_resolution
write_to_SpineTracker('x_y_resolution',128,128);
end