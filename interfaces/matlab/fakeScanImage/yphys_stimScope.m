function yphys_stimScope(callback,handle)
%UNTITLED6 Summary of this function goes here
%   Detailed explanation goes here
feval(callback, handle);

function start_Callback(handle)
disp('doing uncaging...');
pause(.5);
disp('done uncaging...');
write_to_SpineTracker('UncagingDone');

