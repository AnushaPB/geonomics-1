#!/usr/bin/python
# change.py

'''
##########################################

Module name:          sims.change


Module contains:
                      - classes and functions to facilitate environmental, demographic, and parameter change


Author:               Drew Ellison Hart
Email:                drew.hart@berkeley.edu
Github:               URL
Start date:           07-06-18
Documentation:        URL


##########################################
'''
#geonomics imports
from utils import spatial as spt

#other imports
import numpy as np
import numpy.random as r
from operator import attrgetter as ag
from collections import OrderedDict as OD
import itertools as it
import copy


#TODO:

    #1 I created a quick, crude way of stipulating other-parameter pop changes, but it would probably be nicer
        #to just further generalize the dem-change functions to allow for linear, stochastic, cyclic, or custom
        #changes of other param values?

    #2 do I need to create a Gen_Changer?

    #3 then write the overall Sim_Changer class to unite everything? or should the Changers actually be
        #created and made to inhere as attributes of the Landscape_Stack and Population classes instead?

        #4 as soon as I revamp the movement_surf so that it's a pop attribute rather than a land attribute then
        #this will likewise need to be revamped! (because right now movement_surf changes are lumped with landscape changes)

    #5 I think this can be standardized (e.g. Land_Changer get_<   >_change_fns functions I believe return just the
    #functions, whereas Pop_Changer ones return list(zip(t, change_fn)) objects) and generalized still
    #further. Worth doing now, while the code is fresh in my head...


######################################
# -----------------------------------#
# CLASSES ---------------------------#
# -----------------------------------#
######################################

#base class for Land_, Pop_, and Gen_Changer classes
class Changer:
    def __init__(self):
        #set the type-label of the changer
        self.type = None

        #create self.changes, which defaults to None but will be set to an iterator over all changes
        #that are to happen to the changing object during the model (where changes in the iterator are tuples 
        #of (timestep, change_function))
        self.changes = None
        #create self.next_change, which defaults to None but will be set by self.set_changes and upkept by self.make_change
        self.next_change = None

        #set self.changes and self.next_change
        #self.set_changes(land, params)
       
    def set_next_change(self):
        try:
            self.next_change = next(self.changes)
        except StopIteration:
            self.next_change = None

    def make_change(self, t):
        #if this is the right timestep for the next change
        if self.next_change is not None:
            if t == self.next_change[0]:
                print("\n\nRUNNING THE NEXT CHANGE:\n\t%s" % str(self.next_change))
                #call the next_change function to make the change
                self.next_change[1](self) 
                    #NOTE: feeding self in so that some change functions that need to set Changer 
                    #attributes (e.g. pop-changer dem functions set the #base_K raster at the 
                    #beginning of a period of dem changes) have access to the Changer object
                #then load the next change after that
                self.set_next_change()
                #then recurse this function, so that multiple changes will happen this timestep if need be
                self.make_change(t)

    #add a change (in the form of a (timestep, change_fn) pair) at the appropriate timestep
    def add_change(self, change):
        changes = [self.next_change]
        more = True
        while more:
            try:
                changes.append(next(self.changes))
            except StopIteration:
                more = False
        before = [c[0] <= change[0] for c in self.changes]
        insert = before.index(False)
        changes = changes[:insert] + [change] + changes[insert:]
        self.next_change = changes[0]
        self.changes = iter(changes)


