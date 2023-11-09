%%% extract point set intensities and align according to neural IDs from
%%% the clustering pipeline!!

%% %load intensity
prematching_file = '/tigress/LEIFER/PanNeuronal/20191021/BrainScanner20191021_145041/red-prematching.txt';
% prematching_file = '/tigress/LEIFER/PanNeuronal/20190919/BrainScanner20190919_100858/red-prematching.txt';
% prematching_file = '/tigress/LEIFER/PanNeuronal/20191009/BrainScanner20191009_105022/red-prematching.txt';
% prematching_file = '/tigress/LEIFER/PanNeuronal/20191009/BrainScanner20191009_102320/red-prematching.txt';

pointstats_file = '/tigress/LEIFER/python-tracking/SMM_track/trackMatrix_ID_1021_145041';
% pointstats_file = '/tigress/LEIFER/python-tracking/SMM_track/trackMatrix_100858.mat';
% pointstats_file = '/tigress/LEIFER/python-tracking/SMM_track/trackMatrix_ID_1009_105022.mat';
% pointstats_file = '/tigress/LEIFER/python-tracking/SMM_track/trackMatrix_ID_1009_102320.mat';
pointstats2_K = load(pointstats_file);
pointstats2_K = pointstats2_K.pointStats2_K;
table_ = readtable(prematching_file);
intensity_array = table2array(table_);
for vv = 1:length(pointstats2_K)
    nneurons = pointstats2_K(vv).nneurons;
    pointstats2_K(vv).Rintensities = intensity_array(vv,1:nneurons);
end

%% make heat map
%fill in hear map
RR = {};
for vv = 1:length(pointstats2_K)
    neurons = pointstats2_K(vv).nneurons;
    ids = pointstats2_K(vv).trackIdx;
    ints = pointstats2_K(vv).Rintensities;
    for nn = 1:neurons
        if isnan(ids(nn)) ~=1
            RR{vv,ids(nn)} = ints(nn);
        end
    end
end
%fill in NaNs
for ii = 1:size(RR,1)
    for jj = 1:size(RR,2)
        if isempty(RR{ii,jj})==1
            RR{ii,jj} = NaN;
        end
    end
end

rRaw_K = cell2mat(RR)';

%% plot
% rRaw_K(rRaw_K>1000) = 1000;
imagesc(rRaw_K)

%% Custom analysis for hybrid pipeline (with old segmentation and new alignment)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
pointStatsK = load('/tigress/LEIFER/PanNeuronal/20191120/BrainScanner20191120_120312/TrackMatrix_hybrid/TrackMatrix_hybrid.mat');
pointStatsK = pointStatsK.pointStats2_K;
pointStats = load('/tigress/LEIFER/PanNeuronal/20191120/BrainScanner20191120_120312/PointsStats.mat');
pointStats = pointStats.pointStats;
%%
IDs = cell2mat({pointStatsK.stackIdx});
for vv = 1:length(pointStatsK)
    pointStatsK(vv).Rintensities = pointStats(IDs(vv)+1).Rintensities;
end
%%
%fill in hear map
RR = {};
for vv = 1:1000%length(pointStatsK)
    neurons = pointStatsK(vv).nneurons;
    ids = pointStatsK(vv).trackIdx;
    ints = pointStatsK(vv).Rintensities;
    for nn = 1:neurons
        if isnan(ids(nn)) ~=1
            RR{vv,ids(nn)} = ints(nn);
        end
    end
end
%fill in NaNs
for ii = 1:size(RR,1)
    for jj = 1:size(RR,2)
        if isempty(RR{ii,jj})==1
            RR{ii,jj} = NaN;
        end
    end
end

rRaw_K = cell2mat(RR)';

%%
imagesc(rRaw_K)