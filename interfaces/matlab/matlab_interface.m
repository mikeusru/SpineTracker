function matlab_interface(reader_function)
%Using System.IO.FileSystemWatcher class in the System Assembly to monitor
%changes to .txt file

%fileWatcherObject has to remain after function is complete to keep
%monitoring the file

%reader_function indicates the function which is used to send commands to
%the program. 
%for testing, use @eventhandlerChanged_DUMMY
%for Scanimage, try @eventhandlerChanged_Scanimage_3_8

global fileWatcherObject allCommands

if nargin<1
    reader_function = @eventhandlerChanged_DUMMY
allCommands = {}; %initialize cell list of commands
myfile = 'instructions_output.txt';
[parentdir,~,~] = fileparts(pwd);
[parentdir,~,~] = fileparts(parentdir);

%Set up file watcher object, start listening for changes in file
fileWatcherObject = System.IO.FileSystemWatcher(parentdir);
fileWatcherObject.Filter = myfile;
fileWatcherObject.EnableRaisingEvents = true;
addlistener(fileWatcherObject,'Changed',reader_function);
end