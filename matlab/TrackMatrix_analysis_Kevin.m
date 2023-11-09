%TrackMatrix_analysis
inputdir = '/tigress/LEIFER/PanNeuronal/20191120/BrainScanner20191120_120312/TrackMatrix';
S = dir(fullfile(inputdir,'*.mat'));
Track_size = [];
for k = 1:numel(S)
    fnm = fullfile(inputdir,S(k).name);
    temp = load(fnm);
    Track_size = [Track_size, size(temp.TrackMatrixi,1)];
end
plot(Track_size)

%%
