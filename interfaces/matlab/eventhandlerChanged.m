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
    disp(line_split);
    commandQueue{end+1} = line_split;
end
fclose(fid);
translateNewCommands(); %this runs here so program doesn't wait to close file before running commands
end

function translateCommand(line_split)
% do sstuff
end