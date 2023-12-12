import numpy as np
import cv2


def load_image(path, size = 1024):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    img = img[:, -2048:]
    img = cv2.resize(img, (size, size))  # Resize to model's expected input size
    return img[:,:, np.newaxis] / 255.0  # Normalize and add channel dimension