function [bfFrameAtEachVolume, hiMagFrameAtEachVolume] =  heatmap2centerline(volume,dataFolder)


load([dataFolder filesep 'heatData']);

[bfAll,~,hiResData]=tripleFlashAlign(dataFolder);


bfFrameAtEachVolume=interp1(bfAll.frameTime,1:length(bfAll.frameTime),hiResData.frameTime(diff(hiResData.stackIdx)==1),'nearest',0);

hiMagFrameAtEachVolume =find(diff(hiResData.stackIdx)==1);

end