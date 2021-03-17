import os
import numpy as np
from astropy.stats import sigma_clip
from astropy.io import fits

def make_dir(path):
    """Creates folders specified in a given path if they don't already exist.
    
    Parameters
    ----------
    path : str
        path containing folders to be created.
    """
    final_path = '.'
    for folder in path.split('/'):
        if folder not in os.listdir(final_path):
            os.mkdir(final_path+'/'+folder)
        final_path += '/'+folder

def empty_master(path):
    """Creates an empty array based on the size of fits files in the given path.
    
    Parameters
    ----------
    path : str
        path to folder containing fits files.

    Returns
    -------
    numpy array
        empty matrix with the same shape as specifed images.
    """
    for file in os.listdir(path):
        if 'fits' in file:
            file_path = path+'/'+file
            header = fits.getheader(file_path)
            # get shape of fits image
            col = header['NAXIS1']
            row = header['NAXIS2']
            # get overscan
            cover = header['COVER']
            rover = header['ROVER']
            # return an empty 
            return np.zeros((col-cover,row-rover))
    print('There are no fits files in folder')

def overscan(path):
    """Collects fits file and removes overscan.
    
    Parameters
    ----------
    path : str
        fits file image path
    
    Returns
    -------
    numpy array
        return fits image with overscan removed
    """
    cover = fits.getheader(path)['COVER']  
    rover = fits.getheader(path)['ROVER']
    data = fits.getdata(path)
    data = np.delete(data,np.s_[len(data[1])-cover:],1)
    data = np.delete(data,np.s_[len(data[0])-rover:],0)
    return data

def get_bias(path,save_path=None):
    """Creates a master bias frame.
    
    Collects bias frames from a specified path. Check exposure time of each file
    to ensure that it is a bias frame then factors for overscan. Outliers past five
    standard deviations of the mean are removed before all bias frames are averaged into
    the master bias.

    Parameters
    ----------
    path : str
        path to bias frames    
    
    save_path : str, optional
        path to location where master bias will be saved. (default is none)

    Returns
    -------
    numpy array
        master bias as a numpy matrix
    """
    count = 0
    master_bias = empty_master(path)
    for file in os.listdir(path):
        # make sure to only use fits files
        if 'fits' in file:
            file_path = path+'/'+file
            # make sure image is a bias by looking at exposure time
            if fits.getheader(file_path)['EXPTIME'] == 0:
                # collect data
                count += 1        
                # collect data and remove overscan
                data = overscan(file_path)
                # sigma clip
                data = sigma_clip(data,5)
                # add to master
                master_bias+=data
            else:
                print('File %s is not a bias image, exposure time must be equal to zero.' % file)
    # get everage
    master_bias = master_bias/count

    if save_path != None:
        make_dir(save_path)
        hdu = fits.PrimaryHDU(master_bias)
        hdu.writeto(save_path+'/Bias.fits',overwrite=True)

    return master_bias

def get_dark(path,master_bias,save_path=None):
    """Creates a master dark frame
    
    Takes master bias frame, or creates master bias is path is given. Collects dark frames 
    from a specified path, corrects frames for bias, then converts pixel values to units
    of counts/seconds. Outliers past five standard deviations of the mean are removed 
    before all dark frames are averaged into the master dark.

    Parameters
    ----------
    path : str
        path to dark frames. 

    master_bias: str, numpy array
        str - path to bias frames.
        numpy array - master bias file.
    
    save_path : str, optional
        path to location where master dark will be saved. (default is none)

    Returns
    -------
    numpy array
        master dark as a numpy matrix.
    """    
    # create master bias if path is provided
    if type(master_bias) == str:
        master_bias = get_bias(master_bias)
    count = 0
    master_dark = empty_master(path)
    for file in os.listdir(path):
        # make sure to only use fits files
        if 'fits' in file:
            file_path = path+'/'+file
            # collect data
            count += 1        
            time = fits.getheader(file_path)['EXPTIME']
            # deal with overscan
            data = overscan(file_path)
            # callibrate
            data = (data-master_bias)/time
            # sigma clip
            data = sigma_clip(data,5)
            # add to master
            master_dark+=data
    # get average
    master_dark = master_dark/count

    if save_path != None:
        make_dir(save_path)
        hdu = fits.PrimaryHDU(master_dark)
        hdu.writeto(save_path+'/Dark.fits',overwrite=True)

    return master_dark

