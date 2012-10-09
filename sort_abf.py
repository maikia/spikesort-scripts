#!/usr/bin/env python
#coding=utf-8

import spike_sort as sort
from spike_beans import components
from spike_beans.components import GenericSource
import neo.io
import numpy as np

class ABFFilter(object):
   
    def __init__(self, fname, electrodes=None):
        self.reader = neo.io.AxonIO('sample.abf')
        self.block = self.reader.read_block()
        self.electrodes = electrodes

    def read_sp(self, dataset):
        electrodes = self.electrodes
        analogsignals = self.block.segments[0].analogsignals
        if electrodes is not None:
            analogsignals = [analogsignals[i] for i in electrodes]
        sp_raw = np.array(analogsignals)
        FS = float(analogsignals[0].sampling_rate.magnitude)
        n_contacts, _ = sp_raw.shape
        return {"data": sp_raw, "FS": FS, "n_contacts": n_contacts}
    
    def write_sp(self):
        pass

    def write_spt(self, spt_dict, dataset, overwrite=False):
        pass

class ABFSource(components.GenericSource, ABFFilter):
    def __init__(self, fname, electrodes=None, overwrite=False):
        GenericSource.__init__(self, '', overwrite)
        ABFFilter.__init__(self, fname, electrodes)

class MultiChannelSpikeDetector(components.SpikeDetector):

    def __init__(self, thresh='auto',
                 contact=None,
                 type='max',
                 resample=1,
                 sp_win=(-0.2, 0.8),
                 align=True, precision=None):
        
        components.SpikeDetector.__init__(self, thresh=thresh,
                 contact=contact, type=type, 
                 resample=resample,
                 sp_win=sp_win,
                 align=align)

        self.precision = precision


    def _spt_align(self, spt, contact):
        sp = self.waveform_src.signal
        if self.align:
            spt = sort.extract.align_spikes(sp, spt,
                                            self.sp_win,
                                            type=self.type,
                                            contact=contact,
                                            resample=self.resample)
        return spt

    def _detect(self):
        sp = self.waveform_src.signal
        n_contacts = sp['n_contacts']
        
        if self.contact is None:
            all_contacts = range(n_contacts)
        else:
            all_contacts = self.contact

        spt_list  = []
        try: 
            # detect spikes on all electrodes (aka contacts)
            for contact in all_contacts:
                spt = sort.extract.detect_spikes(sp, edge=self.type,
                                                    contact=contact,
                                                    thresh=self._thresh)
                spt = self._spt_align(spt, contact)
                spt_list.append(spt)
            
            # merge int single array (sorted) 
            spt = self.merge_spiketimes(spt_list)
            
            #precision - how close spikes can be in ms
            if self.precision is None:
                FS = sp['FS']
                precision = (1000.0/FS)
            else:
                precision = self.precision

            # remove on of overlapping spikes (if any)
            spt = sort.extract.remove_doubles(spt, precision)
       
        except TypeError:
            # if self.contact is an integer detect on a single
            # electrode
            spt = sort.extract.detect_spikes(sp, edge=self.type,
                                             contact=all_contacts,
                                             thresh=self._thresh)
            spt = self._spt_align(spt, all_contacts)


        self.sp_times = spt


    def merge_spiketimes(self, spt_list):

        spt_data = [spt['data'] for spt in spt_list]

        spt_data = np.concatenate(spt_data)
        spt_data.sort()

        spt_dict = {"data": spt_data}

        return spt_dict
    
