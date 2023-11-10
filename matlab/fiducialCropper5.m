function fiducialCropper5(dataFolder)
%%%%%%%%%%%
% This is adopted from fiducialCropper4 for the new low mag design with
% only the IR camera
%
% There are two difference from fiducialCropper4
% 1) inside function extractSignal hiResData is imported from the
% BrainScanner folder directly
% 2) under the main function bfAll and hiResData is generated from 
% doubleFlashAlign 


%write to status file if we're on della (only newer versions of matlab)
hostname = char( getHostName( java.net.InetAddress.getLocalHost ) );
if contains(hostname,'della')
    Fid=fopen([dataFolder filesep 'status.txt'],'a');
    status=[datestr(datetime('now')) ':Starting Signal Extraction \n'];
    fprintf(Fid,status);
    fclose(Fid);
end


%% Extract signal from neurons
[RvalAll,GvalAll]=extractSignal(dataFolder);

%% makes photobleaching corrected, spatially corrected heatmaps, saves resultheatMapGeneration(dataFolder,RvalAll,GvalAll)
heatMapGeneration(dataFolder, RvalAll, GvalAll);
load([dataFolder filesep 'heatData'])

%% make timing tracks

[bfAll,hiResData]=doubleFlashAlign(dataFolder);
% load pointStats File
FPS_low = 1/median(diff(bfAll.frameTime)); %calculate the behavior frames per second
FPS_hi = 1/median(diff(hiResData.frameTime));

pointStatsFile=[dataFolder filesep 'pointStatsNew.mat'];
pointStats=load(pointStatsFile);
pointStats=pointStats.pointStatsNew;
try
    XYZcoord=getSampleCoordinates(pointStats); %will be saved
catch
    XYZcoord = 0;
end
%change to >=1 to get at least as many time points as stacks
hasPointsTime=hiResData.frameTime(diff(hiResData.stackIdx)>=1);
n_lim = min(length(pointStats), size(hasPointsTime, 1));
hasPoints=1:n_lim;
size(hasPointsTime),size(hasPoints) 
hasPointsTime=hasPointsTime(hasPoints);

[centerline,eigenProj, CLV,wormCentered]=loadCLBehavior(dataFolder);
n_CL=size(centerline,3);
n_CL, size(bfAll.frameTime), size(eigenProj)

if n_CL > length(bfAll.frameTime)
    s = n_CL - length(bfAll.frameTime);
    %centerline = centerline(:,:,1:n_CL);
    %eigenProj = eigenProj(:, 1:n_CL);
    %CLV = CLV(1:n_CL);
    %wormCentered = wormCentered(1:n_CL);
    bfAll.frameTime = padarray(bfAll.frameTime, s, 0, 'post');
end
clTime=bfAll.frameTime(1:n_CL);

%% load centerline data, pad with zeros if needed to making size the same as
%behavior video size

