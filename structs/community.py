#!/usr/bin/python 
# community.py

'''
##########################################

Module name:              community


Module contains:
                          - definition of the Community class
                          - a make_commmunity() function
                          - nothing else for now, but it leaves open the possibility of adding functionality for mutliple populations (e.g. species interactions, speciation models, etc.)


Author:                    Drew Ellison Hart
Email:                     drew.hart@berkeley.edu
Github:                    URL
Start date:                07-25-18
Documentation:             URL


##########################################
'''

#geonomics imports
from structs import population


######################################
# -----------------------------------#
# CLASSES ---------------------------#
# -----------------------------------#
######################################

#NOTE: this class won't be doing too much right away, but it lays the foundation 
#for enabling interactions between populations (i.e. species) further down the road
class Community(dict):
    def __init__(self, land, pops):
        self.land = land
        self.update(pops)
        self.n_pops = len(pops)
        self.t = -1 #counter for timesteps (starts at -1, to indicate that the
                    #community is unrun, and so that the first timestep will be set to 0 at
                    #beginning of the timestep)
        #set the burned attribute (defaults to False, but will be set to True after burn-in 
        #has successfully completed, and will be used by the Model object to determine whether 
        #or not burn-in needs to happen each iteration)
        self.burned = False


    #method to increment the self.t attribute (the timestep counter)
    def set_t(self):
        self.t += 1

    #method to reset the self.t attribute (the timestep counter)
    def reset_t(self):
        self.t = -1

######################################
# -----------------------------------#
# FUNCTIONS -------------------------#
# -----------------------------------#
######################################

#function for making a community using a Land object and params
def make_community(land, params, burn=False):
    pops = {k: population.make_population(land = land, pop_params = params.comm.pops[k], burn = burn) for k in params.comm.pops.keys()}
    return Community(land, pops) 

