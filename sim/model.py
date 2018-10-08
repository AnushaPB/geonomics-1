#!/usr/bin/python
# model.py

'''
##########################################

Module name:          sim.model


Module contains:
                      - classes and functions to facilitate building a Geonomics model and
                      running multiple iterations of it, including across multiple cores


Author:               Drew Ellison Hart
Email:                drew.hart@berkeley.edu
Github:               URL
Start date:           07-06-18
Documentation:        URL


##########################################
'''

#geonomics imports
from structs import landscape, community, genome
from sim import burnin, data, stats

#other imports
import numpy as np
import numpy.random as r
import random
from copy import deepcopy
import sys, os, traceback


######################################
# -----------------------------------#
# CLASSES ---------------------------#
# -----------------------------------#
######################################

#the Model class, which will contain the main model objects, build the
#burn-in and main functions, allow customization of the objects, manage and run
#iterations, and produce and save required stats and data
class Model:
    def __init__(self, name, params, verbose=False):

        #get the full input params dict
        self.params = deepcopy(params)
        #get the model params (to make the following code shorter)
        m_params = self.params.model

        #set the model name (which will come from the params filename)
        self.name = name

        #set the __verbose__ flag
        self.__verbose__ = verbose
        #and set the private __term_width__  and __tab_len__ attributes
        self.__set_term_width__()
        self.__set_tab_len__()

        #set the seed, if required
        self.seed = None
        if 'seed' in [*m_params]:
            if m_params.seed.set:
                self.seed = m_params.seed.num
            self.set_seeds()

        #get minimum burn-in runtime (in timesteps)
        self.burn_T = m_params.time.burn_T
        #and set the burn-timestep counter (burn_t) to -1 (for same reason
        #as explained for self.t)
        self.burn_t = -1
        #get main runtime (in timesteps)
        self.T = m_params.time.T
        #and set the timestep counter (t) to -1 (to indicate that the model
        #is unrun, and so that the first timestep will default to 0 at the 
        #beginning of the timestep
        self.t = -1

        #get the number of model iterations to run
        self.n_its = m_params.its.n_its
        #set the its list
        self.its = [*range(self.n_its)][::-1]
        #and set self.it to default to -1
        self.it = -1

        #make the land and community objects
        self.land = self.make_land()
        self.comm = self.make_community()

        #and make the self.__never_run__ attribute to False,
        #to prevent the land and community from being reset
        #on the very first iteration
        self.__never_run__ = True

        #make a data.DataCollector object for the self.collecter attribute
        #if necessary
        self.data_collector = None
        if 'data' in [*m_params]:
            self.data_collector = self.make_data_collector()

        #make a stats.StatsCollector object for the self.collecter attribute
        #if necessary
        self.stats_collector = None
        if 'stats' in [*m_params]:
            self.stats_collector = self.make_stats_collector()

        #create a self.reassign_genomes attribute, which defaults to False,
        #unless any population has a genomic architecture, indicating that its
        #genomes should be reassigned after burn-in; in that case it will be 
        #reset to False as soon as the genomes are reassigned
        self.reassign_genomes = None

        #and set the orig_land and orig_comm objects, if rand_land and rand_comm are False
        self.rand_land = m_params.its.rand_land
        self.rand_comm = m_params.its.rand_comm
        self.orig_land = None
        self.orig_comm = None
        if not self.rand_land:
            self.orig_land = deepcopy(self.land)
        if not self.rand_comm:
            self.orig_comm = deepcopy(self.comm)
        #and set the self.rand_burn attribute (if this is False and
        #self.rand_comm is False, self.orig_comm will be replaced with the
        #first iteration's community as soon as it has exited burn-in and had
        #its genomes reassigned)
        self.rand_burn = m_params.its.rand_burn

        #set the function queues to None (they will be reset later if self.run 
        #is called, but if self.walk is called then the burn_fn_queue's None
        #status will be checked to determine whether or not to run self.reset()
        self.burn_fn_queue = None
        self.main_fn_queue = None

    #private method for determining the width of the terminal on the current system
    def __set_term_width__(self):
        self.__term_width__ = int(os.popen('stty size', 'r').read().split()[1])

    #private method for determining the length of a tab on the current system
    def __set_tab_len__(self):
        self.__tab_len__ = len('\t'.expandtabs())

    #method to set the iteration-counter, self.it
    def set_it(self):
        self.it = self.its.pop()

    #method to increment self.t (i.e. the main timestep counter)
    def set_t(self, reset=False):
        self.t += 1

    #method to reset self.t (i.e. the main timestep counter)
    def reset_t(self):
        self.t = -1

    #method to increment self.burn_t (i.e. the burn-in timestep counter)
    def set_burn_t(self, reset=False):
        self.burn_t += 1

    #method to reset self.burn_t (i.e. the burn-in timestep counter)
    def reset_burn_t(self):
        self.burn_t = -1

    #method to set the self.reassign_genomes attribute 
    def set_reassign_genomes(self):
        self.reassign_genomes = np.any([pop.gen_arch is not None for pop in self.comm.values()])

    #method to set seed (will be run when Model object is first created, if
    #called for in params)
    def set_seeds(self):
        random.seed(self.seed)
        r.seed(self.seed)

    #method to wrap around landscape.make_land
    def make_land(self):
        land = landscape.make_land(self.params)
        return(land)

    #a method to reset the land as necessary (recopying or regeneratiing as necessary)
    def reset_land(self, rand_land=True):
        #deepcopy the original land if necessary (else randomly generate new land)
        if not rand_land:
            #__verbose__ output
            if self.__verbose__:
                print('Copying the original land for iteration %i...\n\n' % self.it)
            #deepcopy the original land
            self.land = deepcopy(self.orig_land)
            #and reset the land.changer.changes, if needed (so that they
            #point to the current land, not previous objects with possibly
            #updated attribute values)
            if self.land.changer is not None:
                #verbose output
                if self.__verbose__:
                    print('Resetting the land.changer.changes object...\n\n')
                self.land.changer.set_changes(self.land)
        else:
            #verbose output
            if self.__verbose__:
                print('Creating new land for iteration %i...\n\n' % self.it)
            self.land = self.make_land()


    #method to wrap around community.make_community
    def make_community(self):
        comm = community.make_community(self.land, self.params, burn = True)
        return(comm)


    #a method to reset the community (recopying or regenerating as necessary)
    def reset_community(self, rand_comm=True):
        if not rand_comm:
            #verbose output
            if self.__verbose__:
                print('Copying the original community for iteration %i...\n\n' % self.it)
            self.comm = deepcopy(self.orig_comm)
            #and reset the pop.changer.changes objects for each pop, if needed (so that they
            #point to the current populations, not previous ones with
            #updated attribute values)
            for pop in self.comm.values():
                if pop.changer is not None:
                    #verbose output
                    if self.__verbose__:
                        print('Resetting the pop.changer.changes object for population " %s"...\n\n' % pop.name)
                    pop.changer.set_changes(pop)
        else:
            #verbose ouput
            if self.__verbose__:
                print('Creating new community for iteration %i...\n\n' % self.it)
            self.comm = self.make_community()


    #method to make a data.DataCollector object for this model
    def make_data_collector(self):
        data_collector = data.DataCollector(self.name, self.params)
        return data_collector


    #method to reset the self.data_collector attribute 
    #(a data.DataCollector object)
    def reset_data_collector(self):
        self.data_collector = self.make_data_collector()


    #method to use the self.data_collector object to sample and write data
    def write_data(self):
        self.data_collector.write_data(self.comm, self.it)


    #method to make a stats.StatsCollector object for this model
    def make_stats_collector(self):
        stats_collector = stats.StatsCollector(self.name, self.params)
        return stats_collector


    #method to reset the self.stats_collector attribute 
    #(a stats.StatsCollector object)
    def reset_stats_collector(self):
        self.stats_collector = self.make_stats_collector()


    #method to use the self.stats_collector object to sample and write data
    def calc_stats(self):
        self.stats_collector.calc_stats(self.comm, self.t, self.it)


    #method to reset all the model's objects (land, community, and associated) and attributes
    def reset(self, rand_land=None, rand_comm=None, rand_burn=None):
        #default to the self.rand_<_> attributes, if not otherwise provided
        if rand_land is None:
            rand_land = self.rand_land
        if rand_comm is None:
            rand_comm = self.rand_comm
        if rand_burn is None:
            rand_burn = self.rand_burn

        #deepcopy the original land and comm if necessary (if told not to randomize
        #land and not at the beginning of the initial iteration), else randomly generate new
        if not self.__never_run__:
            self.reset_land(rand_land)
            self.reset_community(rand_comm)
        else:
            self.__never_run__ = False

        #reset the self.burn_t and self.t attributes to -1
        self.reset_t()
        if rand_burn:
            self.reset_burn_t()

        #reset the community and population t attributes
        self.comm.reset_t()
        for pop in self.comm.values():
            pop.reset_t()

        #set the self.reassign_genomes attribute
        self.set_reassign_genomes()

        #reset the self.data_collector attribute (the data.DataCollector
        #object) if necessary
        if self.data_collector is not None:
            self.reset_data_collector()

        #reset the self.stats_collector attribute (the stats.StatsCollector
        #object) if necessary
        if self.stats_collector is not None:
            self.reset_stats_collector()

        #create new main fn queue (and burn fn queue, if needed)
        if rand_burn or self.it <= 0:
            #verbose output
            if self.__verbose__:
                print('Creating the burn-in function queue...\n\n')
            self.burn_fn_queue = self.make_fn_queue(burn = True)
        #verbose output
        if self.__verbose__:
            print('Creating the main function queue...\n\n')
        self.main_fn_queue = self.make_fn_queue(burn = False)


    #method to create the simulation functionality, as a function queue 
    #NOTE: (creates the list of functions that will be run by
    #self.run_burn_timestep or self.run_main_timestep, depending on burn argument)
    #NOTE: because the queue is a list of functions, the user could add, remove, 
    #change the order, or repeat functions within the list as desired
    def make_fn_queue(self, burn=False):
        queue = []

        #append the methods to increment the timestep attributes (i.e. the timestep counters)
        if burn:
            queue.append(self.set_burn_t)
        if not burn:
            queue.append(self.set_t)
            queue.append(self.comm.set_t)
            for pop in self.comm.values():
                queue.append(pop.set_t)

        #append the set_age_stage methods to the queue
        for pop in self.comm.values():
            queue.append(pop.set_age_stage)
        #append the set_Nt methods
        for pop in self.comm.values():
            queue.append(pop.set_Nt)
        #append the do_movement_methods, if pop.move
        for pop in self.comm.values():
            if pop.move:
                queue.append(pop.do_movement)
        #append the do_pop_dynamics methods
        #FIXME: Consider whether the order of these needs to be specified, or
        #randomized, should people want to eventually simulate multiple, interacting populations
        for pop in self.comm.values():
            queue.append(pop.do_pop_dynamics)

        #add the Changer.make_change, data.DataCollector.write_data, and 
        #stats.StatsCollector.write_stats methods, if this is not the burn-in
        #and if pop and/or land have Changer objects, or if the model has 
        #DataCollector or StatsCollector objects (in the self.data_collector 
        #and self.stats_collector attributes)
        if not burn:
            #add land.make_change method
            if self.land.changer is not None:
                queue.append(lambda: self.land.make_change(self.t))
            #add pop.make_change methods
            for pop in self.comm.values():
                if pop.changer is not None:
                    queue.append(pop.make_change)
            #add self.write_data method
            if self.data_collector is not None:
                queue.append(self.write_data)
            #add self.calc_stats method
            if self.stats_collector is not None:
                queue.append(self.calc_stats)

            #TODO depending how I integrate the Stats module, 
            #add stats functions to this queue too



        #add the burn-in function if need be
        if burn:
            #for pop in self.comm.values():
                #queue.append(lambda: pop.check_burned(self.burn_T))
            queue.append(lambda: self.comm.check_burned(burn_T = self.burn_T))
        return(queue)


    #method to generate timestep_verbose_output
    def print_timestep_info(self, mode):
        verbose_msg = '%s:\t%i:%i\n' % (mode, self.it, [self.burn_t if mode == 'burn' else self.t][0])
        pops_submsgs = ''.join(['\tPOP: %s%sN=%i\t(births=%i\tdeaths=%i)\n' %
                                    (pop.name,
                                     ' ' * (30 - len(pop.name)),
                                     pop.Nt[:].pop(),
                                     pop.n_births[:].pop(),
                                     pop.n_deaths[:].pop()) for pop in self.comm.values()])
        verbose_msg = verbose_msg + pops_submsgs
        print(verbose_msg)
        print('\t' + '.' * (self.__term_width__ - self.__tab_len__))


    #method to run the burn-in or main function queue (as indicated by mode argument)
    def do_timestep(self, mode):
        #do a burn-in step
        if mode == 'burn':
            for fn in self.burn_fn_queue:
                if True not in [pop.extinct for pop in self.comm.values()]:
                    fn()
                    if self.__verbose__:
                        self.print_timestep_info(mode)
                    #if the burn-in is complete, reassign the genomes if needed
                    #and then set self.comm.burned = True
                    if np.all([pop.burned for pop in self.comm.values()]):
                        if self.reassign_genomes:
                            for pop in self.comm.values():
                                if pop.gen_arch is not None:
                                    #verbose output
                                    if self.__verbose__:
                                        print('Assigning genomes for population "%s"...\n\n' % pop.name)
                                    genome.set_genomes(pop, self.burn_T, self.T)
                            #and then set the reassign_genomes attribute to False, so
                            #that they won'r get reassigned again during this iteration
                            self.reassign_genomes = False
                        #mark the community as burned in
                        self.comm.burned = True
                        #verbose output
                        if self.__verbose__:
                            print('Burn-in complete.\n\n')
                else:
                    break
        #or do a main step
        elif mode == 'main':
            for fn in self.main_fn_queue:
                if  True not in [pop.extinct for pop in self.comm.values()]:
                    fn()
                    if self.__verbose__:
                        self.print_timestep_info(mode)
                else:
                    break

        #then check if any populations are extinct and return the correpsonding boolean
        extinct = np.any([pop.extinct for pop in self.comm.values()])
        #verbose output
        if extinct and self.__verbose__:
            print('XXXX     Population %s went extinct. Iteration %i aborting.\n\n' % (' & '.join(['"' + pop.name + '"' for pop in self.comm.values() if pop.extinct]), self.it))
        return(extinct)


    #method to set the model's next iteration
    def set_next_iteration(self, core=None):
        #update the iteration numbers
        self.set_it()
        #verbose output
        if self.__verbose__:
            print('~' * self.__term_width__ + '\n\n')
            print('Setting up iteration %i...\n\n' % self.it)

        #reset the model (including the burn-in, if self.rand_burn or if this is the first iteration) 
        self.reset(rand_land = self.rand_land,
                         rand_comm = self.rand_comm,
                         rand_burn = self.rand_burn)


    #method for running the model's next iteration
    def do_next_iteration(self):

        #set the next iteration to be run
        self.set_next_iteration()

        #loop over the burn-in timesteps running the burn-in queue (if copied pop isn't already burned in)
        if self.rand_comm or (not self.rand_comm and self.rand_burn) or self.it == 0:
            #verbose output
            if self.__verbose__:
                print('Running burn-in, iteration %i...\n\n' % self.it)
            #until all populations have pop.burned == True
            while not np.all([pop.burned for pop in self.comm.values()]):
                #run a burn-in timestep
                extinct = self.do_timestep(mode = 'burn')
                #and end the iteration early if any population is extinct
                if extinct:
                    break

            #overwrite self.orig_comm with the burned-in community, if necessary
            if not self.rand_comm and not self.rand_burn:
                #verbose output
                if self.__verbose__:
                    print('Saving burned-in community...\n\n')
                self.orig_comm = deepcopy(self.comm)

        #verbose output
        if self.__verbose__:
            print('Running main model, iteration %i...\n\n' % self.it)
        #loop over the timesteps, running the run_main function repeatedly
        for t in range(self.T):
            #run a main timestep
            extinct = self.do_timestep('main')
            #and end the iteration early if any population is extinct 
            if extinct:
                break


    #method to run the overall model
    def run(self, verbose=False):

        #TODO: Add some handler for farming instances out to different nodes, if available?

        #set the self.__verbose__ flag
        self.__verbose__ = verbose

        #verbose output
        if self.__verbose__:
            print('\n\n' + '#' * self.__term_width__ + '\n\n')
            print('Running model "%s"...\n\n' % self.name)

        #loop over all the iterations
        while len(self.its) > 0:
            #do the next iteration
            try:
                self.do_next_iteration()
            except Exception as e:
                msg = ('XXXX\tAn error occurred during iteration %i, '
                    'timestep %i.\n \tPLEASE COPY AND REPORT THE FOLLOWING, '
                    'to help us debug Geonomics:\n')
                if self.comm.burned:
                    msg = msg % (self.it, self.t)
                else:
                    msg = msg % (self.it, self.burn_t)
                print(msg)
                print('<>' * int(self.__term_width__/2))
                print('Error message:\n\t%s\n\n' % e)
                traceback.print_exc(file=sys.stdout)
                print()
                print('<>' * int(self.__term_width__/2) + '\n\n')

        #verbose output
        if self.__verbose__:
            print('\n\nModel "%s" is complete.\n' % self.name)
            print('#' * self.__term_width__)

        #set the __verbose__ flag back to False
        self.__verbose__ = False


    #method to run the model interactively from the command line; named 'walk'
    #to succinctly differentiate it from 'run'
    def walk(self, T=1, mode='main', verbose=True):
        '''Run the model, with its current parameterization, interactively from
        the command line. The number of timesteps provided (T) will be treated
        as burn_T (i.e. the minimum number of burn-in timesteps) if
        mode='burn'.
        '''

        #throw an error and quit if mode == 'main' but the community is 
        #not burned in
        if mode == 'main' and not self.comm.burned:
            raise ValueError(("The Model.walk method cannot be run in 'main' "
                "mode if the Model's Community has not yet been burned in "
                "(i.e. if Model.comm.burned is False)."))

        #set the model's __verbose__ flag
        self.__verbose__ = verbose

        #if verbose, add a space below the command line prompt, for readability
        if self.__verbose__:
            print('\n')

        #run the model for the stipulated number of timesteps
        for t in range(T):
            #exit if burn-in is complete
            if mode == 'burn' and self.comm.burned:
                #verbose output
                if self.__verbose__:
                    print('Burn-in complete.\n\n')
                break
            #reset the mode, if mode is 'burn' and there is no mod.burn_fn_queue
            if mode == 'burn' and self.burn_fn_queue is None:
                #verbose output
                if self.__verbose__:
                    print(('No mod.burn_fn_queue was found. '
                          'Running mod.reset()...\n\n'))
                self.reset()
            extinct = self.do_timestep(mode = mode)
            #end the iteration early if any population is extinct
            if extinct:
                break
        #reset self.__verbose__ to False
        self.__verbose__ = False