def get_flat(path,master_bias,master_dark,save_path=None):
    """Creates a master flat image.    
    
    Takes master bias and master dark frames, or creates them using the paths given. Collects 
    flat frames from a specified path. Corrects frames for bias, then converts pixel values 
    to units of counts/seconds, before correcting for dark current. Outliers past five
    standard deviations of the mean are removed before all flat frames are normalzed then 
    averaged into the master flat.

    Parameters
    ----------
    path : str
        path to dark frames.    

    master_bias: str, numpy array
        str - path to bias frames.
        numpy array - master bias file.

    master_dark: str, numpy array
        str - path to dark frames.
        numpy array - master dark file.
    
    save_path : str, optional
        path to location where master flat will be saved. (default is none)

    Returns
    -------
    numpy array
        master flat as a numpy matrix.
    """   
    # create master bias and master dark if path is provided
    if type(master_bias) == str:
        master_bias = get_bias(master_bias)
    if type(master_dark) == str:
        master_dark = get_dark(master_dark,master_bias)
    count = 0
    master_flat = empty_master(path)
    for file in os.listdir(path):
        # make sure to only use fits files
        if 'fits' in file:
            file_path = path+'/'+file
            # collect data
            count += 1        
            time = fits.getheader(file_path)['EXPTIME']
            # deal with overscan
            data = overscan(file_path)
            # callibrate
            data = ((data-master_bias)/time ) - master_dark
            # sigma clip
            data = sigma_clip(data,5)
            # add to master
            master_flat+=data/np.amin(data)
    # get average
    master_flat = master_flat/count

    if save_path != None:
        make_dir(save_path)
        hdu = fits.PrimaryHDU(master_flat)
        hdu.writeto(save_path+'/Flat.fits',overwrite=True)

    return master_flat

def get_science(path,master_bias,master_dark,master_flat,save_path=None):
    """Collects and calibrates science frames.   
    
    Takes master bias, master dark, and master flate frames, or creates them using the paths
    given. Collects science frames from a specified path then corrects frames using master 
    bias, master dark, and master flat frames.

    Parameters
    ----------
    path : str
        path to dark frames.    

    master_bias: str, numpy array
        str - path to bias frames.
        numpy array - master bias file.

    master_dark: str, numpy array
        str - path to dark frames
        numpy array - master dark file.

    master_flat: str, numpy array
        str - path to flat frames.
        numpy array - master flat file.
    
    save_path : str, optional
        path to location where all calibrated science files will be saved. (default is none)

    Returns
    -------
    list
        list containing all calibrated science frames as numpy matrices.
    """   
    # create master bias and master dark if path is provided
    if type(master_bias) == str:
        master_bias = get_bias(master_bias)
    if type(master_dark) == str:
        master_dark = get_dark(master_dark,master_bias)
    if type(master_flat) == str:
        master_flat = get_flat(master_flat,master_bias,master_dark)
    reduced_science = []
    count=1
    for file in os.listdir(path):
        # make sure to only use fits files
        if 'fits' in file:
            file_path = path+'/'+file
            # collect data       
            header = fits.getheader(file_path)
            time = header['EXPTIME']
            error = header['CRDER2S']
            # deal with overscan
            data = overscan(file_path)
            # callibrate
            data = ( ((data-master_bias)/time ) - master_dark ) / master_flat
            # remove CCD artifacts
            data = remove_lines(data)
            # append
            reduced_science.append([file,data])

            if save_path != None:
                make_dir(save_path)
                hdr = fits.Header()
                hdr.set('ERROR',error)
                hdu = fits.PrimaryHDU(data,header=hdr)
                hdu.writeto(save_path+'/Sci_'+str(count)+'.fits',overwrite=True)
            count+=1
                
    return reduced_science 

def remove_lines(img,max_lim=95,min_lim=10):
    """Removes CCD artifacts.
    
    Flattens image by column, aggregating by sum. Outlires are found by finding the index
    of columns with sum values outside the specified percentile thresholds. Pixels in these
    columns are then replaced by the median of nearby pixels in the row. 

    Parameters
    ----------
    img : numpy array
        image to be corrected.

    max_lim: int, float, optional
        upper percentile limit, values above this percentile are considered outliers. 
        (default = 95)
    
    min_lim: int, float, optional
        lower percentile limit, values below this percentile are considered outliers.
        (defualt = 10)

    Returns
    -------
    numpy array
        image with CCD artifacts removed.
    """
    data = img.copy()
    flat = np.sum(data, axis=0)
    # True for all columns with sum greater than the 95th percentile
    bright_lines = flat > np.percentile(flat,max_lim)
    # True for all columns with sum less than the 10th percentile
    dark_lines = flat < np.percentile(flat,min_lim)
    # get index of the outlier columns
    bright_lines = [index for index, value in enumerate(bright_lines) if value == True]
    dark_lines = [index for index, value in enumerate(dark_lines) if value == True]
    # replace the pixel values of each row in a column with the median of the 
    # closest pixels in the row
    for line_list in [bright_lines,dark_lines]:
        for col in line_list:
            for row in range(len(data)):
                index_list=[]
                for n in range(-5,6):
                    try: 
                        index_list.append(data[row][col+n])
                    except:
                        pass
                data[row][col] = np.median(index_list)
    return data   