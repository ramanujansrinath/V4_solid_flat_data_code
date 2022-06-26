% This script is for internal purposes only.
% It lets me collate data from various sources and create a unified data
% file that contains the shape specifications and neural responses for each
% unit in V4 across monkeys. This file can then be used to generate all the
% stimuli and reproduce all analyses.

clear; clc;

projPath = '/Volumes/Supportboy/cold/Hopkins/monkey/prod/EP/projectMaskedGA3D';
load([projPath '/analysis/plots/population/ids.mat'],'population');
splits = 1:10:length(population);

monkeyNames = {'dobby' 'merri' 'gizmo'};
for jj=1:length(splits)-1
    sCount = 1;
    for ii=splits(jj):splits(jj+1)
        nGen = population(ii).nGen-population(ii).nPostHoc;
        for gg=1:nGen
            load([projPath '/stim/' monkeyNames{population(ii).monkeyId} '/' num2str(population(ii).prefix) '_r-' num2str(population(ii).runNum) '_g-' num2str(gg) '/stimParams.mat'])
            stimuli = stimuli'; stimuli = stimuli(:);
            for ss=1:length(stimuli)
                shapeResp(sCount).id = stimuli{ss}.id.descId;
                shapeResp(sCount).col = stimuli{ss}.shape.color;
                shapeResp(sCount).tex = stimuli{ss}.shape.texture;
                shapeResp(sCount).spec = stimuli{ss}.shape.mstickspec;
                shapeResp(sCount).x = stimuli{ss}.shape.x;
                shapeResp(sCount).y = stimuli{ss}.shape.y;
                shapeResp(sCount).s = stimuli{ss}.shape.s;
                shapeResp(sCount).resp = mean(stimuli{ss}.id.respMatrix);
                sCount = sCount+1;
            end
        end
    end

    save(['export/phys_shapeResp_' num2str(jj) '.mat'],'shapeResp')
end