#!/usr/bin/python 
# community.py

'''
##########################################

Module name:              community


Module contains:
                          - definition of the Community class
                          - a make_commmunity() function
                          - nothing else for now, but it leaves open the
                            possibility of adding functionality for mutliple
                            species (e.g. species interactions, speciation
                            models, etc.)


Author:                    Drew Ellison Hart
Email:                     drew.hart@berkeley.edu
Github:                    URL
Start date:                07-25-18
Documentation:             URL


##########################################
'''

#geonomics imports
from structs import species
from sim import burnin

#other imports
import numpy as np


######################################
# -----------------------------------#
# CLASSES ---------------------------#
# -----------------------------------#
######################################

#NOTE: this class won't be doing too much right away, but lays the foundation 
#for enabling interactions between species (i.e. species) further down the road
class Community(dict):
    def __init__(self, land, spps):
        self.update(spps)
        self.n_spps = len(spps)
        self.t = -1 #counter for timesteps (starts at -1, to indicate that the
                    #community is unrun, and so that the first timestep will
                    #be set to 0 at beginning of the timestep)
        #set the burned attribute (defaults to False, but will be set to True
        #after burn-in has successfully completed, and will be used by the
        #Model object to determine whether or not burn-in needs to happen
        #each iteration)
        self.burned = False

    #define the __str__ and __repr__ special methods
    def __str__(self):
        #get the longest spp name and longest string-repr spp size, to be used
        #to horizontally rectify all the lines for each of the spps
        max_len_spp_name = max([len(spp.name) for spp in self.values()])
        max_len_spp_size = max([len(str(len(spp))) for spp in self.values()])
        #get a string representation of the class
        type_str = str(type(self))
        #get a string representation of the species
        spps_str = '%i Species:\n' % (len(self))
        spps_str = spps_str + '\n'.join(['\tspp %i: ' % k +
            "%s'%s' (%s%s inds.): " % (' ' * (max_len_spp_name - len(v.name)),
            v.name, ' ' * (max_len_spp_size - len(str(len(v)))),
            str(len(v))) +
            str(v).split('\n')[0] for k,v in self.items()])
        return '\n'.join([type_str, spps_str])

    def __repr__(self):
        repr_str = self.__str__()
        return repr_str



    #method to increment the self.t attribute (the timestep counter)
    def _set_t(self):
        self.t += 1

    #method to reset the self.t attribute (the timestep counter)
    def _reset_t(self):
        self.t = -1

    #method to check if all species have burned in
    def _check_burned(self, burn_T):
        #check minimum burn-in time has passed
        burnin_status= np.all([len(spp.Nt) >= burn_T for spp in self.values()])
        #if so, then check all burn-in tests for all spps
        if burnin_status:
            adf_tests = np.all([burnin._test_adf_threshold(spp, burn_T) for
                                spp in self.values()])
            t_tests = np.all([burnin._test_t_threshold(spp, burn_T) for
                                spp in self.values()])
            burnin_status = adf_tests and t_tests
        #set the community burn-in tracker
        self.burned = burnin_status
        #and set the spps' burn-in trackers
        [setattr(spp, 'burned', burnin_status) for spp in self.values()]


######################################
# -----------------------------------#
# FUNCTIONS -------------------------#
# -----------------------------------#
######################################

#function for making a community using a Landscape object and params
def _make_community(land, params, burn=False):
    spps = {n: species._make_species(land = land, name = name, idx = n,
        spp_params = params.comm.species[name], burn = burn) for n, name in
            enumerate(params.comm.species.keys())}
    return Community(land, spps)