class Land_Changer(Changer):
    def __init__(self, land, params):
        super(Land_Changer, self).__init__()
        #set the type-label of the changer
        self.type = 'land'

    #call self.set_changes() to set self.changes and self.next_change
        self.set_changes(land, params)

    #method to set the changes stipulated in params dict for the land object
    def set_changes(self, land, params):
        #pull out the separate parts of the params file
        land_change_params = params['change']['land']

        #get the linearly spaced time-series of scapes for each scape_num
        scapes = {}
        surfs = {}
        for scape_num in land_change_params.keys():
            scape_series, dim, res, ulc = make_linear_scape_series(land.scapes[scape_num].rast, **land_change_params[scape_num])
            assert dim == land.dim, 'ERROR: dimensionality of scape_series fed into Land_Changer does not match that of the land to be changed.'
            assert res == land.res or res is None, 'ERROR: resolution of scape_series fed into Land_Changer does not match that of the land to be changed.'
            assert ulc == land.ulc or ulc is None, 'ERROR: upper-left corner of scape_series fed into Land_Changer does not match that of the land to be changed.'
            scapes[scape_num] = scape_series
            if scape_num == land.move_surf_scape_num:
                surf_series = make_movement_surface_series(land, scape_series)
                surfs[scape_num] = surf_series
        
        #check that timesteps are the same for the surf_series and scape_series items pertaining to the
        #movement-surface scape
        if land.move_surf_scape_num in scapes.keys():
            assert [i[0] for i in scapes[land.move_surf_scape_num]] == [i[0] for i in surfs[land.move_surf_scape_num]], 'ERROR: scape_series and surf_series do not contain the same timesteps for the movement surface scape'
        
        #get everything in chronological order (with scape-change functions coming before surf-change
        #functions if they're in the same timestep)
        scape_changes = []
        for scape_num in scapes.keys():
            scape_changes.extend([(t, scape_num, scape) for t,scape in scapes[scape_num]])
            #if scape_num == land.move_surf_scape_num:
                #all_changes.extend([(t, scape_num, surf) for t,surf in surfs[scape_num]])
        scape_changes = sorted(scape_changes, key = lambda x: x[0])
        all_changes = []
        for change in scape_changes:
            all_changes.append(change)
            if change[1] == land.move_surf_scape_num:
                corresp_surf_change = [(t, change[1], surf) for t, surf in surfs[change[1]] if list(surfs.keys())[0] == change[1] and t == change[0]]
                assert len(corresp_surf_change) == 1, "ERROR: Found more than one surface-change function corresponding to a given scape-change function (i.e. for a given timestep and scape_num combo)"
                all_changes.append(corresp_surf_change[0])

        #make a list of change_fns for the changes in all_changes, and make self.changes an iterator over that list
        change_fns = [(change[0], get_land_change_fn(land, *change[1:])) for change in all_changes]
        change_fns = iter(change_fns)
        self.changes = change_fns
        #load the first change to happen into the self.next_change attribute
        self.set_next_change()


class Pop_Changer(Changer):
    def __init__(self, pop, params):
        self.type = 'pop'
        
        #an attribute that is used by some dem-change fns, as a baseline population size at the start of the
        #demographic change event against which later timesteps' changes are defined
        self.base_K = None

    #call self.set_changes() to set self.changes and self.next_change
        self.set_changes(pop, params)

    #method to set the base_K attribute to pop.K
    def set_base_K(self, pop):
        self.base_K = pop.K

    #method to set the changes stipulated in params dict for the pop object
    def set_changes(self, pop, params):
        #pull out the relevant part of the params file
        pop_change_params = params['change']['pops']
        dem_change_params = pop_change_params['dem']
        other_change_params = pop_change_params['other']

        #set the demographic changes, if applicable
        dem_change_fns = []
        if pop.name in dem_change_params.keys():
            if True in [v is not None for v in dem_change_params[pop.name].values()]:
                for event_key, event_params in dem_change_params[pop.name].items():
                    dem_change_fns.extend(get_dem_change_fns(pop, **event_params))

        #set the other changes, if applicable
        other_change_fns = []
        if pop.name in other_change_params.keys():
            for param in other_change_params[pop.name].keys():
                if True in [v is not None for v in other_change_params[pop.name][param].values()]:
                    other_change_fns.extend(get_other_change_fns(pop, param, **other_change_params[pop.name][param]))

        #put all the changes in chronological order
        if len(dem_change_fns) + len(other_change_fns) > 0:
            change_fns = dem_change_fns + other_change_fns
            change_fns = sorted(change_fns, key = lambda x: x[0])

            #make self.changes an iterator over that list
            change_fns = iter(change_fns)
            self.changes = change_fns
            #load the first change to happen into the self.next_change attribute
            self.set_next_change()

    #a method to visualize the population changes that will occur
    def show_dem_changes(self, pop):
        from copy import deepcopy
        import matplotlib.pyplot as plt
        cop_pop = deepcopy(pop)
        cop_self = deepcopy(self)
        cop_changes = deepcopy(cop_self.changes)
        step_list = [cop_self.next_change[0]]
        more = True
        while more:
            try:
                next_change = next(cop_changes)
                step_list.append(next_change[0])
            except StopIteration:
                more = False
        end = int(1.1*max(step_list))
        #set pop.K to 1, for viz purposes
        pop.K = 1
        #and set cop_self.base_K 
        cop_self.set_base_K(pop)
        Ks = []
        for t in range(end):
            cop_self.make_change(t)
            Ks.append(pop.K)
        plt.plot(range(end), Ks)
        #set pop back to its original value
        pop = cop_pop
            

