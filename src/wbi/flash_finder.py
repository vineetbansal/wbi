# Copied from
# https://github.com/leiferlab/3dbrain/blob/master/TimeAlignment/highResTimeTraceAnalysisTriangle4.py
# with minor modifications to work with Python 3.x
import os
import numpy as np
import scipy.io as sio


def flash_finder(input_folder, output_folder=None, chunksize=4000, max_frames=None):

    output_folder = output_folder or input_folder

    # Limit memory usage. Load chunks of data
    # TODO: Why are we doing this?
    chunkMaxSize = chunksize // 6  # number of frames to read at once

    # Open file containing frames
    filename = os.path.join(input_folder, "sCMOS_Frames_U16_1024x512.dat")

    # try to be robust to renaming
    try:
        filesize = os.stat(filename).st_size
        f = open(filename, "rb")
    except FileNotFoundError:
        filename = os.path.join(input_folder, "frames_U16_1024x512.dat")
        filesize = os.stat(filename).st_size
        f = open(filename, "rb")
    # Find out how many iterations you have to do
    nFrames = filesize // (1024 * 512 * 2)
    if max_frames is not None:
        nFrames = min(nFrames, max_frames)
    nIterations = nFrames // chunkMaxSize
    remainingframes = nFrames - nIterations * chunkMaxSize
    brightness = np.zeros(nFrames)
    stdev = np.zeros(nFrames)

    # Full iterations
    for i in np.arange(nIterations):
        chunk = np.fromfile(f, dtype=np.uint16, count=chunkMaxSize * 1024 * 512)
        frames = chunk.reshape((chunkMaxSize, 1024 * 512))
        brightness[i * chunkMaxSize : (i + 1) * chunkMaxSize] = np.average(
            frames, axis=1
        )
        stdev[i * chunkMaxSize : (i + 1) * chunkMaxSize] = np.std(
            frames.astype(np.float64), axis=1
        )
        # f.seek(chunkMaxSize*1024*512*2*i) #not needed, np.fromfile moves the pointer

    # In cases where the number of frames in .dat file aren't exact multiple of 6 * chunk_size
    if remainingframes > 0:
        # Last partial chunk
        chunk = np.fromfile(f, dtype=np.uint16, count=remainingframes * 1024 * 512)
        frames = chunk.reshape((remainingframes, 1024 * 512))
        brightness[-remainingframes:] = np.average(frames, axis=1)
        stdev[-remainingframes:] = np.std(frames.astype(np.float64), axis=1)

    # Close file containing frames
    f.close()

    # Threshold brightness to find flashes
    brightnessB = brightness - np.average(brightness)
    if os.path.exists(os.path.join(input_folder, "BFP.txt")):
        # TODO: Move Magic number somewhere else
        stdevbrightness = np.std(brightnessB[: nIterations - 12000])
    else:
        stdevbrightness = np.std(brightnessB)

    # If the flash shows up in two or more consecutive frames, this will list a
    # flash in each of them.
    (flashLocRepeated,) = np.where(brightnessB > stdevbrightness * 10)

    # Select only first frame of multiple in which the same flash shows up.
    flashLoc = []
    nFlashRep = len(flashLocRepeated)
    for nf in np.arange(nFlashRep):
        if nf == 0:
            flashLoc.append(flashLocRepeated[nf])
        else:
            if flashLocRepeated[nf] != flashLocRepeated[nf - 1] + 1:
                flashLoc.append(flashLocRepeated[nf])

    flashLoc = np.array(flashLoc)

    framesDetails = np.loadtxt(
        os.path.join(input_folder, "framesDetails.txt"), skiprows=1
    ).T
    framesSync = np.loadtxt(
        os.path.join(input_folder, "other-frameSynchronous.txt"), skiprows=1
    ).T

    # TODO: this wasn't commented on the lab's version, only did so to pass the pre-commit checks
    # utilities = np.loadtxt(
    #    os.path.join(input_folder, "other-volumeMetadataUtilities.txt"), skiprows=1
    # ).T

    frameIdx = framesDetails[1]
    frameTime = framesDetails[0]
    volumeIndex = np.zeros_like(framesDetails[1], dtype=np.float64)  # was np.int32....
    Z = np.zeros_like(framesDetails[1], dtype=np.float64)
    xPos = (
        np.ones_like(framesDetails[1]) * -1000
    )  # large number so we can check for this later
    yPos = (
        np.ones_like(framesDetails[1]) * -1000
    )  # large number so we can check for this later
    ZframeSync = framesSync[1]

    vindold = -1
    vsignold = 0
    # xpos = 0.0
    # ypos = 0.0
    for i in np.arange(len(framesDetails[1])):
        frameindex = framesDetails[1][i]

        # Assign a volume index to each frame
        j1B = np.where(framesSync[0] == frameindex)[0]
        if len(j1B) != 0:
            j1 = j1B[0]

            if framesSync[2, j1] != vsignold:
                vindold += 1
            vsignold = framesSync[2, j1]
            volumeIndex[i] = vindold
            Z[i] = ZframeSync[j1]
            xPos[i] = framesSync[4, j1]
            yPos[i] = framesSync[5, j1]
        else:
            volumeIndex[i] = vindold

    # second pass to assign correct Z and positions to frames
    Q = len(Z)
    for q in np.arange(Q):
        if Z[q] == 0.0 and q > 0 and q < Q - 1:
            Z[q] = (Z[q - 1] + Z[q + 1]) / 2.0
        if xPos[q] == -1000.0 and q > 0 and q < Q - 1:
            xPos[q] = (xPos[q - 1] + xPos[q + 1]) / 2.0
        if yPos[q] == -1000.0 and q > 0 and q < Q - 1:
            yPos[q] = (yPos[q - 1] + yPos[q + 1]) / 2.0

    # framesDetails = np.loadtxt(folder+"framesDetails.txt",skiprows=1).T
    frameTime = framesDetails[0]
    frameCount = framesDetails[1].astype(int)

    frameSync = np.loadtxt(
        os.path.join(input_folder, "other-frameSynchronous.txt"), skiprows=1
    ).T
    frameCountDAQ = frameSync[0].astype(int)
    latencyShift = 0
    if latencyShift != 0:
        frameCountDAQ += latencyShift
        print("Applying latency shift " + str(latencyShift))
    volumeIndexDAQ = frameSync[3].astype(int)
    volumeDirectionDAQ = frameSync[2].astype(int)
    ZDAQ = frameSync[1]

    # Correct frameCount: sometimes the frameCount jumps by 2 at one step
    # and by 0 at the next one.
    frameCountCorr = np.copy(frameCount)
    dframeCount = np.diff(frameCount)

    for i in np.arange(len(frameCount) - 1):
        if dframeCount[i] == 0 and dframeCount[i - 1] == 2:
            frameCountCorr[i] -= 1

    frameCount = frameCountCorr

    # Get the volume to which each frame in FrameDetails belongs from the DAQ data
    volumeIndex = np.ones_like(frameCount) * (-10)
    # TODO: Had dtype=np.int8 but latest numpys don't allow us to assign
    #   np.nan to the array later on, as we do here.
    volumeDirection = np.empty(len(frameCount))
    volumeDirection[:] = np.nan
    Z = np.empty(len(frameCount), dtype=float)
    Z[:] = np.nan
    for i in np.arange(len(frameCount)):
        try:
            indexInDAQ = np.where(frameCountDAQ == frameCount[i])
            volumeIndex[i] = volumeIndexDAQ[indexInDAQ]
            Z[i] = ZDAQ[indexInDAQ]
            volumeDirection[i] = (volumeDirectionDAQ[indexInDAQ] + 1) // 2
        # TODO: this was simply a bare exception in the lab's version
        # Changed it to pass the pre-commit checks
        except ValueError:
            pass

    # Interpolate missing values for Z and volumeDirection
    nans, x = np.isnan(Z), lambda z: z.nonzero()[0]
    Z[nans] = np.interp(x(nans), x(~nans), Z[~nans])
    volumeDirection[nans] = np.interp(x(nans), x(~nans), volumeDirection[~nans]).astype(
        np.int8
    )

    # Smooth Z
    smn = 4
    sm = np.ones(smn) / smn
    Z_sm = np.copy(Z)
    Z_sm = np.convolve(Z, sm, mode="same")

    # Derivative of Z
    volumeDirection[:-1] = np.sign(np.diff(Z_sm))
    volumeDirection[-1] = volumeDirection[-2]
    volumeDirection = (volumeDirection + 1) // 2
    volumeIndex = np.cumsum(np.absolute(np.diff(volumeDirection)))

    Mat = {}
    dataAll = {
        "imageIdx": (frameIdx - frameIdx[0] + 1).reshape((frameIdx.shape[0], 1)),
        "frameTime": (frameTime).reshape((frameTime.shape[0], 1)),
        "flashLoc": (flashLoc + 1).reshape((flashLoc.shape[0], 1)),
        "stackIdx": (volumeIndex + 1).reshape((volumeIndex.shape[0], 1)),
        "imSTD": stdev.reshape((stdev.shape[0], 1)),
        "imAvg": brightness.reshape((brightness.shape[0], 1)),
        "xPos": xPos.reshape((xPos.shape[0], 1)),
        "yPos": yPos.reshape((yPos.shape[0], 1)),
        "Z": Z.reshape((Z.shape[0], 1)),
    }
    Mat["dataAll"] = dataAll

    sio.savemat(os.path.join(output_folder, "hiResData.mat"), Mat)

    stringa = "NFrames " + str(
        int(volumeIndex[-1])
    )  # needs to be int or tk doesn't like it

    f = open(os.path.join(output_folder, "submissionParameters.txt"), "w")
    f.write(stringa)
    f.close()
