#!/usr/bin/env python -i

import matplotlib
matplotlib.use("TkAgg")
matplotlib.interactive(True)

from spike_beans import components, base
from sort_abf import ABFSource, MultiChannelSpikeDetector

#############################################
# Adjust these fields for your needs

#input data
file_name = 'sample.abf' 

#spike detection/extraction properties
contact     = None # if None - detect on all electrodes
type        = "usin"
thresh      = "4"
filter_freq = (800., 100.)
n_clusters  = 4
sp_win      = [-0.6, 0.8]
precision   = None 

#############################################
# Definition of processing stack

import numpy as np
import time
import os

io = ABFSource(file_name, electrodes=[1,2])
io_filter = components.FilterStack()
base.features.Provide("RawSource", io)
base.features.Provide("EventsOutput", io)
base.features.Provide("SignalSource", io_filter)
base.features.Provide("SpikeMarkerSource",
                      MultiChannelSpikeDetector(contact = contact, 
                                               thresh  = thresh,
                                               type    = type,
                                               sp_win  = [-0.6, 0.8],
                                               resample = 10,
                                               align  = True))
base.features.Provide("SpikeSource",   
                      components.SpikeExtractor(sp_win=sp_win))
base.features.Provide("FeatureSource", 
                      components.FeatureExtractor())
base.features.Provide("LabelSource",   
                      components.ClusterAnalyzer("gmm", n_clusters))

src      = base.features['SignalSource']
features = base.features['FeatureSource']
clusters = base.features['LabelSource']
events   = base.features['SpikeMarkerSource']
labels   = base.features['LabelSource']

browser  = components.SpikeBrowserWithLabels()
plot1    = components.PlotFeaturesTimeline()
plot2    = components.PlotSpikes()
legend   = components.Legend()
export   = components.ExportCells()

#############################################################
# Add filters here

base.features["SignalSource"].add_filter("LinearIIR", *filter_freq)

# Add the features here: 

base.features["FeatureSource"].add_feature("P2P")
base.features["FeatureSource"].add_feature("PCs", ncomps=2)

#############################################################
# Run the analysis (this can take a while)

browser.update()
browser.show()
