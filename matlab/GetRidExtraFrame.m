function []=GetRidExtraFrame(dataFolder)
%dataFolder='/tigress/LEIFER/PanNeuronal/20181114/BrainScanner20181114_214842';

A=load([dataFolder,'/hiResData.mat']);
dataAll=A.dataAll;
save([dataFolder, filesep ,'hiResData_backup.mat'],'dataAll')

stackIdx=dataAll.stackIdx;

maxIdx=max(stackIdx);



Z=dataAll.Z;
Zindex=find(Z==0);
for i=1:length(Zindex)
    if Zindex(i)>1 && Zindex(i)<length(Z)
        Z(Zindex(i))=(Z(Zindex(i)+1)+Z(Zindex(i)-1))/2;
    end
end
dataAll.Z=Z;


for i=maxIdx:-1:stackIdx(1)
    stacki=find(stackIdx==i);
    if length(stacki)==1 && stacki<length(Z)-2 && stacki>2
        if (Z(stacki)-Z(stacki+1))*(Z(stacki+1)-Z(stacki+2))>0
            dataAll.stackIdx(stacki)=dataAll.stackIdx(stacki+1);
            dataAll.stackIdx(stacki:end)=dataAll.stackIdx(stacki:end)-1;
        else
            dataAll.stackIdx(stacki)=dataAll.stackIdx(stacki-1);
            dataAll.stackIdx(stacki+1:end)=dataAll.stackIdx(stacki+1:end)-1;
    
        end
    end
end


save([dataFolder, filesep ,'hiResData.mat'],'dataAll')

