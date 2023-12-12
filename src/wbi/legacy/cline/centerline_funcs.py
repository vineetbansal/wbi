"""
A collection of functions related to center line of the worm
"""

import cv2
import numpy as np
from scipy import interpolate
from scipy.signal import savgol_filter


def _centerline_angle_curvature(predicted_mask, num_points= 50, angle=True, roll_angle = 10):
    """
    Extract the centerline from a binary segmentation of c elegans.
    Two methods are implemented in this functions: angle and curvature.

    They perform quite well, but both have many hyperparameters.

    parameters
    ----------
    predicted_mask:
        array of shape (N, N), representing a binary image of the worm.
    num_points:
        number of points along the centerline to sample from it.
    angle:
        Boolean variable representing which method to use,
    roll_angle:
        a integer representing the distance between the two vectors whose inner product is computed.
        in units of number of points.
    return
    ------
    x, y: 
        coordinates of the fitted contour.
    centerline:
        centerline represented, in either head-to-tail or tail-to-head order.
    """
    try:
        # I don't really know what this will output, maybe change it later.
        contours, _ = cv2.findContours(predicted_mask.astype("uint8"), 
            cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        len_list = [len(c) for c in contours]
        ct = contours[np.argmax(len_list)].squeeze().T
    except Exception as e:
        print("error during getting contour:", e)
        return  [[np.nan, np.nan]]

    # downsample ct for smooth interpolation
    ct = ct[:,::10]
    ct = np.hstack((ct,ct))

    tck, _ = interpolate.splprep(ct, s=64)
    t = np.linspace(0, 1, 500)
    x, y = interpolate.splev(t, tck)

    # compute the curvature of spline


    if angle:
        dy = interpolate.splev(t, tck, der=1)
        dy = np.array(dy)
        tan_vec = dy/np.sqrt(dy[0]**2+dy[1]**2)
        tan_vec_1 = np.roll(tan_vec, -roll_angle)
        cos = np.sum(tan_vec*tan_vec_1, axis=0)

        cos = savgol_filter(np.max(cos) - np.roll(cos, int(roll_angle/2)), 9,0)
        cos[0:250] += cos[:-250]
        cos = cos[0:250]

        metric = cos
    else:
        ddy = interpolate.splev(t, tck, der=2)
        curvature = np.sqrt(ddy[0]**2 + ddy[1]**2)

        curvature = savgol_filter(curvature, 9, 3)
        curvature[0:250] += curvature[:-250]
        curvature = curvature[0:250]

        metric = curvature

    idx1 = np.argmax(metric)
    metric = np.roll(metric, -idx1)

    low = int(0.25*len(metric))
    high = int(0.75*len(metric))
    idx = np.argmax(metric[low:high])+low


    x = np.roll(x[0:250], -idx1)
    y = np.roll(y[0:250], -idx1)

    x1 = x[np.linspace(0,idx,num_points, dtype="int")]
    y1 = y[np.linspace(0,idx,num_points, dtype="int")]

    x2 = x[np.linspace(idx,len(x)-1,num_points, dtype="int")]
    y2 = y[np.linspace(idx,len(x)-1,num_points, dtype="int")]

    x2 = x2[::-1]
    y2 = y2[::-1]

    centerline = np.array([(x1+x2)/2, (y1+y2)/2]).T

    return x, y, centerline



def extract_centerline(predicted_mask, num_points = 50, method="angle", **kwargs):
    """
    Wrapper for different methods to extract center line. Default method uses "angle"
    """
    methods = {
                "angle": _centerline_angle_curvature,
                "curvature": _centerline_angle_curvature
                }
    
    if method in methods:
        if method == "angle":
            return methods[method](predicted_mask, num_points, angle=True, **kwargs)
        elif method == "curvature":
            return methods[method](predicted_mask, num_points, angle=False, **kwargs)
        else:
            return methods[method](predicted_mask, num_points, **kwargs)
    else:
        print("Center line method not implemented")
        return None



def register_centerline(endnodes, centerline):
    """
    The direction of centerlines are not necessarily aligned
    This function makes sure that the centerlines are aligned. 

    """

    if np.isnan(endnodes).any() or np.isnan(centerline).any():
        return np.array([centerline[0], centerline[-1]]), centerline

    def compute_dist(ends, line):
       sum_dist = np.hypot(line[0][0] - ends[0][0], line[0][1] - ends[0][1]) + np.hypot(line[-1][0] - ends[1][0], line[-1][1] - ends[1][1])
       return sum_dist
    
    if compute_dist(endnodes, centerline) < compute_dist(endnodes, centerline[::-1]):
        return np.array([centerline[0], centerline[-1]]), centerline
    else:
        return np.array([centerline[-1], centerline[0]]), centerline[::-1]