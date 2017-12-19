function matlab_interface()
%Using System.IO.FileSystemWatcher class in the System Assembly to monitor
%changes to .txt file

%fileWatcherObject has to remain after function is complete to keep
%monitoring the file
global fileWatcherObject allCommands
allCommands = {}; %initialize cell list of commands
myfile = 'instructions_output.txt';
[parentdir,~,~] = fileparts(pwd);
[parentdir,~,~] = fileparts(parentdir);

%Set up file watcher object, start listening for changes in file
fileWatcherObject = System.IO.FileSystemWatcher(parentdir);
fileWatcherObject.Filter = myfile;
fileWatcherObject.EnableRaisingEvents = true;
addlistener(fileWatcherObject,'Changed',@eventhandlerChanged);
end