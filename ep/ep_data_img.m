clear; clc;
load('export/phys_shapeResp.mat','shapeResp')

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