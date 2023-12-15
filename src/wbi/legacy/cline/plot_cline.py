"""
A function that plots the centerline.
"""
import matplotlib.pyplot as plt

def plot_centerline(image, preds, x,y, centerline):
    """
    plot the image, with confidence map, contour, and centerline overlayed on top

    """
    cl = centerline.T

    _, ax = plt.subplots()
    # display raw image
    ax.imshow(image.squeeze(), cmap="gray")
    
    # plot the centerline and contour
    ax.plot(cl[0],cl[1], linewidth=0.5, color='orange')
    ax.plot(x,y, linewidth=0.1, color='blue')

    # plot the first point of the center line
    ax.scatter(cl[0][0], cl[1][0], s=0.5, color='red')

    # plot confidence map and colorbar.
    conf_map = ax.imshow(preds.squeeze(), cmap="Blues", alpha=0.25)
    cbar = plt.colorbar(conf_map, ax=ax, fraction=0.04, pad=0.04) 

    cbar.set_ticks([0, 0.2, 0.4, 0.6, 0.8, 1])

    ax.axis('off')
    plt.tight_layout(pad=0)