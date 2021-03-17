import numpy as np
import photutils

def photometry(file,file_err,coord,radius):
    aperture = photutils.CircularAperture(coord,radius)
    annulus_aperture = photutils.CircularAnnulus(coord, r_in=2*radius, r_out=(2*radius + 2))        
    photometry_table = photutils.aperture_photometry(file, [aperture,annulus_aperture],error=file*file_err)
    
    bkg_mean = photometry_table['aperture_sum_1'] / annulus_aperture.area
    bkg_mean_err = photometry_table['aperture_sum_err_1'] / annulus_aperture.area
    bkg_sum = bkg_mean * aperture.area
    bkg_sum_err = bkg_mean_err * aperture.area
    
    file = float(photometry_table['aperture_sum_0'] - bkg_sum)
    file_err = float(photometry_table['aperture_sum_err_0'] - bkg_sum_err)
    
    return [file,file_err]

def count_to_inst_mag(count,count_err):
    """takes the flux in count/sec and converts it as the instrumental magnitude."""
    mag = -2.5*np.log10(count)
    mag_err = np.abs(-2.5/(np.log(10)*count_err))
    return [mag,mag_err]