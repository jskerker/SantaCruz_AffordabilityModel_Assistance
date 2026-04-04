#%% import packages
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
import itertools
import time
import csv
import matplotlib.gridspec as gridspec
from statsmodels.distributions.empirical_distribution import ECDF
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")
import os
import sys
import matplotlib.patches as mpatches
import matplotlib.image as mpimg
import warnings
warnings.filterwarnings("ignore")
sys.path.append('/Users/jenniferskerker/Documents/GradSchool/Research/Equity/Model/Santa_Cruz_WRM_Assistance/scripts')
from Setup_SCWSM_Option_Analysis_CST import simSetup
print('packages imported')

#%% Import images
# import images
image_path_A = "../../outputs/Figures/Schematic/partA.png"
image_A = mpimg.imread(image_path_A) # load image

image_path_B = "../../outputs/Figures/Schematic/partB.png"
image_B = mpimg.imread(image_path_B) # load image

#%% Create figure
fig = plt.figure(figsize = (7, 11))
# define the grid layout
gs = gridspec.GridSpec(2, 1, height_ratios = [1.8, 1]) # hspace

# First column (spanning all rows): display XLRM framework
ax0 = fig.add_subplot(gs[0, 0])  # Span all rows in the first column
ax0.imshow(image_A)
ax0.axis("off")
ax0.set_title('Model Framework', fontweight='bold', fontsize=11, pad=8)

# second subplot: examples of assistance types
ax10 = fig.add_subplot(gs[1, 0])
ax10.imshow(image_B)
ax10.axis("off")
# move subplot
left, bottom, width, height = ax10.get_position().bounds
ax10.set_position([left+0.01, bottom+0.12, width, height])
ax10.set_title('Example of Assistance Types', fontweight='bold', fontsize=11)

# add labels
ax10.text(30, -753, 'a', fontsize=20, fontweight='bold')
ax10.text(30, -13, 'b', fontsize=20, fontweight='bold')

plt.savefig('../../outputs/Figures/Schematic/Figure1.png', dpi=300, bbox_inches='tight') # transparent=True
plt.show()