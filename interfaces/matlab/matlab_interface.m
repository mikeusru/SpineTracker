function matlab_interface(start_stop, reader_function)
%Using System.IO.FileSystemWatcher class in the System Assembly to monitor
%changes to .txt file

%the start_stop variable tells the program whether to start or stop the
%listener. the variable should either say 'start' or 'stop'

%fileWatcherObject has to remain after function is complete to keep
%monitoring the file

%reader_function indicates the function which is used to send commands to
%the program. 
%for testing, use @eventhandlerChanged_DUMMY
%for Scanimage, try @eventhandlerChanged_Scanimage_3_8

global spineTracker

if nargin <1
    start_stop = 'start';
end

if strcmp(start_stop,'stop')
    delete(spineTracker.lh);
    return
end

if strcmp(start_stop,'reset')
    delete(spineTracker.lh);
end

if nargin<2
    reader_function = @eventhandlerChanged_Scanimage_3_8;
end

spineTracker.allCommands = {}; %initialize cell list of commands
spineTracker.commandQueue = {}; %initialize cell list of commands in queue
outfile = 'instructions_output.txt';
infile = 'instructions_input.txt';
[parentdir,~,~] = fileparts(mfilename('fullpath'));
[parentdir,~,~] = fileparts(parentdir);
[parentdir,~,~] = fileparts(parentdir);
commands_from_spine_tracker = fullfile(parentdir,outfile);
commands_to_spine_tracker = fullfile(parentdir,infile);
fid = fopen(commands_from_spine_tracker,'w');
fclose(fid);
spineTracker.commands_from_spine_tracker = commands_from_spine_tracker;
spineTracker.commands_to_spine_tracker = commands_to_spine_tracker;

%Set up file watcher object, start listening for changes in file
spineTracker.fileWatcherObject = System.IO.FileSystemWatcher(parentdir);
spineTracker.fileWatcherObject.Filter = outfile;
spineTracker.fileWatcherObject.EnableRaisingEvents = true;
spineTracker.lh = addlistener(spineTracker.fileWatcherObject,'Changed',reader_function);
