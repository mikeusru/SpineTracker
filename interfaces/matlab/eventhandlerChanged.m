%Once a change has been detected in the text file, this function runs
%put code to read text file here
function eventhandlerChanged(source,arg)
%%This function runs every time the text file is changed
% disp('TXT file changed')
readNewInstructions(arg.FullPath.char)
end

function readNewInstructions(fullpath)
%%This functions reads the text file and adds new lines to the allCommands
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
    line_split = strsplit(line_text);
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
        case 'channelstobesaved'
        case 'parameterfilesaved'
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

% respond with StageMoveDone
end

function grabOneStack()
% Grab an image stack

% respond with AcquisitionDone
end

function setZoom(zoom)
% set zoom to new value

% respond with Zoom
end

function runUncaging()
% initiate uncaging

% respond with UncagingDone
end

function getCurrentPositions()
% request for current xyz position

% respond with CurrentPosition
end

function getFOV_xy()
% request FOV size in �m, in x and y

% respond with fov_XY_um
end