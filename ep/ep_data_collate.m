clear; clc;

projPath = '/Volumes/Supportboy/cold/Hopkins/NHP/prod/EP/projectMaskedGA3D';
load([projPath '/analysis/plots/population/ids.mat'],'population');

monkeyNames = {'dobby' 'merri' 'gizmo'};
sCount = 1;
for ii=60:60 % 1:length(population)
    nGen = population(ii).nGen-population(ii).nPostHoc;
    for gg=1:nGen
        load([projPath '/stim/' monkeyNames{population(ii).monkeyId} '/' num2str(population(ii).prefix) '_r-' num2str(population(ii).runNum) '_g-' num2str(gg) '/stimParams.mat'])
        stimuli = stimuli'; stimuli = stimuli(:);
        for ss=1:length(stimuli)
            shapeResp(sCount).id = stimuli{ss}.id.descId;
            shapeResp(sCount).col = stimuli{ss}.shape.color;
            shapeResp(sCount).tex = stimuli{ss}.shape.texture;
            shapeResp(sCount).spec = stimuli{ss}.shape.mstickspec;
            shapeResp(sCount).resp = mean(stimuli{ss}.id.respMatrix);
            sCount = sCount+1;
        end
    end
end

save('export/phys_shapeResp.mat','shapeResp')