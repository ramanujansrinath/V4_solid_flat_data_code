% This script generates the image for any stimulus - 3d or 2d
% It loads the data file, gets the details of the stimulus, and calls the
% java executable that generates the image. The spec and image are
% temporarily stored in the export folder.
% Note: The java executables have been tested for JDK 8 and below.

clear; clc;
load('export/phys_shapeResp_4.mat','shapeResp')

imgId = 1;
fore_color = ceil(shapeResp(imgId).col);
contrast = max(shapeResp(imgId).col);
tex = shapeResp(imgId).tex;

fid = fopen('export/999_spec.xml','w');
fwrite(fid,shapeResp(imgId).spec);
fclose(fid);

regenStr = ['java -Djava.library.path=' pwd '/imgGen/macos -jar ' ...
    pwd '/imgGen/genImage.jar '  pwd '/export/ 999 ' tex ' ' num2str(contrast) ' ' num2str(fore_color)];
system(regenStr);

imshow('export/999.png');