class Gen_Changer:
    def __init__(self, change_vals, params):
        self.type = 'gen'


#an overall Sim_Changer class, which will contain and operate the Land_, Pop_, and Gen_Changer objects
#and will make each timestep's necessary changes in that order (land-level changes, then population, then genome)
class Sim_Changer:
    def __init__(self, changers, params):
        type_getter = ag('type')
        valid_changer_types = ['land', 'pop', 'gen']
        types = list(map(type_getter, changers))
        for t in types:
            setattr(self, t, [changer for changer in changers if changer.type == t])
        for t in set(valid_changer_types) - set(types):
            setattr(self, t, None)


######################################
# -----------------------------------#
# FUNCTIONS -------------------------#
# -----------------------------------#
######################################

    ####################
    # for Land_Changer #
    ####################
    
#function that takes a starting scape, an ending scape, a number of timesteps, and a Model object,
#and returns a linearly interpolated stack of scapes
def make_linear_scape_series(start_scape, end_scape, t_start, t_end, n):
    if type(end_scape) is str:
        end_scape, dim, ulc, res = io.read_raster(end_scape)

    elif type(end_scape) is np.ndarray:
        dim = end_scape.shape
        ulc = None
        res = None
        
    #get (rounded) evenly spaced timesteps at which to implement the changes
    timesteps = np.int64(np.round(np.linspace(t_start, t_end, n)))
    #flatten the starting and ending scapes
    start = start_scape.flatten()
    end = end_scape.flatten()
    #get a column of values for each grid cell on the landscape, linearly spaced between that cell's start and end values
    #NOTE: linspace(..., ..., n+1)[1:] gives us the changed scapes for n steps, leaving off the starting scape
    #value because that's already the existing scape so we don't want that added into our changes
    scape_series = np.vstack([np.linspace(start[i], end[i], n+1)[1:] for i in range(len(start))])
    #then reshape each timeslice into the dimensions of start_scape
    scape_series = [scape_series[:,i].reshape(start_scape.shape) for i in range(scape_series.shape[1])]
    #check that all the lenghts match up
    assert len(scape_series) == n, "ERROR: len(scape_series) != n"
    assert len(scape_series) == len(timesteps), "ERROR: the number of changing scapes created is not the same as the number of timesteps to be assigned to them"
    #zip the timesteps and the scapes together and return them as a list
    scape_series = list(zip(timesteps, scape_series))
    return(scape_series, dim, res, ulc)


#function that takes a Landscape_Stack, a scape_num and a dictionary of {t_change:new_scape} 
#and creates an Env_Changer object that will change out Landscape_Stack.scapes[scape_num] for new_scape at
#each requisite t_change timestep
def make_custom_scape_series(scape_dict):
    pass


