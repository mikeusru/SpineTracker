function write_to_SpineTracker(varargin)
% write_to_SpineTracker will convert any input arguments into a single
% string, format it properly, and write it to the SpineTracker
% instructions_input.txt file
myfile = 'instructions_input.txt';
[parentdir,~,~] = fileparts(pwd);
[parentdir,~,~] = fileparts(parentdir);

filepath = fullfile(parentdir,myfile);

%create line of text to write
for i = 1:nargin
    if ~ischar(varargin{i})
        varargin{i} = num2str(varargin{i});
    end
end
%create comma-delimited string followed by linebreak
line_to_write = sprintf('%s,',string(varargin));
line_to_write = sprintf('%s\n',line_to_write(1:end-1));

%open file
fileID = fopen(filepath,'a');
%write line
fprintf('Writing Line: %s',line_to_write);
fprintf(fileID, '%s', line_to_write);
%close file
fclose(fileID);