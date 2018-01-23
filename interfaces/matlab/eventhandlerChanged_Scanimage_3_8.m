%% This function runs every time the text file is changed
function eventhandlerChanged_Scanimage_3_8(source,arg)
% disp('TXT file changed')
readNewInstructions(arg.FullPath.char)
end

%% This functions reads the text file and adds new lines to the spineTracker.allCommands
function readNewInstructions(fullpath)
%%variable, and to the spineTracker.commandQueue
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
%%This function takes commands out of the spineTracker.commandQueue variable and sends them
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
global state
motorSetPositionAbsolute([str2double(x),str2double(y),str2double(z)],'verify');
% verify command makes it wait to read the position it moved to
% respond with StageMoveDone
[xyz] = state.motor.lastPositionSet;
write_to_SpineTracker('StageMoveDone',xyz(1),xyz(2),xyz(3))
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
write_to_SpineTracker('GrabOneStackDone',state.files.fullFileName);
end

function setZoom(zoom)
global state
% set zoom to new value
setZoomValue(str2double(zoom))
% respond with Zoom
write_to_SpineTracker('Zoom',state.acq.zoomFactor);
end

function runUncaging(roi_x,roi_y)
global gh state
% initiate uncaging
% set up ROI using process similar to yphys_makeRoi
%% Delete all current ROIs
for roiNum=1:length(gh.yphys.figure.yphys_roi)
    if ishandle(gh.yphys.figure.yphys_roi(roiNum))
        a=findobj('Tag', num2str(roiNum));
        delete(a);
    end
end
%% define new ROI
roiNum=1;
roisize = 6;
axes(state.internal.axis(1));
xlimit1 = get(state.internal.axis(1), 'Xlim');
ylimit1 = get(state.internal.axis(1), 'Ylim');
x_r = round(roisize*xlimit1(2)/128);
y_r = round(roisize*ylimit1(2)/128);

roiPosition = round([roi_x - x_r/2, roi_y - y_r/2, x_r, y_r]);
axes(state.internal.axis(1));

%% show ROI
axes(state.internal.axis(1));
gh.yphys.figure.yphys_roi(roiNum) = rectangle('Position', roiPosition, 'Curvature',[1, 1], 'EdgeColor', 'cyan', 'ButtonDownFcn', 'yphys_dragRoi', 'Tag', num2str(roiNum));
gh.yphys.figure.yphys_roiText(roiNum) = text(roiPosition(1)-3, roiPosition(2)-3, num2str(roiNum), 'Tag', num2str(roiNum), 'ButtonDownFcn', 'yphys_roiDelete');
set(gh.yphys.figure.yphys_roiText(roiNum), 'Color', 'Red');

axes(state.internal.axis(2));
gh.yphys.figure.yphys_roi2(roiNum) = rectangle('Position', roiPosition, 'Curvature',[1, 1], 'EdgeColor', 'cyan', 'ButtonDownFcn', 'yphys_dragRoi', 'Tag', num2str(roiNum));
gh.yphys.figure.yphys_roiText2(roiNum) = text(roiPosition(1)-3, roiPosition(2)-3, num2str(roiNum), 'Tag', num2str(roiNum), 'ButtonDownFcn', 'yphys_roiDelete');
set(gh.yphys.figure.yphys_roiText2(roiNum), 'Color', 'Red');

axes(state.internal.maxaxis(2));
gh.yphys.figure.yphys_roi3(roiNum) = rectangle('Position', roiPosition, 'Curvature',[1, 1], 'EdgeColor', 'cyan', 'ButtonDownFcn', 'yphys_dragRoi', 'Tag', num2str(roiNum));
gh.yphys.figure.yphys_roiText3(roiNum) = text(roiPosition(1)-3, roiPosition(2)-3, num2str(roiNum), 'Tag', num2str(roiNum), 'ButtonDownFcn', 'yphys_roiDelete');
set(gh.yphys.figure.yphys_roiText3(roiNum), 'Color', 'Red');

updateUAgui;
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
write_to_SpineTracker('CurrentPosition',xyz(1),xyz(2),xyz(3));
end

function getFOV_xy()
% request FOV size in µm, in x and y
% this should probably just be set in SpineTracker
% respond with fov_XY_um
write_to_SpineTracker('fov_XY_um',250,250);
end

function getScanAngleXY()
global state
% request Scan Angle measurements in X and Y
% respond with ScanAngleXY
write_to_SpineTracker('ScanAngleXY',state.acq.scanShiftFast,state.acq.scanShiftSlow);
end

function setScanAngleXY(scanShiftFast,scanShiftSlow)
global state
%set Scan Angle to be set
state.acq.scanShiftSlow = scanShiftSlow;
state.acq.scanShiftFast = scanShiftFast;
updateGUIByGlobal('state.acq.scanShiftSlow');
updateGUIByGlobal('state.acq.scanShiftFast');
setupAOData; %needed to reset scanning shift
%respond with ScanAngleXY
getScanAngleXY()
end

function getScanAngleMultiplier()
global state
% Request Scan Angle Multiplier, slow and fast
% Respond with ScanAngleMultiplier
write_to_SpineTracker('ScanAngleMultiplier',state.acq.scanAngleMultiplierFast,state.acq.scanAngleMultiplierSlow);
end

function getScanAngleRangeReference()
global state
% request Scan Angle Range Reference, slow and fast
% respond with ScanAngleRangeReference
write_to_SpineTracker('ScanAngleRangeReference',state.init.scanAngularRangeReferenceFast,state.init.scanAngularRangeReferenceSlow);
end

function setZSliceNum(z_slice_num)
global state gh
% set number of Z slices to image when grabbig stack
set(gh.motorControls.etNumberOfZSlices,'String',num2str(z_slice_num));
motorControls('etNumberOfZSlices_Callback',gh.motorControls.etNumberOfZSlices);
% respond with ZSliceNum
write_to_SpineTracker('ZSliceNum',state.acq.numberOfZSlices);
end