def make_movement_surface_series(land, scape_series, kappa=12):
    #create a deepcopy of the Landscape_Stack, to change the scape out for and then use to make movement surfaces
    copy_land = copy.deepcopy(land)
    surf_series = []
    for t, scape in scape_series:
        #change the appropriate scape in the Landscape_Stack
        copy_land.set_raster(copy_land.move_surf_scape_num, scape)
        #then create a Movement_Surface using the copied Landscape_Stack
        surf_series.append((t, spt.Movement_Surface(copy_land, kappa = kappa)))
    return(surf_series)


def change_movement_surface(land, new_move_surf):
    assert type(new_move_surf) == spt.Movement_Surface, "ERROR: new_move_surf does not appear to be of type utils.spatial.Movement_Surface"
    land.move_surf = new_move_surf


def get_scape_change_fn(land, scape_num, new_scape):
    def fn(lc, land = land, scape_num = scape_num, new_scape = new_scape):
        land.set_raster(scape_num, new_scape)
    return(fn)


def get_surf_change_fn(land, scape_num, new_surf):
    def fn(lc, land = land, scape_num = scape_num, new_surf = new_surf):
        change_movement_surface(land = land, new_move_surf = new_surf)
    return(fn)


def get_land_change_fn(land, scape_num, item):
    type_fns = {np.ndarray              : get_scape_change_fn, 
                spt.Movement_Surface    : get_surf_change_fn
                }
    change_fn = type_fns[type(item)](land, scape_num, item)
    return(change_fn)


    ###################
    # for Pop_Changer #
    ###################


        ###############
        # demographic #
        ###############

                                                           
def get_dem_change_fns(pop, kind, start=None, end=None, rate=None, interval=None, size_target=None, n_cycles=None, size_range=None, dist='uniform', min_size=None, max_size=None, timesteps=None, sizes=None, increase_first=True):
    if kind == 'monotonic':
        fns = get_monotonic_dem_change_fns(pop = pop, rate = rate, start = start, end = end, size_target = size_target)
    elif kind == 'stochastic':
        fns = get_stochastic_dem_change_fns(pop = pop, start = start, end = end, interval = interval, size_range = size_range, dist = dist)
    elif kind == 'cyclical':
        fns = get_cyclical_dem_change_fns(pop = pop, start = start, end = end, n_cycles = n_cycles, size_range = size_range, min_size = min_size, max_size = max_size, increase_first = increase_first)
    elif kind == 'custom':
        fns = get_custom_dem_change_fns(pop = pop, timesteps = timesteps, sizes = sizes)
    return(fns)
        

def make_dem_change_fns(pop, sizes, timesteps, K_mode='base'):
    fns = []
    if K_mode == 'current':
        for size in sizes:
            def fn(pc, pop = pop, size = size):
                pop.K*=size
            fns.append(fn)
    elif K_mode == 'base':
        t0 = timesteps[0]
        for size in sizes:
            def fn(pc, pop=pop, size=size, t0 = t0):
                if pop.t == t0:
                    pc.set_base_K(pop)
                pop.K = pc.base_K*size
            fns.append(fn)
    change_fns = list(zip(timesteps, fns))
    return(change_fns)


#NOTE: I haven't implemented the size_target argument yet!

#will generate exponential change in the population by iteratively multiplying a carrying-capacity (K) raster
def get_monotonic_dem_change_fns(pop, rate, start, end, size_target=None):
    #get the timesteps for the demogprahic changes (subtract 1 from start to set Python's 0th timestep as 1)
    #NOTE: setting start and end to the same value will create a single-timestep change (e.g. a sudden bottleneck or rapid expansion)
    timesteps = range(start, end) 
    sizes = [rate]*len(timesteps)
    change_fns = make_dem_change_fns(pop, sizes, timesteps, K_mode='current')
    return(change_fns)


#NOTE: should I provide an option for linear monotonic change (because I can set pc.base_K and then multiply it by rate *t at each t of a period of change)?


