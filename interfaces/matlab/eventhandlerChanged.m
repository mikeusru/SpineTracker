%Once a change has been detected in the text file, this function runs
%put code to read text file here
function eventhandlerChanged(source,arg)
% global test
% test.source = source
% test.arg = arg
disp('TXT file changed')
readNewInstructions(arg.FullPath.char)
end

function readNewInstructions(fullpath)
global allCommands commandQueue
fid = fopen(fullpath,'r');
ii = 0;
commandLen = length(allCommands);
while ~feof(fid)
    line = fgets(fid); %read line by line
    line = strtrim(line);
    if isempty(line)
        continue
    end
    ii = ii + 1;
    if ii <= commandLen
        continue
    end
    line_split = strsplit(line);
    allCommands{end+1} = line_split;
    commandQueue{end+1} = line_split;
end
fclose(fid);
translateNewCommands(); %this runs here so program doesn't wait to close file before running commands
end

function translateNewCommands()
global commandQueue
while ~isempty(commandQueue)
    command = commandQueue{1};
    commandQueue(1)=[];
    switch lower(command{1})
        case 'movexyz'
            disp('movexyz')
        case 'grabonestack'
            disp('grabonestack')
        case 'setzoom'
            disp('setzoom');
        case 'rununcaging'
            disp('rununcaging')
        case 'getcurrentposition'
            disp('getcurrentposition')
        case 'getfov_xy'
            disp('getfov_xy')
        otherwise
            disp('COMMAND NOT UNDERSTOOD')
    end
end
end