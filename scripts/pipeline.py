from wbi.experiment import Experiment
from wbi.legacy.make_centerline import make_centerline
from wbi.legacy.flash_finder import flash_finder


FOLDER = "/bs"
"""
.
├── alignments.mat
├── CameraFrameData.txt
├── framesDetails.txt
├── other-frameSynchronous.txt
├── other-volumeMetadataUtilities.txt
├── LowMagBrain20231018_143646
│   ├── cam1.avi
│   └── CamData.txt
└── sCMOS_Frames_U16_1024x512.dat
"""

if __name__ == "__main__":
    e = Experiment(FOLDER)

    flash_finder(input_folder=FOLDER, experiment=e, max_frames=10)

    # This is for bead alignment and only works for /bsa
    # e.generate_median_images()

    make_centerline(input_folder=FOLDER, plot=True, max_frames=10)
