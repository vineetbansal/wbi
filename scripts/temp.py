import numpy as np
from scipy.optimize import curve_fit
from scipy.io import loadmat
from wbi.experiment import Experiment
from wbi.matlab.misc import smooth


def poly1(x, m, c):
    return m * x + c


def poly1b(x, a):
    return a * x


def flash_time_align(flashA, flashB):
    # If length of flashB is 1, find the closest match in flashA
    if len(flashB) == 1:
        min_dist_idx = np.argmin(np.abs(flashA - flashB))
        idx_out = np.array([0, min_dist_idx])
        output_offset = np.array([min_dist_idx])
        return idx_out, output_offset

    best = np.inf

    for i in range(len(flashB)):
        for j in range(len(flashA)):
            offset = flashA[j] - flashB[i]
            ab_dist = np.abs(flashA[:, None] - (flashB + offset))
            mindist_idx = np.argmin(ab_dist, axis=0)
            mindist = ab_dist[mindist_idx, :].trace()
            if mindist < best:
                best = mindist
                output_offset = mindist_idx

    return output_offset


def timefit(bestFlashTime, sampleFlashTime):
    bf2fluor = flash_time_align(bestFlashTime, sampleFlashTime)

    flash_diff = sampleFlashTime - bestFlashTime[bf2fluor]
    flash_diff -= flash_diff.min()

    if len(sampleFlashTime) > 1:
        weights = np.exp(-(flash_diff**2))
        # NOTE: MATLAB `fit` uses weights, scipy `curve_fit` uses sigma
        sigma = np.diag([1 / w for w in weights])
        params, covariance = curve_fit(
            f=poly1, xdata=sampleFlashTime, ydata=bestFlashTime[bf2fluor], sigma=sigma
        )
        m, c = params
        if m < 0.1:
            m = 1.0  # TODO: Why?
    else:
        coeff_init = 1
        myarray = -sampleFlashTime[0] + bestFlashTime[bf2fluor]
        params, covariance = curve_fit(
            f=poly1b, xdata=myarray, ydata=myarray * coeff_init
        )
        (m,) = params
        c = 0

    return m, c


if __name__ == "__main__":

    e = Experiment("/bs")
    bfFlash = loadmat("/bs/LowMagBrain20231024_153442/cam1flashTrack.mat")["imFlash"][0]
    bfFlash -= smooth(bfFlash, 200)
    bfFlash -= bfFlash.min()
    bfFlashLoc = np.where(bfFlash > bfFlash.mean() + 5 * bfFlash.std())[0]
    differences = np.diff(bfFlashLoc)
    # Get rid of double peaks too close to each other
    mask = np.concatenate([np.array([True]), differences >= 3])
    bfFlashLoc = bfFlashLoc[mask]

    e.timing_lowmag.fix_repeats()

    bfAll = {
        "frametime": e.timing_lowmag.time_deltas(),
        "flashTrack": bfFlash,
        "flashLoc": bfFlashLoc,
        "stageX": e.timing_lowmag.timing["stage_x"]
        if e.timing_lowmag.has_stage_data
        else None,
        "stagey": e.timing_lowmag.timing["stage_y"]
        if e.timing_lowmag.has_stage_data
        else None,
    }

    hiResFlashTime = e.hires_data.flash_times()
    bfFlashTime = e.timing_lowmag.time_deltas()[bfFlashLoc]

    if len(hiResFlashTime) > len(bfFlashTime):
        bestFlashTime = hiResFlashTime
    else:
        bestFlashTime = bfFlashTime

    if len(hiResFlashTime) == 0 or len(bfFlashTime) == 0:
        raise RuntimeError("Flashes not detected in all of the videos")

    m, c = timefit(bestFlashTime, bfFlashTime)
    bfAll_frametime = poly1(bfAll["frametime"], m=m, c=c)

    m, c = timefit(bestFlashTime, hiResFlashTime)
    hisResData_frameTime = poly1(e.hires_data.frame_times_delta(), m=m, c=c)

    volume_index = e.hires_data.data[0, 0]["stackIdx"].squeeze()
    # stackIdx was saved with a length 1 less than it should have.
    # We prepend the first element to it so we can subset using it
    # This works in the MATLAB case since an array can be indexed using a bool
    # array that is shorter in length than the array being indexed
    # (in which case the logical array is left aligned to the array being
    # indexed)
    # volume_index = np.array(volume_index[0] + volume_index.tolist())
    print("debug")
