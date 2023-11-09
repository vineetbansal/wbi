function mcw2wbi_straight(dataFolder)
%%%%%%%%%%%%%%%%%
% add multicolor worm recording image(straightened) to pointStats 
% this help use to use NeRVE with multicolor recording.
%%%%%%%%%%%%%%%

ps = load([dataFolder filesep 'PointsStats.mat']);

ps_l = length(ps.pointStats);
iStack = ps_l + 1;

jeff_f = [dataFolder filesep 'straight_mcw' filesep 'jeff.mat'];
ps_mcw = load(jeff_f);
jeff_img = [dataFolder filesep 'straight_mcw' filesep 'image.tif'];


ps_mcw.pointStats.stackIdx = iStack;

dp = dir([dataFolder filesep 'CLstraight_*']);
destination_path = [dataFolder filesep dp(end).name];
image_destination=...
        [destination_path filesep 'image' num2str(iStack,'%3.5d') '.tif'];
    
mat_destination=...
        [destination_path filesep 'pointStats' num2str(iStack,'%3.5d')];
    
    
ps.pointStats(iStack).stackIdx = ps_mcw.pointStats.stackIdx;
ps.pointStats(iStack).straightPoints = ps_mcw.pointStats.straightPoints;
ps.pointStats(iStack).rawPoints = ps_mcw.pointStats.rawPoints;
ps.pointStats(iStack).pointIdx = ps_mcw.pointStats.pointIdx;
ps.pointStats(iStack).Rintensities = ps_mcw.pointStats.Rintensities;
ps.pointStats(iStack).Volume = ps_mcw.pointStats.Volume;
% save 
pointStats = ps_mcw.pointStats;
save(mat_destination,'pointStats');
pointStats = ps.pointStats;
save([dataFolder filesep 'PointsStats'],'pointStats');

copyfile(jeff_img, image_destination)


