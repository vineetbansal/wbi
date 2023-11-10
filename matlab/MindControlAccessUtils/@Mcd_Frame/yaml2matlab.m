function mcdf=yaml2matlab(file,fSTART,fEND)
% This function reads in a yaml file produced by the MindControl Software
% and exports an array of MindControl Data Frames (mcdf's) that is easy to
% manipulate in matlab.
%
% Andrew Leifer
% leifer@fas.harvard.edu
% 2 November 2010


fid = fopen(file); 
if nargin==3;Mcd_Frame.seekToFirstFrame(fid, fSTART);end
if nargin==1;Mcd_Frame.seekToFirstFrame(fid);end
k=1;
while(~feof(fid))
%for i = fSTART:fEND
    mcdf(k)=Mcd_Frame.readOneFrame(fid); %#ok<AGROW>
    k=k+1;
    if ~mod(k,100)
        disp(k);
    end
    if nargin==3 && k==fEND-fSTART;break;end
end
if nargin==3;
mcdf(1).FrameNumber = fSTART; %since skipped in finding start frame
end
fclose(fid);

