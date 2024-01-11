"""
This script is meant to play the same role as CenterlineFromVideo.py does in the old pipeline
"""
from tensorflow.keras.models import load_model
from importlib.resources import path
import glob
import os
import scipy.io as sio
import cv2
import numpy as np
import tensorflow as tf
from tqdm import tqdm
import matplotlib.pyplot as plt

from wbi.legacy.cline.centerline_funcs import extract_centerline
from wbi.legacy.cline.plot_cline import plot_centerline
from wbi.matlab.imresize import imresize
from wbi.data.ondemand import get_file


def find_worm_centered(center_line):
    numframes = center_line.shape[2]
    numcurvpts = center_line.shape[0]-2

    tanvecs = np.zeros((numcurvpts+1, 2, numframes))
    atdf2 = np.zeros((numcurvpts+1, numframes))
    wormcentered = np.zeros((numcurvpts+1, numframes))

    for j in range(numframes):
        # calculate tangent vector along curve (not normalized)
        df2 = np.diff(center_line[:, :, j], axis=0)
        tanvecs[:, :, j] = df2
        # angle of tangent vector. unwrapped to avoid 2pi jumps
        angles = np.unwrap(np.arctan2(-df2[:, 1], df2[:, 0]))
        atdf2[:, j] = angles

        # subtract average theta to get 'wormcentered' coords
        avg = np.mean(angles)

        wormcentered[:, j] = angles - avg

    return wormcentered


def clineFromVideo(path_cam, output_folder=None,plot=False, max_frames=None):
    """
    A method that does approximately the same thing as CenterlineFromVideo.Video2Centerlines()
    """
    cap = cv2.VideoCapture(path_cam)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if max_frames is not None:
        frame_count = min(frame_count, max_frames)

    model = load_model(get_file("best_model.h5"))

    # create a new folder containing the centerline images frame-by-frame

    if output_folder is None:
        output_folder = os.path.dirname(os.path.abspath(path_cam))

    # generate two folders alongside cam1.avi
    cl_img_dir = os.path.join(output_folder, "centerline_img")
    err_dir = os.path.join(output_folder, "err_frame")

    os.makedirs(cl_img_dir,exist_ok=True)
    os.makedirs(err_dir, exist_ok=True)

    size = model.input_shape[1]

    cline_arr = []

    for i in tqdm(range(frame_count)):
        ret, frame = cap.read()

        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # This is a hacky solution to only infer on part of the image, this limits the fov.
        # The following lines preprocess the image for prediction
        image = image[:, :2048]
        image = cv2.resize(image, (
        size, size))  # Resize to model's expected input size

        image = image[:, :,
                np.newaxis] / 255.0  # Normalize and add channel dimension

        def get_centerline(img):

            try:
                preds = model.predict_on_batch(tf.expand_dims(img, axis=0))
                predicted_mask = (preds.squeeze() > 0.5)
                x, y, centerline = extract_centerline(predicted_mask,
                                                      num_points=100)

                if plot:
                    # plot the centerline and save the image
                    plot_centerline(image, preds, x, y, centerline)
                    plt.savefig(f"{cl_img_dir}/centerline_{i:06d}.png",
                                dpi=500)

            except Exception as e:

                if plot:
                    # plot the raw image if there's no centerline output.
                    plt.imshow(image.squeeze(), cmap="gray")
                    plt.axis('off')
                    plt.savefig(f"{err_dir}/centerline_{i:06d}.png", dpi=500)

                print(f"Error during frame {i}:", e)
                return [[np.nan, np.nan]] * 100

            plt.close()

            return centerline * 2048 / size

        cl = get_centerline(image)
        cline_arr.append(cl)
    cline_arr = np.moveaxis(np.array(cline_arr), 0,
                            2)  # (num_points, 2, num_frames)

    return cline_arr


def make_centerline(input_folder, output_folder=None, max_frames=None, plot=False):
    avi_path = glob.glob(f'{input_folder}/LowMagBrain*/cam1.avi')
    if not len(avi_path) == 1:
        raise FileNotFoundError("The cam1.avi file is not found")
    else:
        avi_path = avi_path[0]
        center_line = clineFromVideo(avi_path, output_folder=output_folder, plot=plot, max_frames=max_frames)

        if output_folder is None:
            output_folder = os.path.join(input_folder, 'BehaviorAnalysis')
        os.makedirs(output_folder, exist_ok=True)

        with path('wbi.data', 'eigenWorms.mat') as eigenworms_path:
            eigbasis = sio.loadmat(eigenworms_path)['eigbasis']  # 6x101

        worm_centered = find_worm_centered(center_line)
        eigbasis_resized = imresize(eigbasis, output_shape=(
        eigbasis.shape[0], worm_centered.shape[0]))
        eigenProj = eigbasis_resized @ worm_centered

        sio.savemat(os.path.join(output_folder, 'centerline.mat'), {
            'centerline': center_line,
            'eigenProj': eigenProj,
            'wormcentered': worm_centered
        })