#will create stochastic changes around a baseline carrying-capacity (K) raster
def get_stochastic_dem_change_fns(pop, size_range, start, end, interval, dist = 'uniform'):
    start_K = pop.K
    if interval is None:
        interval = 1
    timesteps = range(start, end, interval)
    if dist == 'uniform':
        sizes = r.uniform(*size_range, len(timesteps))
    elif dist == 'normal':
        mean = np.mean(size_range)
        sd = (size_range[1] - size_range[0])/6
        sizes = r.normal(loc = mean, scale = sd, size = len(timesteps))
    else:
        raise ValueError("ERROR: dist must be a value among ['uniform', 'normal']")
    #make size return to starting size
    sizes[-1] = 1
    #make all the change functions
    change_fns = make_dem_change_fns(pop, sizes, timesteps, K_mode = 'base')
    return(change_fns)


def get_cyclical_dem_change_fns(pop, start, end, n_cycles, size_range=None, min_size=None, max_size=None, increase_first=True):
    #detemine the min and max sizes for the cycles, based on input arguments
    if size_range is not None and min_size is None and max_size is None:
        min_size, max_size = size_range
    elif size_range is None and min_size is not None and max_size is not None:
        pass
    #and throw an informative error if both size_range and min_size&max_size arguments are provided (or neither)
    else:
        raise ValueError('ERROR: Must either provide size_range (as a tuple of minimum and maximum sizes), or provide min_size and max_size separately, but not both.')
    #check that there are enough timesteps to complete the cycles
    assert n_cycles <= (end - start)/2, 'ERROR: The number of cycles requested must be no more than half the number of time steps over which the cycling should take place.'
    #create a base cycle (one sine cycle)
    base = np.sin(np.linspace(0, 2*np.pi,1000)) 
    #flip it if cycles should decrease before increasing
    if not increase_first:
        base = base[::-1]
    #scale the base cycle to the min_size
    scaled_base = [1 + n*(max_size-1) if n>=0 else n for n in base]
    #and scale it to the max_size
    scaled_base = [1 + n*(1-min_size) if n<0 else n for n in scaled_base]
    scaled_base = np.array(scaled_base)
    #then get the timesteps at which each cycle should complete
    cycle_timesteps = np.int32(np.linspace(start, end, n_cycles+1))
    #get from that the length in timesteps of each cycle
    cycle_lengths = np.diff(cycle_timesteps)
    #get from that the pop sizes at each timestep (which will approximate the scaled sine curve from scaled_base
    sizes = np.hstack([scaled_base[np.int32(np.linspace(1, len(scaled_base)-1, l))] for l in cycle_lengths] + [1])
    #then get all timesteps across the cycles, to match up to the pop sizes
    timesteps = range(cycle_timesteps[0], cycle_timesteps[-1]+1) 
    #get all the change functions for those timesteps
    change_fns = make_dem_change_fns(pop, sizes, timesteps, K_mode = 'base')
    return(change_fns)


def get_custom_dem_change_fns(pop, timesteps, sizes):
    assert len(timesteps) == len(sizes), 'ERROR: For custom demographic changes, timesteps and sizes must be iterables of equal length.'
    change_fns = make_dem_change_fns(pop, sizes, timesteps, K_mode = 'base')
    return(change_fns)


        ##############
        #   params   #
        ##############

def make_other_change_fns(pop, param, timesteps, values):
    fns = []
    for value in values:
        def fn(pc, param, pop = pop, value = value):
            setattr(pop, param, value)
        fns.append(fn)
    change_fns = list(zip(timesteps, fns))
    return(change_fns)


def get_other_change_fns(pop, param, timesteps, values):
    assert len(timesteps) == len(values), "ERROR: For custom changes of the '%s' paramter, timesteps and values must be iterables of equal length." % param
    change_fns = make_other_change_fns(pop, param, timesteps, values)
    return(change_fns)


    


    ###################
    # for Gen_Changer #
    ###################


    ###################
    # for Sim_Changer #
    ###################


    ###################
    #     Others      #
    ###################
    

