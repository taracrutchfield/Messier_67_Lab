import matplotlib.pyplot as plt
import numpy as np

def see_image(data,percentile=85,title=None):
    """Easily plots fits file.

    Honestly I just made this because I'm lazy and don't want to type out the whole np.percentile(...)
    numerous times. Using the percentile limits are often the only way to see any features on these images.
    
    Parameters
    ----------
    data : numpy array
        fits file images you wish to visualize.
        
    percentile : int, float between 1-100, optional
        percentile of data you with to see. (default = 85)

    title : str, optional
        title of image. (default = None)

    Returns
    -------
    AxesImage
    """
    percentile = (100-percentile)/2
    ax = plt.imshow(data, vmin=np.percentile(data, percentile), vmax = np.percentile(data, 100-percentile))
    if title != None:
        plt.title(title)
    plt.xlabel('pixel column')
    plt.ylabel('pixel row')
    return ax