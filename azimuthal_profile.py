"""
Combine column densities into plots

python azimuthal_profile.py parameter_file

where parameter file is formatted as:

m12i_ref11:
snapshot_600_cdens.h5

m12i_ref11_x3:
snapshot_600_cdens.h5
snapshot_600_cdens.h5
snapshot_600_cdens.h5

REMEMBER THE TRAILING WHITESPACE LINE AT THE BOTTOM OF THIS FILE.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import yt
import numpy as np
import h5py as h5
import sys
from matplotlib.colors import LogNorm
import sys
sys.path.insert(0, '/home/andyr/src/frb')
from get_COS_data import get_COS_data, plot_COS_data
from radial_profile2 import *

def make_profiles2(a_arr, r_arr, cdens_arr, a_bins, r_bins):
  """
  Splits data into three radial groups (50 kpc, 100 kpc, 150 kpc) and bins data
  with respect to azimuthal angle to find the percentiles of each raidal group.
  """
  r_bin_ids = np.digitize(r_arr, r_bins)
  a_bin_ids = np.digitize(a_arr, a_bins)
  radii = [1, 11, 21]
  profile_data = [np.zeros([3, len(a_bins)]), np.zeros([3, len(a_bins)]), \
                  np.zeros([3, len(a_bins)])]
  for i, a_bin_id in enumerate(np.arange(len(a_bins))):
    for j in range(len(radii)):
      sample = normalize_by_radius(cdens_arr, r_bin_ids, radii[j], a_bin_ids, a_bin_id)
      profile_data[j][0,i] = np.median(sample)
      profile_data[j][1,i] = np.percentile(sample, 25)
      profile_data[j][2,i] = np.percentile(sample, 75)
  return profile_data

def normalize_by_radius(cdens_arr, r_bin_ids, r, a_bin_ids, a_bin_id):
  '''
  Takes a raidal bin of width 50kpc and splits it into 10 smaller bins of 5kpc.
  Takes the average column density of each bin and appends it to sample. Will
  return a len 10 array of the average cden of each 5kpc bin which is used to 
  give the percentiles. 
  '''
  sample = np.array([])
  r += 1
  radial_bin_id = r
  while radial_bin_id < r+10:
    ids = np.logical_and(a_bin_ids == a_bin_id, r_bin_ids == radial_bin_id)
    bin_data = cdens_arr[ids]
    sample = np.append(sample, np.sum(bin_data) / len(bin_data))
    radial_bin_id += 1
  return sample

def make_radial_bins(a_arr, r_arr, cdens_arr, a_bins, r_bins):
  '''
  Makes a profile based on radius with 3 bins of azimuthal angles: 0-30, 30-60, 
  60-90. 
  '''
  r_bin_ids = np.digitize(r_arr, r_bins)
  a_bin_ids = np.digitize(a_arr, a_bins)
  angle_bins = [0, 10, 20, 30]
  profile_data = [np.zeros([3, len(a_bins)]), np.zeros([3, len(a_bins)]), \
                  np.zeros([3, len(a_bins)])]
  for i, r_bin_id in enumerate(np.arange(len(r_bins))):
    for j in range(len(angle_bins)):
      ids = np.logical_and(r_bin_ids == r_bin_id, a_bin_ids >= angle_bins[j])
      sample = cdens_arr[np.logical_and(ids, a_bin_ids < angle_bins[j+1])]
      if len(sample) < 5:
        print('Radial bin: %s' % r_bin_id)
        print('Angle bin: %s - %s' % (angle_bins[j], angle_bins[j+1]))
      profile_data[j][0,i] = np.median(sample)
      profile_data[j][1,i] = np.percentile(sample, 25)
      profile_data[j][2,i] = np.percentile(sample, 75)
  return profile_data

def fplot_angle(r, ion):
  plt.title('%ss from %s kpc to %s kpc' % (ion, r, r+50))
  plt.xlabel('Azimuthal Angle [degrees]')
  plt.xlim((0,90))
  # plt.legend()
  print('%s_%s_%s.png' % (fn_head, ion, r+50))
  plt.savefig('plots/%s_%s_%s.png' % (fn_head, ion, r+50))
  plt.clf()

def fplot_radius(ion):
  plt.title('%ss')
  plt.xlabel('Impact Parameter [kpc]')
  plt.xlim((0,150))
  plt.legend(title='Azimuthal Angle')
  print('%s_%s_radial.png' % (fn_head, ion))
  plt.savefig('plots/%s_%s_radial.png' % (fn_head, ion))
  plt.clf()

if __name__ == '__main__':
  """
  Takes file generated by azimuthal_projections.py and creates column density
  plots.
  """

  threshold = {'H_number_density' : 10**16, 'O_p5_number_density':1e14, 'density':1e-4}

  # Get observational data from file
  COS_data = get_COS_data()

  # Color cycling
  colors = 3*['black', 'cyan', 'green', 'magenta', 'yellow', 'blue', 'red']

  fn_head = sys.argv[1].split('.')[0]
  profiles_dict = read_parameter_file(sys.argv[1])

  a_n_bins = 30
  r_n_bins = 31
  r_bins = np.linspace(150, 0, r_n_bins)
  r_bins = np.flip(r_bins, 0)
  a_bins = np.linspace(90, 0, a_n_bins, endpoint=False)
  a_bins = np.flip(a_bins, 0)

# Get the list of ion_fields from the first file available
  fn = list(profiles_dict.values())[0][0]
  f = h5.File(fn, 'r')
  ion_fields = list(f.keys())
  ion_fields.remove('radius')
  ion_fields.remove('phi')
  f.close()

  # Step through each ion
  for field in ion_fields:
    # Makes plots of azimuthal angle vs N
    for c, (k,v) in enumerate(profiles_dict.items()):
      n_files = len(v)
      cdens_arr = np.array([])
      a_arr = np.array([])
      r_arr = np.array([])
      for j in range(n_files):
        f = h5.File(v[j], 'r')
        a_arr = np.concatenate((a_arr, f['phi'].value))
        r_arr = np.concatenate((r_arr, f['radius'].value))
        cdens_arr = np.concatenate((cdens_arr, f["%s/%s" % (field, 'edge')].value))
      profile_data = make_profiles2(a_arr, r_arr, cdens_arr, a_bins, r_bins)
      for i in range(3):
        plot_profile(np.linspace(0, 90, a_n_bins), profile_data[i], k, colors[c])
        ion = finish_plot(field, COS_data, fn_head)
        fplot_angle(i*50, ion)

      # Makes radius vs N for 3 bins
      radial_data = make_radial_bins(a_arr, r_arr, cdens_arr, a_bins, r_bins)
      for i in range(3):
        plot_profile(r_bins, radial_data[i], k+str('%s\degrees-%s\degrees' % \
                    (30*i, 30*i + 30)), colors[3*i])
      ion = finish_plot(field, COS_data, fn_head)
      fplot_radius(ion)



