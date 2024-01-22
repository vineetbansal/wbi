import numpy as np
import os
import os.path
import glob
import cv2
import logging
import matplotlib.pyplot as plt
from scipy.io import savemat
import shutil
from wbi.timing import Timing, LowMagTiming, FrameSynchronous
from wbi.dat import Dat
from wbi import config

logger = logging.getLogger(__name__)


class Experiment:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.dat = Dat(folder_path)
        self.timing = Timing(folder_path)
        self.frames_sync = FrameSynchronous(folder_path)
        if self.frames_sync is not None:
            self.timing_dataframe = self.timing.merge_sync(self.frames_sync)

        lowmag_folders = glob.glob(f"{folder_path}/LowMagBrain*/")
        if len(lowmag_folders) != 1:
            raise RuntimeError(f"Cannot find LowMagBrain* folder in {folder_path}")
        self.lowmag_folder = lowmag_folders[0]

        self.timing_lowmag = LowMagTiming(self.lowmag_folder)
        self.avi_files = glob.glob(f"{self.lowmag_folder}/*.avi")

    def median_images_himag(self):
        for chunk in range(self.timing.n_chunks):
            yield self.median_image_himag(chunk)

    def median_image_himag(self, chunk):
        start, end = self.timing.get_start_end_row_indices(chunk)
        img = self.dat.load(count=end - start, offset=start)
        img = np.median(img, axis=-1)
        return img

    def median_images_lomag(self):
        logger.warning(
            "LowMag images are generated only for the first LowMag*/*.avi file"
        )

        avi_file = self.avi_files[0]
        cap = cv2.VideoCapture(avi_file)
        number_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        for frame_number in range(number_of_frames):
            _, frame = cap.read()
            mean_frame = np.mean(frame, axis=2)  # type: ignore
            yield mean_frame

    def generate_median_images(self, output_folder=None, tif=True):

        self.generate_cameraframedata_files(output_folder)

        output_folder_himag = output_folder or self.folder_path
        os.makedirs(output_folder_himag, exist_ok=True)

        for i, img in enumerate(self.median_images_himag(), start=1):
            if tif:
                plt.imsave(
                    os.path.join(output_folder_himag, f"dat_{i}.tif"),
                    arr=img,
                    format="tiff",
                )
            else:
                # A more natural way to visualize median images
                red = img[: self.dat.rows, :]
                plt.imshow(red, cmap="viridis")
                plt.savefig(
                    os.path.join(output_folder_himag, f"mean_img_red_{i:06d}.jpg")
                )
                plt.close()

                green = img[self.dat.rows :, :]
                plt.imshow(green, cmap="viridis")
                plt.savefig(
                    os.path.join(output_folder_himag, f"mean_img_green_{i:06d}.jpg")
                )
                plt.close()

        output_folder_lowmag = output_folder or self.lowmag_folder
        for i, img in enumerate(self.median_images_lomag(), start=1):
            if tif:
                plt.imsave(
                    os.path.join(output_folder_lowmag, f"cam1_{i}"),
                    arr=img,
                    format="tiff",
                )
            else:
                # A more natural way to visualize median images
                plt.imshow(img, cmap="viridis")
                plt.savefig(os.path.join(output_folder_lowmag, f"mean_img_{i:06d}.jpg"))
                plt.close()

    def generate_flashtrack_files(self, output_folder=None):
        output_folder = output_folder or self.lowmag_folder
        for avi_file in self.avi_files:
            cap = cv2.VideoCapture(avi_file)
            number_of_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            mat = np.empty((1, number_of_frames)).astype(np.float64)
            for frame_number in range(number_of_frames):
                _, frame = cap.read()
                frame = frame[:, :, 0]
                mean_frame = np.mean(frame)  # type: ignore
                mat[0, frame_number] = mean_frame

            basename = os.path.splitext(os.path.basename(avi_file))[0]
            output_file = os.path.join(output_folder, f"{basename}flashTrack.mat")
            savemat(output_file, {"imFlash": mat}, do_compression=True)

    def generate_cameraframedata_files(self, output_folder=None):
        output_folder = output_folder or self.folder_path
        timing_df = self.timing.timing[["frame", "frame_index", "dc_offset", "stddev"]]
        timing_df.to_csv(
            os.path.join(output_folder, "CameraFrameData.txt"),
            header=["# Total Frames", "Saved Frames", "DC Offset", "Image Stdev"],
            sep="\t",
            index=False,
        )

    def flash_finder(self, output_folder=None, chunk_size=4000, max_frames=None):
        output_folder = output_folder or self.folder_path

        dat = self.dat
        n_frames = dat.n_frames if max_frames is None else min(max_frames, dat.n_frames)
        brightness = np.zeros(n_frames)
        stdev = np.zeros(n_frames)

        for index, chunk in enumerate(
            dat.chunks(chunk_size=chunk_size, max_frames=n_frames)
        ):
            brightness[index * chunk_size : (index + 1) * chunk_size] = np.average(
                chunk, axis=(0, 1)
            )
            stdev[index * chunk_size : (index + 1) * chunk_size] = np.std(
                chunk, axis=(0, 1)
            )

            term_width, _ = shutil.get_terminal_size()
            progress = (index * chunk_size) / n_frames
            block = int(round((term_width - 20) * progress))
            text = "\rProgress: [{0}] {1}%".format(
                "#" * block + "-" * (term_width - 20 - block), round(progress * 100, 2)
            )
            logger.info(f"{text}")

        adjusted_brightness = brightness - np.average(brightness)
        stdev_brightness = np.std(adjusted_brightness)

        (flash_loc,) = np.where(
            adjusted_brightness > stdev_brightness * config.flash_finder.std_factor
        )

        # Remove flash frames that are consecutive and thus represent the same flash
        flash_loc = flash_loc[np.nonzero(np.diff(flash_loc, prepend=-np.inf) != 1)]

        data = self.timing_dataframe
        # All the data we wish to save in a .mat file
        mat_data = {
            "imageIdx": data["frame_index"].to_numpy()[:, np.newaxis],
            "frameTime": data["time"].to_numpy()[:, np.newaxis],
            "flashLoc": (flash_loc + 1)[:, np.newaxis],  # 1-indexed
            # TODO: Legacy code is taking a diff without a prepend, thus ends up 1 shorter than all the rest
            # of the arrays here. We take values from 1: to emulate legacy behavior
            "stackIdx": (data["volume_index"].to_numpy() + 1)[1:, np.newaxis],
            # 1-indexed
            "imSTD": stdev[:, np.newaxis],
            "imAvg": brightness[:, np.newaxis],
            "xPos": data["ludl_x"].to_numpy()[:, np.newaxis],
            "yPos": data["ludl_y"].to_numpy()[:, np.newaxis],
            "Z": data["piezo_position"].to_numpy()[:, np.newaxis],
        }

        savemat(
            os.path.join(output_folder, "hiResData.mat"),
            mat_data,
        )

        # TODO: The following file is generated for legacy reasons
        max_volume_index = data["volume_index"].max()
        with open(os.path.join(output_folder, "submissionParameters.txt"), "w") as f:
            f.write(f"NFrames {max_volume_index}")

        return mat_data