CLbehavior=sign(smooth(-CLV',FPS_low));
hiResCLbehavior=interp1(clTime,CLbehavior,hiResData.frameTime,'nearest',0);

%% add centerline center of mass to stage position
[xPos,yPos]=calculate_cm_position(centerline,hiResData,clTime,dataFolder,'head');
%get worm cm positions for each volume measured


%% Calculate worm velocities


if false
    filterKernal2=makeGaussKernel(3 * FPS_hi, 1 * FPS_hi);
    filterFactor2=imfilter(ones(size(xPos)),filterKernal2);
    xV=imfilter((xPos),filterKernal2)./filterFactor2;
    yV=imfilter((yPos),filterKernal2)./filterFactor2;
    hiResVel=[gradient(xV) gradient(yV)];
    hiResVel=sqrt(sum(hiResVel.^2,2));
    hiResVel=hiResVel.*hiResCLbehavior; %ANdy needs to: replace this


else

    %% Simultaneously smooth and take derivative
    sigma_smooth=1/2;
    derivSmoothKernel=makeDerivGaussKernel(4 * FPS_hi, (sigma_smooth)*FPS_hi , FPS_hi);
    dx = imfilter((xPos),derivSmoothKernel,'replicate');
    dy = imfilter((yPos),derivSmoothKernel, 'replicate');
    hiResSpeed=sqrt(sum([dx, dy].^2,2)); 

    %% Find the worm's orientation in the same coordinate system as the velocity vector
    %First  
    [ox,oy]=find_head_vec(centerline,hiResData,clTime,dataFolder);
    ox_smooth = smoothdata(ox,'gaussian',sigma_smooth*FPS_hi);
    oy_smooth = smoothdata(oy,'gaussian',sigma_smooth*FPS_hi);
    vel_dot = dot([ox_smooth,oy_smooth],[dx,dy],2)./ sqrt(dot([ox_smooth,oy_smooth],[ox_smooth,oy_smooth],2));
    vel_sign = sign(vel_dot);
    hiResVel = vel_dot; %take the dot product as the final velocity    
    
    DEBUG=true;
    if DEBUG
        figure;  hold on;
        plot(hiResSpeed,'DisplayName', 'Speed')
        plot(hiResSpeed.*vel_sign,'DisplayName','Speed*sign(dot)');
        plot(hiResVel-0.2,'DisplayName','OUTPUT (speed dot headvec)');
        plot(0.02*sign(vel_dot)-.25,'DisplayName','Sign');
        plot(vel_dot-0.2, 'DisplayName', 'Head dot TangentVec');
        plot(0.02*hiResCLbehavior-0.3,'DisplayName','HiResCLBehavior');
        plot(.02 *(vel_sign-hiResCLbehavior)-.4,'DisplayName','Residual');
        line(xlim(), [0,0], 'LineWidth', 1, 'Color', 'k')
        line(xlim(), [-.2,-0.2], 'LineWidth', 1, 'Color', 'k')
        legend; title([dataFolder, ' \sigma=', num2str(sigma_smooth), 's' ]); ylabel('mm/s'); xlabel('HiFrames (200fps)');
    end
        
    
end



%%
xPosTrack=[xPos(1); xPos((find(diff(hiResData.stackIdx)>0)))];
yPosTrack=[yPos(1); yPos((find(diff(hiResData.stackIdx)>0)))];
xPosTrack=xPosTrack(hasPoints);
yPosTrack=yPosTrack(hasPoints);

vTrack=[hiResVel(1); hiResVel((find(diff(hiResData.stackIdx)>0)))];
vTrack=vTrack(hasPoints);
%% Don't load eigen behavior and do cylindrical rotation for more independent Z

eigenBehavior=eigenProj;
temp=eigenBehavior;
behaviorProjection=temp(1:3,:)';
[~,maxIdx]=max(sum(behaviorProjection.^2,2));
maxPoint=behaviorProjection(maxIdx,:);
[phi,theta,R] = cart2sph(maxPoint(1),maxPoint(2),maxPoint(3));
[x,E]=fminsearch(@(x) circlePlane(behaviorProjection,x(1),x(2)),[phi theta]);
phi=x(2);
theta=x(1);
[~,projections]=circlePlane(behaviorProjection,theta,phi);
n=[cos(phi)*sin(theta) sin(phi)*sin(theta) cos(theta)];
behaviorZP=behaviorProjection*n';
%Rmat=normc(projections'*behaviorZ);
%Rmat=[Rmat(1) Rmat(2); Rmat(2) -Rmat(1)];
%projections=(Rmat*projections')';

behaviorZ = eigenBehavior(1,:);
nonprojections = eigenBehavior(2:3,:)';

behaviorZTrack=interp1(clTime,behaviorZ,hasPointsTime);
%behaviorZProj = interp1(clTime,behaviorZP,hasPointsTime);
projectionsTrack=interp1(clTime,nonprojections,hasPointsTime);
hiResBehaviorZ=interp1(clTime,behaviorZP,hiResData.frameTime);

%% make some sort of ethogram;
%still in progress for more types of worm
% -1 for reverse
% 0 for pause
% 1 for forward
% 2 for turn

ethogram=makeEthogram(hiResVel,hiResBehaviorZ);
ethoTrack=interp1(hiResData.frameTime([true; diff(hiResData.frameTime)~=0]),ethogram([true; diff(hiResData.frameTime)~=0]),hasPointsTime,'nearest');

%combine behaviors into structure
behavior.ethogram=ethoTrack;
behavior.x_pos=xPosTrack;
behavior.y_pos=yPosTrack;
behavior.v=vTrack;
behavior.pc1_2=projectionsTrack;
behavior.pc_3=behaviorZTrack;

%% save files
save([dataFolder filesep 'positionDataMS'],...
    'xPos','yPos','hiResVel','behaviorZTrack','projectionsTrack','-v6')

save([dataFolder filesep 'heatData'],...
    'XYZcoord',...
    'behavior',...
    'hasPointsTime',...
    'clTime',...
    '-append','-v6');



function boxPix=boxCoord(L)
%% initialize box. This will be added to gather pixel values from around the centroid
boxR=[L L L];
[boxX,boxY,boxZ]=meshgrid(-boxR(1):boxR(1),-boxR(2):boxR(2),-boxR(3):boxR(3));
boxMask=(boxX.^2+boxY.^2+boxZ.^2)<25;
boxX=boxX(boxMask);
boxY=boxY(boxMask);
boxZ=boxZ(boxMask);
boxPix=[boxX,boxY,boxZ];


function all_corr=illuminationCorrection()
%% create illumination profile correction, if files are present

try
    %load illumination profiles, these are images normalized images of a
    %fluorescent calibration slide. Each image is full field, but due to
    %the filters only the appropriate half of the dual view image is shown.
    
    profileG=load('illumination_profile_G.mat');
    profileG=profileG.illumination_profile;
    profileG=profileG./max(profileG(:));

    g_corr=1./profileG;
    %remove very bright and very dim pixels in the calibration image
    g_corr(g_corr>5| g_corr<0)=0;
    
    profileR=load('illumination_profile_R.mat');
    profileR=profileR.illumination_profile;
    profileR=profileR/max(profileR(:));
    r_corr=1./profileR;
    r_corr(r_corr>5 | r_corr<0)=0;
    
    %combine the two halves, the two regions corresponding to the image should
    %have no overlap so a straight pix by pix sum will work
    all_corr=g_corr+r_corr;
catch me
    
    display(' No illumination profile found, no correction applied')
    all_corr=1;
end


function [RvalAll,GvalAll]=extractSignal(dataFolder)
%%
%get files from dataFolder, including the imageFolder and the pointStats
%file.

boxPix=boxCoord(5);
all_corr=illuminationCorrection();

pointStatsFile=[dataFolder filesep 'pointStatsNew.mat'];
psFolder=dir([dataFolder filesep 'CLstraight*']);
imageFolder=[dataFolder filesep psFolder(end).name];
%% load pointStats File

pointStats=load(pointStatsFile);
pointStats=pointStats.pointStatsNew;

% read in sCMOS dat file
datFileDir=dir([dataFolder filesep 'sCMOS_Frames_U16_*']);
datFile=[dataFolder filesep datFileDir.name];
%get image dimensions
[rows,cols]=getdatdimensions(datFile);

if rows == 1024 && cols == 1024
    rows = 1200;
    cols = 600;
end
nPix=rows*cols;


%read in timing data
% [~,hiResData]=doubleFlashAlign(dataFolder);
hiResData = importdata([dataFolder filesep 'hiResData.mat']);


%also need phase delay used between z position and image number
timeOffset=load([dataFolder filesep 'startWorkspace.mat'],'zOffset');
timeOffset=timeOffset.zOffset;

% load alignments
alignments=load([dataFolder filesep 'alignments.mat']);
alignments=alignments.alignments;
S2AHiRes=alignments.S2AHiRes;
rect1=S2AHiRes.rect1;
rect2=S2AHiRes.rect2;

if isfield(alignments,'background')
    background=alignments.background;
else
    background=0;
end



%%
fiducialPoints=cell(1,length(pointStats));
for i=1:length(pointStats)
    try
        %load and process the image
        
        iFile=pointStats(i).stackIdx;
        Fid=fopen(datFile);
        %get startframe for single voluem scan
        lowLimit=find(hiResData.stackIdx==iFile,1,'first')+timeOffset;
        nSlices=nnz(hiResData.stackIdx==iFile);
        
        %move pointer and read the pixel values
        status=fseek(Fid,2*(lowLimit)*nPix,-1);
        pixelValues=fread(Fid,nPix*nSlices,'uint16',0,'l');
        
        %create image volume
        hiResImage=(reshape(pixelValues,rows,cols,nSlices));
        
        %subtract background and apply intensity correction
        if any(background(:))
            hiResImage=bsxfun(@minus,hiResImage,background);
        else
            hiResImage=pedistalSubtract(hiResImage);
        end
       % hiResImage=bsxfun(@times,hiResImage,all_corr);
        hiResImage(hiResImage<0)=0;
        
        
        %% load transformation from striaghtened to original
        pointFile=([imageFolder ...
            filesep 'pointStats' num2str(iFile,'%2.5d') '.mat']);
        pointStatsTemp=load(pointFile);
        pointStatsTemp=pointStatsTemp.pointStats;
        
        %tgese are the lookuptables between pixel in straightened
        %coordinate and original image.
        
        X=double(pointStatsTemp.transformx);
        Y=double(pointStatsTemp.transformy);
        Z=double(pointStatsTemp.transformz);
        
        if any(size(X)==1);
            [X, Y, Z]=meshgrid(X,Y,Z);
        end
        
        nSize=size(X);
        
        %pull tracking results
        trackIdx=pointStats(i).trackIdx;
        trackWeights=pointStats(i).trackWeights;
        straightPoints=pointStats(i).straightPoints;
        
        % get the tracked neurons present in this volume
        present=~isnan(trackIdx) & ~isnan(straightPoints(1:length(trackIdx),1));
        
        %compress and organize tracking results
        trackIdx=trackIdx(present);
        trackWeights=trackWeights(present(1:length(trackWeights)));
        trackWeightstemp=zeros(size(trackIdx));
        trackWeightstemp(1:length(trackWeights))=trackWeights;
        trackWeights=trackWeightstemp;
        straightPoints=straightPoints(present,:);
        
        %% get pixels of interest by adding the boxPix to each point.
        boxPixAll=bsxfun(@plus,straightPoints,permute(boxPix,[3,2,1]));
        boxPixAll=round(boxPixAll);
        % bound at the end of the box, though this is rare
        boxPixAll(boxPixAll<1)=1;
        for iDim=1:3
            temp=boxPixAll(:,iDim,:);
            temp(temp>nSize(iDim))=nSize(iDim);
            boxPixAll(:,iDim,:)=temp;
        end
        
        %turn sub into linear index,
        boxPixAllLin=sub2ind_nocheck(nSize,boxPixAll(:,1,:),boxPixAll(:,2,:),boxPixAll(:,3,:));
        boxPixAllLin=permute(boxPixAllLin,[3,1,2]);
        %%
        %transform points ball points into unstraightened coord (red image)
        newX=X(boxPixAllLin);
        newY=Y(boxPixAllLin);
        newZ=Z(boxPixAllLin);
        newX1=newX+rect1(1)-1;
        newY1=newY+rect1(2)-1;
        
        %do transformation for green image
        [newX2,newY2]=transformPointsInverse(S2AHiRes.t_concord,newX,newY);
        newY2=newY2+rect2(2)-1;
        newX2=newX2+rect2(1)-1;
        newX2=round(newX2);
        newY2=round(newY2);
        %make raw points for saving, need to check
        rawPoints=coordinateTransform3d(straightPoints,X,Y,Z);
        hiResRange=find(hiResData.stackIdx==pointStats(i).stackIdx);
        hiResIdx=interp1(hiResRange,rawPoints(:,3),'linear','extrap')+timeOffset;
        hiResVoltage=interp1(hiResData.Z,hiResIdx-timeOffset);
        fiducialPointsi=cell(200,4);
        %% loop over points and get average pixel intensities
        %intialize intensity vector for a given volume
        
        R_i=interpSignal(hiResImage,newX1,newY1,newZ);
        G_i=interpSignal(hiResImage,newX2,newY2,newZ);
        
        
        %on first pass, initialize outputs for green and red and weights as
        %nans
        if ~exist('GvalAll','var')
            GvalAll=nan(nnz(present),max([pointStats.stackIdx]));
            RvalAll=GvalAll;
            trackWeightAll=RvalAll;
        end
        
        if length(trackIdx)==length(trackWeights)
            trackWeightAll(trackIdx,iFile)=trackWeights;
        end
        
        %save intensity averages
        RvalAll(trackIdx,iFile)=R_i;
        GvalAll(trackIdx,iFile)=G_i;
        
        %save cell aray with all coordinates, voltages, and frame numbers
        fiducialPointsi(trackIdx,:)=...
            num2cell([rawPoints(:,1:2) hiResVoltage hiResIdx]);
        
        fclose(Fid);
        fiducialPoints{iFile}=fiducialPointsi;
        display(['Finished frame : ' num2str(i)]);
    catch ME
        ME
        display(['Error frame:' num2str(i)]);
    end
    
end

%% save cropped regions and a new set of unstraighted centroids
newFiducialFolder=[dataFolder filesep 'BotfFiducialPoints'];
mkdir(newFiducialFolder);
%save time offset and unstraightened fiducial cell structure, not as
%important any more, but good for visualization

%used for clicking back in the day, not really needed anymore
clickPoints=0;
save([newFiducialFolder filesep 'timeOffset'],'timeOffset');
save([newFiducialFolder filesep 'botFiducials'],...
    'fiducialPoints',...
    'clickPoints');

%write to status file
hostname = char( getHostName( java.net.InetAddress.getLocalHost ) );
if contains(hostname,'della')
    Fid=fopen([dataFolder filesep 'status.txt'],'a');
    status=[datestr(datetime('now')) ':Finished Signal Extraction \n'];
    fprintf(Fid,status);
    fclose(Fid);
end



% interpSignal takes coordinates given by XYZ and interpolates the signal
% from hiResImage. The signal is averaged over the columns, with a few
% checks for ensuring the pixels are in the image and do not have wild
% variations.
function signal=interpSignal(hiResImage,X,Y,Z)

signal=nan(size(X,2),1);


for iPoint=1:size(X,2)
    %%
    %get all pixels of interest for a point iPoint, red version
    xball1=X(:,iPoint);
    yball1=Y(:,iPoint);
    zball=Z(:,iPoint);
    
    %remove bad pixels
    xball1(xball1==0)=nan;
    yball1(yball1==0)=nan;
    zball(zball==0)=nan;
    reject1=isnan(xball1) |isnan(yball1)|isnan(zball);
    keep=~reject1;
    
    % get index for each pixel of interest for R and G
    linBall1=sub2ind_nocheck(...
        size(hiResImage),...
        yball1(keep),...
        xball1(keep),...
        zball(keep));
    
    % get pixel values
    Fset=hiResImage(linBall1);
    %some pixels are prone to producing large values, try to remove
    %these
    bad_pix=abs(zscore(Fset))>5;
    Fset(bad_pix)=[];
    Fnorm=normalizeRange(Fset);
    Fthresh=Fnorm<graythresh(Fnorm);
    Fset(Fthresh)=[];
    %take trim mean to try to clean signal a bit
    F_point=trimmean(Fset,20);
    
    signal(iPoint)=F_point;
    
end


function [xPos,yPos]=calculate_cm_position(centerline,hiResData,bf_frameTime,dataFolder,target)


    

%some conversion factors
pos2mm=1/10000;

%% SETTINGS THAT DEPEND ON THE CAMERAS ORIENTATION WITH RESPECT TO STAGE
% These have changed at least three times over the course of the project
if contains(dataFolder, '2017') %Note i have not investigated situation for 2016 or before
    CL2mm=1/557;
    stageCamAngle=90;
    orientationX=-1;
else
    CL2mm=1/473; % 1mm per 473 pixels  (as measured by Kelsey late Feb 2020 and re assess Aug 2020)
    stageCamAngle=270;
    orientationX=1;
end
stageCamAngle=stageCamAngle*pi/180;

CL2mm=1/473; % 1mm per 473 pixels  (as measured by Kelsey late Feb 2020 and re assess Aug 2020)
orientationX=1;

if strcmp(target,'com') 
     %get mean of CL coordinates for center of mass
    centerLinePosition=squeeze(mean(centerline,1));
else
    %Otherwise use a point part way down the body of the worm
    HEAD=15;
    centerLinePosition=squeeze(centerline(HEAD,:,:));
end
centerLinePosition(centerLinePosition==0)=nan;
centerLinePosition=inpaint_nans(centerLinePosition);
%Set (0,0) for the coordinate system of the image to be the worm's mean position 
centerLinePosition=bsxfun(@minus,centerLinePosition,mean(centerLinePosition,2));
centerLinePosition=centerLinePosition';

%Run a hampel filter on the centerline position to account for odd discrete
%jumps in centerline
WIN=3;
centerLinePosition(:,1) = hampel(centerLinePosition(:,1),WIN);
centerLinePosition(:,2) = hampel(centerLinePosition(:,2),WIN);

%interpolate into imaging rate of hiRes
hiResCLposition=...
    [interp1(bf_frameTime,centerLinePosition(:,1),...
    hiResData.frameTime,'nearest',0),...
    interp1(bf_frameTime,centerLinePosition(:,2),...
    hiResData.frameTime,'nearest',0)];

hiResCLposition(isnan(hiResCLposition(:,1)),1)=nanmean(hiResCLposition(:,1));
hiResCLposition(isnan(hiResCLposition(:,2)),2)=nanmean(hiResCLposition(:,2));

hiResCLposition=hiResCLposition*CL2mm;


%rotation matrix that takes motion of stage direction to motion in low mag
%behavior image
Rmatrix=[-cos(stageCamAngle) sin(stageCamAngle);...
    -sin(stageCamAngle) -cos(stageCamAngle)];
hiResCLposition=(Rmatrix'*hiResCLposition')';

%convert units
xPosStage=hiResData.xPos*pos2mm;
yPosStage=hiResData.yPos*pos2mm;

%Run a hampel filter on the raw stage position data
xPosStage=hampel(xPosStage,WIN);
yPosStage=hampel(yPosStage,WIN);

%Deal with NaNs (I think? --Andy)
xPosStage([0; diff(xPosStage)]==0)=nan;
xPosStage=inpaint_nans(xPosStage);
yPosStage([0; diff(yPosStage)]==0)=nan;
yPosStage=inpaint_nans(yPosStage);

% Combine stage position with centerline position
% (If the axes were the same i believe you would want to subtract)
% switched some signs 1 and 2 for jeff cls, may need switching for some
% camera rotations
xPos=xPosStage+orientationX*hiResCLposition(:,1); %Andy cnangd this from -1->+1 Aug 21 2020
yPos=yPosStage+1*hiResCLposition(:,2);

debug=true;
if debug
    figure;
    hold on;
    plot(xPosStage, 'DisplayName','x Stage');  
    plot(hiResCLposition(:,1), 'DisplayName','x Centerline COM');
    plot(xPos, 'DisplayName','x Combined');
    plot(yPosStage, 'DisplayName','y Stage');  
    plot(hiResCLposition(:,2), 'DisplayName','y Centerline COM');
    plot(yPos, 'DisplayName','y Combined');
    legend; title(dataFolder); xlabel('HiMag Frame (200fps)'); ylabel('mm')
end





%simple function to make normalized gaussian kernel with sdev
function filterKernel=makeGaussKernel(winsize, sdev)
alpha= (winsize-1)/(2*sdev); %from the matlab function definition
filterKernel=gausswin(winsize, alpha);
filterKernel=filterKernel-min(filterKernel(:));
filterKernel=filterKernel/sum(filterKernel);


%simple function to make normalized derivative of a gaussian kernel with sdev
% perfected by Ross Dempsey
function filterKernel=makeDerivGaussKernel(winsize,sdev,  fps)
alpha= (winsize-1)/(2*sdev); %from the matlab function definition
gauss = gausswin(winsize, alpha);
filterKernel = gradient(gauss, 1/fps);
%figure; plot(filterKernel); hold on; plot(gauss)
cms_left = dot(1:floor(winsize/2),filterKernel(1:floor(winsize/2)))/sum(filterKernel(1:floor(winsize/2)));
cms_right = dot(ceil(winsize/2):winsize,filterKernel(ceil(winsize/2):winsize))/sum(filterKernel(ceil(winsize/2):winsize));
filterKernel = filterKernel/(sum(filterKernel(ceil(winsize/2):winsize))*(cms_right-cms_left)/fps);




% -1 for reverse
% 0 for pause
% 1 for forward
% 2 for turn

%colors for plotting
function c_out=ethocolormap()
fcolor=[0 1 0];%[27 158 119]/256;
bcolor=[1 0 0];%[217 95 2]/256;
turncolor=[0 0 1];%[117 112 179]/256;
pausecolor=[255 217 50]/256;
c_out=[bcolor;pausecolor;fcolor;turncolor];


function ethogram=makeEthogram(hiResVel,hiResBehaviorZ)
%attempt to make an ethogram of behavior using the velocity of the animal
%(which will have a sign to take into account forward and reversal) and the
%projection onto the "3rd" eigenworm, where peaks correspond to high
%curvature and likely turns. 

%use 3rd eigenmode for finding turns
ethoZ=hiResBehaviorZ;
ethoZ=ethoZ-nanmean(ethoZ);
ethoZ(isnan(ethoZ))=0;

%cluster velocities to find forward and back
Vcluster=smooth(hiResVel,100);
idx=sign(Vcluster);
idx(abs(Vcluster)<.00005)=0;
ethogram=idx;
ethogram((((abs(ethoZ)>2*std(ethoZ))& (ethogram>=0)))|abs(ethoZ)>10)=2;

% Kill off short behaviors unless they are reversals
for iBehavior=[0 1 2];
    cpause=bwconncomp(ethogram==iBehavior);
    shortPause=cellfun(@(x) length(x), cpause.PixelIdxList);
    shortPause= shortPause'<500;
    shortPause=cpause.PixelIdxList(shortPause);
    shortPause=cell2mat(shortPause');
    ethogram(shortPause)=nan;
    ethogram=colNanFill(ethogram,'nearest');
end

ethogram(hiResVel==0)=nan;


function coord_out=getSampleCoordinates(pointStats)


foundNeurons= max(cellfun(@(x) nanmax(x),{pointStats.trackIdx}));
coord_out = zeros(foundNeurons, 3);
length_c = 0;


for iFrame=1:length(pointStats)
ps=pointStats(iFrame);
coord=ps.straightPoints;
trackIdx=ps.trackIdx;
coord=coord(~isnan(trackIdx),:);
trackIdx=trackIdx(~isnan(trackIdx));
%coord=coord(trackIdx,:);

% Xinwei change here
if length(trackIdx) > length_c
    coord_out = zeros(foundNeurons, 3);
    coord_out(trackIdx, :) = coord;
    length_c = length(trackIdx);
    if length_c == foundNeurons
        return
    end
end

% if ~any(isnan(coord(:))) && size(coord,1)==foundNeurons
%     return
% end
end
% error('No frame has all the neurons! Tracking failed');

function [ox, oy]=find_head_vec(centerline, hiResData, clTime, dataFolder)
%Find the head vector in the same coordinate as the center of mass velocity
% Andrew Leifer
% 10 May 2021

NOSE=10;
NECK=20;

%Lets use a trick to calculate the position in the velocity coordinate
%system
% Here we calculate the "center of mass' of the centerline, but the trick
% is we only pass in a single point of the centerline, so instead we just
% use the function as a transformation to get out the centerline in the new
% coordinate system
[xNose,yNose]=calculate_cm_position(centerline(NOSE,:,:),hiResData,clTime,dataFolder,'com');
[xNeck,yNeck]=calculate_cm_position(centerline(NECK,:,:),hiResData,clTime,dataFolder, 'com');

ox=xNose-xNeck;
oy=yNose-yNeck;


