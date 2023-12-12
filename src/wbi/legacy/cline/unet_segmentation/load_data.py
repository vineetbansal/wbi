from glob import glob
import utils
import wbi.legacy.cline.unet_segmentation.data_augmentation as data_augmentation
import numpy as np
from sklearn.model_selection import train_test_split

def generators(data_dir, size=1024):

    image_paths = sorted(glob(f"{data_dir}/img_*.png"))
    mask_paths = sorted(glob(f"{data_dir}/mask_img_*.png"))

    images = np.array([utils.load_image(path, size) for path in image_paths])
    masks = np.array([utils.load_image(path, size) for path in mask_paths])

    train_images, val_images, train_masks, val_masks = train_test_split(images, masks, test_size=0.2, random_state=42)
    train_generator = data_augmentation.data_augmentation(train_images, train_masks)

    val_generator = data_augmentation.data_augmentation(val_images, val_masks)

    return train_generator, val_generator