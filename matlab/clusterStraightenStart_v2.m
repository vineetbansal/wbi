
function clusterStraightenStart_v2(dataFolder)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Creates Initial files for Straightening images
% Inputs:
%   dataFolder- file path to data folder containing raw .dat file
%               timing results, behavior folder, lowmag folder,
%               alignments file. 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%



%% write to status file
hostname = char( getHostName( java.net.InetAddress.getLocalHost ) );
if contains(hostname,'della')
    Fid=fopen([dataFolder filesep 'status.txt'],'a');
    status=[datestr(datetime('now')) ':Starting straightening \n'];
    fprintf(Fid,status);
    fclose(Fid);
end



%which volume to do for initial, not too close to begining because start
%might not have all video feeds tracking properly
counter=100; 
%% bundle timing data
[bfAll,fluorAll,hiResData]=tripleFlashAlign(dataFolder);
vidInfo.bfAll=bfAll;
vidInfo.fluorAll=fluorAll;
vidInfo.hiResData=hiResData;

%% make time alignments
bf_ft=bfAll.frameTime;
fluor_ft=fluorAll.frameTime;
hi_ft=hiResData.frameTime;

bfIdxList=1:length(bfAll.frameTime);

fluorIdxList=1:length(fluor_ft);
bfIdxLookup=interp1(bf_ft,bfIdxList,hi_ft,'linear','extrap');
fluorIdxLookup=interp1(fluor_ft,fluorIdxList,hi_ft,'linear','extrap');
stack2BFidx=bfIdxLookup(diff(hiResData.stackIdx)==1);
stack2fluoridx=fluorIdxLookup(diff(hiResData.stackIdx)==1);

topLimit=min(max(hiResData.stackIdx),length(stack2BFidx));
BF2stackIdx=interp1(double(stack2BFidx),1:double(topLimit),double(bfIdxList),'nearest');
fluor2stackIdx=interp1(double(stack2fluoridx),1:double(topLimit),double(fluorIdxList),'nearest');


%% just using 300th volume for now
test_frame=counter;

%% load alignment data

%try to load the alignment file in the folder, otherwise, select them
%individual in the registration folder
alignments=load([dataFolder filesep 'alignments']);
alignments=alignments.alignments;

% to save the perspective transformation.
Aall = alignments.S2AHiRes.Aall;
Sall = alignments.S2AHiRes.Sall;

Aall = Aall(:, [2,1]) - 1;
Sall = Sall(:, [2,1]) - 1;
tform = fitgeotrans(Aall, Sall, 'projective');
M_matrix = tform.T;
tform = fitgeotrans(Sall, Aall, 'projective');
M_matrix_inv = tform.T;

% deal with missing backgrounds
if ~isfield(alignments,'background');
    alignments.background=0;
    save([dataFolder filesep 'alignments'],'alignments');
end

%% calculate offset between frame position and zposition
zWave=hiResData.Z;
zWave=gradient(zWave);
zWave=smooth(zWave,100);
image_std=hiResData.imSTD;
image_std=image_std-mean(image_std);
image_std(image_std>150)=0;
[ZSTDcorrplot,lags]=crosscorr(abs(zWave),image_std,30);
ZSTDcorrplot=smooth(ZSTDcorrplot,3);
zOffset=lags(ZSTDcorrplot==max(ZSTDcorrplot));


%save initial workspace from first sample for later use
save([dataFolder filesep 'startWorkspace'],...
    'zOffset', 'vidInfo', 'M_matrix', 'M_matrix_inv')
