% this code save results of tripleFlashAlign.m
function [bfAll,fluorAll,hiResData]=compile_tripleFlashAlign(dataFolder, f_idx)

%save_path = '/projects/LEIFER/Xinwei/github/Pytorch-Unet/tmp';

% run the tripleFlashAlign.m
[bfAll,fluorAll,hiResData] = tripleFlashAlign(dataFolder);

save_destination = [dataFolder filesep 'timeFile_tmp'];

save(save_destination,'bfAll', 'fluorAll','hiResData');


