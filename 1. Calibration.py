
import json 
import Functions.calibration_functions as calfunc

# LOAD CONFIG
#
# Loads the paths to each frame type specified in the file ‘calibration_config.json’.

with open('Config/calibration_config.json') as f:
    paths = json.load(f)
from_path = paths['path_raw']+'/'
save_path = paths['path_clean']+'/'

# BIAS CALIBRATION
#
# Bias frames are images taken instantaneously thus only have an exposure time of zero 
# seconds. These frames are used to find and correct for the readout noise, or bias, of
# each pixel on the camera. Typically, ten or more bias frames are averaged into a 
# master bias which is subtracted from all frames.

bias_path = paths['bias']['path']
master_bias = calfunc.get_bias(from_path+bias_path,save_path+bias_path)

# DARK CALIBRATION
#
# Dark frames are images taken with long exposure times (typically a couple minutes) with
# a closed shutter. This helps factor for the dark current, the noise that develops when
# the camera heats up due to prolonged use. Typically ten or more dark frames will be 
# averaged into master dark which will be subtracted from all frames after the master bias
# has been applied and the frame pixel values have been converted to units of 
# counts-per-second by dividing the image by it’s exposure time. 

dark_path = paths['dark']['path']
master_dark = calfunc.get_dark(from_path+dark_path,master_bias,save_path+dark_path)

# FLAT CALIBRATION 
#
# Flat frames are images of an evenly illuminated subject (typically an image of the uniform
# twilight sky or using some kind of filter to evenly spread light). These images help 
# correct any non-uniform sensitivities of the camera as well as remove any dust or debris
# that may have accumulated. Typical ten or more flat frames will be normalized then 
# averaged, before being divided from the rest of the frames after the application of the 
# master bias and master dark. Different flat frames must be made for different camera 
# settings( in the case of my experiment the different light bands). 

master_flat = dict()
for band in paths['flat'].keys():
    flat_path = paths['flat'][band]
    master_flat[band] = calfunc.get_flat(from_path+flat_path,master_bias,master_dark,save_path+flat_path)

# SCIENCE CALIBRATION 
#
# Science frames are the images of the target of observation. For these images to be properly
# calibrated, they must be subtracted by the master bias, converted to units of 
# counts-per-seconds, subtracted by the master dark, then divided by the master flat. This 
# should provide the clearest image, free of the imperfection of the camera.

for star in paths['science'].keys():
    for n, band in enumerate(paths['science'][star]['band']):
        sci_path = paths['science'][star]['path'][n]
        calfunc.get_science(from_path+sci_path, master_bias, master_dark, master_flat[band],save_path+sci_path)