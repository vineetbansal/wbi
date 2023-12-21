import numpy as np
import os.path
import glob
import cv2
import logging
import matplotlib.pyplot as plt
from scipy.io import savemat
from wbi.timing import Timing, LowMagTiming, FrameSynchronous
from wbi.dat import Dat

logger = logging.getLogger(__name__)


class Experiment:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.timing = Timing(folder_path)
        self.dat = Dat(folder_path)
        self.frames_sync = FrameSynchronous(folder_path, latency_shift=0)

        lowmag_folders = glob.glob(f"{folder_path}/LowMagBrain*")
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

    def configure_frame_positions(self):
        volume_index = np.zeros_like(self.timing.timing["frame"], dtype=np.float64)
        z_pos = np.zeros_like(self.timing.timing["frame"], dtype=np.float64)
        x_pos = np.ones_like(self.timing.timing["frame"]) * -1000
        y_pos = np.ones_like(self.timing.timing["frame"]) * -1000
        volume_index_old = -1
        volume_sign_old = 0

        for i, frame in enumerate(self.timing.timing["frame"]):
            matching_indexes = np.where(self.frames_sync.sync["frame"] == frame)[0]

            if len(matching_indexes):
                matching_index = matching_indexes[0]
                try:
                    if (
                        self.frames_sync.sync["piezo_direction"][matching_index]
                        != volume_sign_old
                    ):
                        volume_index_old += 1

                    volume_sign_old = self.frames_sync.sync["piezo_direction"][
                        matching_index
                    ]
                    volume_index[i] = volume_index_old
                    z_pos[i] = self.frames_sync.sync["piezo_position"][matching_index]
                    x_pos[i] = self.frames_sync.sync["ludl_x"][matching_index]
                    y_pos[i] = self.frames_sync.sync["ludl_y"][matching_index]
                except KeyError:
                    pass
            else:
                volume_index[i] = volume_index_old

        n_positions = len(z_pos)
        for index in np.arange(n_positions):
            if z_pos[index] == 0.0 and 0 < index < n_positions - 1:
                z_pos[index] = (z_pos[index - 1] + z_pos[index + 1]) / 2.0
            if x_pos[index] == -1000.0 and 0 < index < n_positions - 1:
                x_pos[index] = (x_pos[index - 1] + x_pos[index + 1]) / 2.0
            if y_pos[index] == -1000.0 and 0 < index < n_positions - 1:
                y_pos[index] = (y_pos[index - 1] + y_pos[index + 1]) / 2.0

        return x_pos, y_pos, z_pos

    def configure_frame_timings(self, data_folder):
        frame_count = self.timing.timing["frame"].astype(int)
        frame_count_daq = self.frames_sync.sync["frame"].astype(int)

        if self.frames_sync.latency_shift:
            frame_count_daq += self.frames_sync.latency_shift
            logger.info(f"Applying latency shift {self.frames_sync.latency_shift}")

        d_frame_count = np.diff(frame_count)

        for i in np.arange(len(frame_count) - 1):
            if d_frame_count[i] == 0 and d_frame_count[i - 1] == 2:
                frame_count[i] -= 1

        volume_index = np.ones_like(frame_count) * -10
        volume_direction = np.empty(len(frame_count))
        volume_direction[:] = np.nan
        piezo_position = np.full(frame_count.shape, np.nan, dtype=float)
        for i, element in enumerate(frame_count):
            try:
                index_in_daq = (
                    np.where(frame_count_daq == element)[0][0]
                    if len(np.where(frame_count_daq == element)[0]) > 0
                    else None
                )
                piezo_position[i] = self.frames_sync.sync["piezo_position"][
                    index_in_daq
                ]
                volume_direction[i] = (
                    self.frames_sync.sync["piezo_direction"][index_in_daq] + 1
                ) // 2
            except KeyError:
                pass

        nans, non_zeros = np.isnan(piezo_position), lambda z: z.nonzero()[0]
        piezo_position[nans] = np.interp(
            non_zeros(nans), non_zeros(~nans), piezo_position[~nans]
        )
        volume_direction[nans] = np.interp(
            non_zeros(nans), non_zeros(~nans), volume_direction[~nans]
        ).astype(np.int8)

        smn = 4
        sm = np.ones(smn) / smn
        piezo_sm = np.convolve(piezo_position, sm, mode="same")

        volume_direction[:-1] = np.sign(np.diff(piezo_sm))
        volume_direction[-1] = volume_direction[-2]
        volume_direction = (volume_direction + 1) // 2
        volume_index = np.cumsum(np.absolute(np.diff(volume_direction)))

        return volume_index
