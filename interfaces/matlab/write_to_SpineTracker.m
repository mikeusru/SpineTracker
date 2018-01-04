function write_to_SpineTracker(varargin)
% write_to_SpineTracker will convert any input arguments into a single
% string, format it properly, and write it to the SpineTracker
% instructions_input.txt file
myfile = 'instructions_input.txt';
[parentdir,~,~] = fileparts(pwd);
[parentdir,~,~] = fileparts(parentdir);

filepath = fullfile(parentdir,myfile);

%create line of text to write
line_to_write = '';
for i = 1:nargin
    var = varargin{i};
    if ~ischar(var)
        var = num2str(var);
    end
    line_to_write = sprintf('%s ', line_to_write, var);
end
line_to_write = sprintf('%s\n',line_to_write);

%open file
fileID = fopen(filepath,'a');
%write line
fprintf(fileID, line_to_write);
%close file
fclose(fileID);