#GEONOMICS_params_01-10-2018_22:25:05.py

#This is a default parameters file generated by Geonomics 
#(by the gnx.params.make_parameters_file() function).


                      # :: ::    :::            #      
                #:::   :::::    :::   ::    :: :: :::# 
             # ::::     ::           ::   ::::::::::::::#
           #::::::                       ::::::::: :::::: :#
         # :    :::                    :::    ::    :::::::::#
        #ggggg eeee ooo   n   n   ooo   m   m iiiii  cccc ssss#
       #g     e    o   o  nn  n  o   o  m   m   i   c     s    # 
       #g     eee o     o n n n o     o mm mm   i   c     sssss#
       #g ggg eee o     o n  nn o     o m m m   i   c         s#
       #g   g e    o   o  n   n  o   o  m   m   i   c        ss#
        #gggg  eeee ooo   n   n   ooo   m   m iiiii  cccc ssss#
         #  ::::::::        ::::::::::::  :       ::  ::   : #
           #  ::::              :::::::  ::     ::::::::  :#
             # :::               :::::: ::       ::::::  #
                #:                ::::                # 
                      #                         #      


params = {

##############
#### LAND ####
##############
    'land': {

    ##############
    #### main ####
    ##############
        'main': {
            'dim':                      (20,20),
                #x- and y-dimensionality of landscape
            'res':                      (1,1),
                #landscape resolution in x and y dimensions (for crosswalking with real-world
                #distances; defaults to meaningless (1,1), will be reset if GIS rasters are read in
            'ulc':                      (0,0),
                #upper-left corner of the landscape; defaults to meaningless (0,0), can be set
                #to alternative values for crosswalking with real-world data, and will be
                #reset if GIS rasters are read in
            'prj':                      None,
                #projection of the landscape; only applicable if layers are to
                #be read in from a raster file; defaults to None
            }, # <END> 'main'

    ################
    #### scapes ####
    ################
        'scapes': {

            0: {
                #scape name; each scape must be give a unique string or numeric 
                #(e.g. 0, 0.1, 'scape0', '1994', 'mean_T'); default to serial
                #integers from 0

        ############################
        #### scape num. 0: init ####
        ############################

                'init': {
                    #initiating parameters for this scape

                    'rand': {
                        #parameters for making a random scape (interpolated 
                        #from randomly located random values)
                        'n_pts':                        500,
                            #number of random coordinates to be used in generating random landscapes
                                #(only needed if rand == True)
                        'interp_method':                'cubic'
                            # interpolation method (valid: 'linear', 'cubic', 'nearest')
                        },

                    } # <END> 'init'

                }, # <END> scape num. 0


            1: {
                #scape name; each scape must be give a unique string or numeric 
                #(e.g. 0, 0.1, 'scape0', '1994', 'mean_T'); default to serial
                #integers from 0

        ############################
        #### scape num. 1: init ####
        ############################

                'init': {
                    #initiating parameters for this scape

                    'rand': {
                        #parameters for making a random scape (interpolated 
                        #from randomly located random values)
                        'n_pts':                        500,
                            #number of random coordinates to be used in generating random landscapes
                                #(only needed if rand == True)
                        'interp_method':                'cubic'
                            # interpolation method (valid: 'linear', 'cubic', 'nearest')
                        },

                    } # <END> 'init'

                }, # <END> scape num. 1



    #### NOTE: Individual Scapes' sections can be copy-and-pasted (and
    #### assigned distinct keys and names), to create additional Scapes.


            } # <END> 'scapes'

        }, # <END> 'land'

###################
#### COMMUNITY ####
###################
    'comm': {

        'pops': {

            0  :   {
                #pop name; each pop must get a unique numeric or string name 
                #(e.g. 0, 0.1, 'pop0', 'south', 'C_fasciata'); default to 
                #serial integers from 0

            ##########################
            #### pop num. 0: init ####
            ##########################

                'init': {
                    'N':                200,
                        #starting population size
                    'K_scape_num':      0,
                        #the scape_num of the raster to use as the carrying-capacity raster (K)
                    'K_fact':           2
                        #the factor to multiply the K raster by in order to generate pop.K
                    }, # <END> 'init'

            ############################
            #### pop num. 0: mating ####
            ############################

                'mating'    : {
                    'repro_age':            0,
                        #age at sexual maturity (int or float for non-sexual species, tuple or list
                            #of two ints/floats for sexual species; set to 'None' to not make this
                            #an age-structured species
                    'max_age':              5,
                        #age beyond which all individuals will automatically die; default to None
                    'sex':                  False,
                        #is this a sexual species?
                    'sex_ratio':            1/1,
                        #ratio of males to females
                    #NOTE: I CAN PROBABLY GET RID OF THIS PARAMETER...
                    'distweighted_birth':  False,
                        #should the probability of birth be weighted by the distance between
                            #individuals in a pair?
                    'R':                    0.5,
                        #pop intrinsic growth rate
                    'b':                    0.2,
                        #population intrinsic birth rate (implemented as the probability
                            #that an identified potential mating pair successfully mates);
                            #NOTE: this may later need to be re-implemented to allow for spatial
                            #variation in intrinsic rate (e.g. expression as a raster) and/or for
                            #density-dependent births as well as deaths
                    'n_births_distr_lambda':      4,
                        #expected value of offspring for a successful mating pair (used as the lambda value in a Poisson distribution)
                    'mating_radius':        1
                        #radius of mate-searching area
                    }, # <END> 'mating'

            ###############################
            #### pop num. 0: mortality ####
            ###############################

                'mortality'     : {
                    'n_deaths_distr_sigma':           0.2,
                        #std for the normal distribution used to choose the r.v. of deaths
                            #per timestep (mean of this distribution is the overshoot,
                            #as calculated from pop.size and pop.census())
                    'selection':                True,
                        #should the population undergo natural selection?
                    'dens_dependent_fitness':   True,
                        #should fitness be density dependent? (note: helps to avoid subpopulation 'clumping')
                    'dens_grid_window_width':   None,
                        #with window-width used for the Density_Grid_Stack that calculates pop density
                            #(if set to None, defaults to the closest factor of the larger landscape
                            #dimension to 1/10th of that dimension)
                            #NOTE: will eventually default to an approximation of Wright's genetic neighborhood
                            #distance, based on the population's movement/dispersal parameters
                   'd_min':                     0.01,
                        #minimum neutral (i.e. non-selection driven) probability of death
                    'd_max':                    0.90,
                        #maximum neutral probability of death
                    }, # <END> 'mortality'

            ##############################
            #### pop num. 0: movement ####
            ##############################

                'movement': {
                   'move':          True,
                        #is this a mobile species?
                    'direction_distr_mu':     0,
                        #mu for von mises distribution defining movement directions
                    'direction_distr_kappa':  0,
                        #kappa for von mises distribution
                    'distance_distr_mu':      0.5,
                        #mean movement-distance (lognormal distribution)
                    'distance_distr_sigma':   0.5,
                        #sd of movement distance
                    'dispersal_distr_mu':     0.5,
                        #mean dispersal distance (lognormal distribution)
                    'dispersal_distr_sigma':  0.5,
                        #sd of dispersal distance

                    'move_surf'     : {
                        'scape_num':                    0,
                            #scape number to use as the movement surface
                        'mixture':                      True,
                            #should this MovementSurface be composed of
                            #VonMises mixture distribution approximations (i.e.
                            #True) or of unimodal VonMises distribution
                            #approximations (i.e. False); the latter is better
                            #for landscapes characterized by gradual gradients
                            #(i.e. where many cells' neighborhoods have very
                            #little variation between the highest- and lowest
                            #permeability values, so that mixture distributions
                            #would be largely uniform in all directions);
                            #defaults to True
                        'approximation_len':            7500,
                            #length of the lookup vectors (numpy arrays) used to approximate
                                #the VonMises mixture distributions at each cell
                        'vm_distr_kappa':                     None,
                            #kappa value to use in the von Mises mixture distributions (KDEs)
                                #underlying resistance surface movement
                        'gauss_KDE_bw':                 None
                            #bandwidth value to use in the Gaussian KDEs that are created to
                                #approximate the von Mises mixture distributions (KDEs)
                                #underlying resistance surface movement
                        } # <END> 'move_surf'

                    },    # <END> 'movement'


            ##############################
            #### pop num. 0: gen_arch ####
            ##############################

                'gen_arch': {
                    'L':                        10,
                        #total number of loci
                    'l_c':                      [10],
                        #chromosome lengths [sum(l_c) == L is enforced]
                    'gen_arch_file':            None,
                        #if not None, should point to a file stipulating a
                            #custom genomic architecture (i.e. a CSV with loci
                            #as rows and 'locus_num', 'p', 'r', 'trait', and
                            #'alpha' as columns, such as is created by
                            #main.make_params_file, when the custom_gen_arch
                            #arugment is True)
                    'mu_neut':                  1e-9,
                        #genome-wide neutral mutation rate, per base per generation
                            #(set to 0 to disable neutral mutation)
                    'mu_delet':                 1e-9,
                        #genome-wide deleterious mutation rate, per base per generation
                            #(set to 0 to disable deleterious mutation)
                            #NOTE: these mutations will fall outside the loci involved in any traits
                            #being simulated, and are simply treated as universally deleterious, with the same
                            #negative influence on fitness regardless of spatial context
                    'mut_log':                  False,
                        #whether or not to store a mutation log; if true, will be saved as mut_log.txt
                        #within each iteration's subdirectory
                    'delet_s_distr_shape':       0.2,
                    'delet_s_distr_scale':       0.2,
                        #mean and standard deviation of the gamma distribution
                        #parameterizig the per-allele effect size of 
                        #deleterious mutations (std = 0 will fix all mutations
                        #for the mean value)
                    'r_distr_alpha':             0.5,
                        #alpha for beta distribution of linkage values
                            #NOTE: alpha = 14.999e9, beta = 15e9 has a VERY sharp peak on D = 0.4998333,
                            #with no values exceeding equalling or exceeding 0.5 in 10e6 draws in R
                    'r_distr_beta':              15e9,
                        #beta for beta distribution of linkage values
                    'use_dom':                  False,
                        #whether or not to use dominance (default to False)
                            #NOTE: REALLY JUST NEED TO GET RID OF THE DOMINANCE THING; IT'S ALL MESSED UP
                    'pleiotropy':               True,
                        #allow pleiotropy? (i.e. allow same locus to affect value of more than one trait?) false
                    'recomb_rate_custom_fn':    None,
                        #if provided, must be a function that returns a single recombination rate value (r) when called
                    'recomb_lookup_array_size': int(1e3),
                        #the size of the recombination-path lookup array to have
                            #read in at one time (needs to be comfortably larger than the anticipated totaly number of
                            #recombination paths to be drawn at once, i.e. than 2 times the anticipated most number of births at once)
                    'n_recomb_paths':           int(1e4),
                        #the total number of distinct recombination paths to
                            #generate at the outset, to approximate truly free recombination at the recombination rates specified
                            #by the genomic architecture (hence the larger the value the less the likelihood of mis-approximation artifacts)

                    'traits': {

                        0: {
                            #an arbitrary number of traits can be provided for a genomic_architecture object
                            'name':             'trait0',
                                #each trait must be a given a string name (e.g. 'trait0', 'scape0_trait', 'min_temp_trait', 'bill_length')
                            'scape_num':        0,
                                #the landscape numbers to be used for selection on this trait
                            'phi':              0.1,
                                #phenotypic selection coefficient for this trait; can either be a
                                    #numeric value, or can be an array of spatialized selection
                                    #values (with dimensions equal to land.dims)
                            'n_loci':           1,
                                #number of loci to be assigned to this trait
                            'mu':      1e-9,
                                #mutation rate for this trait (if set to 0, or if genome['mutation'] == False, no mutation will occur)
                                    #(set to 0 to disable mutation for this trait)
                            'alpha_distr_mu' : 0,
                            'alpha_distr_sigma' : 0.5,
                                #the mean and standard deviation of the normal distribution used to choose effect size
                                    #(alpha) for this trait's loci
                                    #NOTE: for mean = 0, std = 0.5, one average locus is enough to generate both optimum
                                    #genotypes; for mean = 0, std = 0.025, 10 loci should generate both (on average, but depends of course on
                                    #the random sample of alphas drawn); and so on linearly
                            'gamma':            1,
                                #gamma exponent for the trait's fitness function (determines the shape of the
                                #curve of fitness as a function of absolute difference between an individual's
                                #phenotype and its environment; <1 = concave up, 1 = linear, >1 = convex up)
                            'univ_advant':      False
                                #is the trait unviersally advantageous? if so, phenotypes closer to 1 will
                                    #have higher fitness at all locations on the land
                            }, # <END> trait 0


    #### NOTE: Individual Traits' sections can be copy-and-pasted (and
    #### assigned distinct keys and names), to create additional Traits.


                        }, # <END> 'traits'

                    }, # <END> 'gen_arch'


            ############################
            #### pop num. 0: change ####
            ############################

                'change': {

                    'dem': {
                        #(all population sizes are expressed relative to the carrying-capacity
                            #raster at the time that the demographic change event begins (i.e. as
                            #factors by which pop.K will be multiplied; thus they can also be thought
                            #of as multipliers of the expected total population size (i.e. pop.K.sum())
                            #and they will generally change the average population size by that multiple,
                            #but of course not precisely, because population size is stochastic. If you
                            #seek exact control of total population size, please seek a simpler simulation
                            #model, perhaps a coalescent one.

                        0: {
                            #can add an arbitrary number of demographic change events for
                                #each population, each event identified by a distinct integer
                            'kind':             'custom',
                                #what kind of change event? ('monotonic', 'stochastic', 'cyclical', 'custom')
                            'start':            200,
                                #at which timestep should the event start?
                            'end':              1200,
                                #at which timestep should the event end?
                            'rate':             .98,
                                #at what rate should the population change each timestep
                                    #(positive for growth, negative for reduction)
                            'interval':         11,
                                #at what interval should stochastic change take place (None defaults to every timestep)
                            'dist':             'uniform',
                                #what distribution to draw stochastic population sizes from (valid values: 'uniform', 'normal')
                            'size_target':      None,
                                #what is the target size of the demographic change event (defaults to None)
                            'n_cycles':         20,
                                #how many cycles of cyclical change should occur during the event?
                            'size_range':       (0.5, 1.5), 
                                #an iterable of the min and max population sizes to be used in stochastic or cyclical changes
                            'timesteps':        [6,8],
                                #at which timesteps should custom changes take place?
                            'sizes':            [2,0.25],
                                #what custom size-changes should occur at the above-stipulated timesteps?
                            } # <END> event 0
 



    #### NOTE: Individual demographic change events' sections can be
    #### copy-and-pasted (and assigned distinct keys and names), to create
    #### additional events.


                        }, # <END> 'dem'

                        } # <END> 'change'

                }, # <END> pop num. 0

            1  :   {
                #pop name; each pop must get a unique numeric or string name 
                #(e.g. 0, 0.1, 'pop0', 'south', 'C_fasciata'); default to 
                #serial integers from 0

            ##########################
            #### pop num. 1: init ####
            ##########################

                'init': {
                    'N':                200,
                        #starting population size
                    'K_scape_num':      0,
                        #the scape_num of the raster to use as the carrying-capacity raster (K)
                    'K_fact':           2
                        #the factor to multiply the K raster by in order to generate pop.K
                    }, # <END> 'init'

            ############################
            #### pop num. 1: mating ####
            ############################

                'mating'    : {
                    'repro_age':            0,
                        #age at sexual maturity (int or float for non-sexual species, tuple or list
                            #of two ints/floats for sexual species; set to 'None' to not make this
                            #an age-structured species
                    'max_age':              5,
                        #age beyond which all individuals will automatically die; default to None
                    'sex':                  False,
                        #is this a sexual species?
                    'sex_ratio':            1/1,
                        #ratio of males to females
                    #NOTE: I CAN PROBABLY GET RID OF THIS PARAMETER...
                    'distweighted_birth':  False,
                        #should the probability of birth be weighted by the distance between
                            #individuals in a pair?
                    'R':                    0.5,
                        #pop intrinsic growth rate
                    'b':                    0.2,
                        #population intrinsic birth rate (implemented as the probability
                            #that an identified potential mating pair successfully mates);
                            #NOTE: this may later need to be re-implemented to allow for spatial
                            #variation in intrinsic rate (e.g. expression as a raster) and/or for
                            #density-dependent births as well as deaths
                    'n_births_distr_lambda':      4,
                        #expected value of offspring for a successful mating pair (used as the lambda value in a Poisson distribution)
                    'mating_radius':        1
                        #radius of mate-searching area
                    }, # <END> 'mating'

            ###############################
            #### pop num. 1: mortality ####
            ###############################

                'mortality'     : {
                    'n_deaths_distr_sigma':           0.2,
                        #std for the normal distribution used to choose the r.v. of deaths
                            #per timestep (mean of this distribution is the overshoot,
                            #as calculated from pop.size and pop.census())
                    'selection':                True,
                        #should the population undergo natural selection?
                    'dens_dependent_fitness':   True,
                        #should fitness be density dependent? (note: helps to avoid subpopulation 'clumping')
                    'dens_grid_window_width':   None,
                        #with window-width used for the Density_Grid_Stack that calculates pop density
                            #(if set to None, defaults to the closest factor of the larger landscape
                            #dimension to 1/10th of that dimension)
                            #NOTE: will eventually default to an approximation of Wright's genetic neighborhood
                            #distance, based on the population's movement/dispersal parameters
                   'd_min':                     0.01,
                        #minimum neutral (i.e. non-selection driven) probability of death
                    'd_max':                    0.90,
                        #maximum neutral probability of death
                    }, # <END> 'mortality'



                }, # <END> pop num. 1



    #### NOTE: Individual Populations' sections can be copy-and-pasted (and
    #### assigned distinct keys and names), to create additional Populations.


            }, # <END> 'pops'

        }, # <END> 'comm'

###############
#### MODEL ####
###############
    'model': {
        'time': {
            #parameters to control the number of burn-in and main timesteps to
            #run for each iterations
            'T':            12,
                #total model runtime (in timesteps)
            'burn_T':       30
                #minimum burn-in runtime (in timesteps; this is a mininimum because
                    #burn-in will run for at least this long but until
                    #stationarity detected, which will likely be longer)
            }, # <END> 'timesteps'

        'its': {
            #parameters to control how many iterations of the model to run,
            #and whether or not to randomize the land and/or community
            #objects in each model iteration
            'n_its': 1,
                #how many iterations of the model should be run?
            'rand_land':    False,
                #randomize the land for each new iteration?
            'rand_comm':    False,
                #randomize the community for each new iteration?
            'rand_burn':  False,
                #randomize the burn-in for each new iteration? (i.e. burn in
                #each time, or burn in once at creation and then use the same
                #burnt-in population for each iteration?)
            }, # <END> 'iterations'



        'stats': {
            #dictionary defining which stats to be calculated, and parameters for
                #their calculation (including frequency, in timesteps, of collection)
                #valid stats include:
                    # 'Nt'  : population census size
                    # 'het' : heterozygosity
                    # 'maf' : minor allele frequency
                    # 'ld'  : linkage disequilibrium
                    # 'mean_fit' : mean fitness 
            'Nt':       {'calc': True,
                         'freq': 2,
                        },
            'het':      {'calc': True,
                         'freq': 1,
                         'mean': False,
                        },
            'maf':      {'calc': True,
                         'freq': 5,
                        },
            'ld':       {'calc': True,
                         'freq': 10,
                        },
            'mean_fit': {'calc': True,
                             'freq': 3,
                        },
            }, # <END> 'stats'


        } # <END> 'model'

    } # <END> params
