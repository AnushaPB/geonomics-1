#/usr/bin/python
#PRACTICE_create_land_genomic_arch_pop.py

'''Creates a landscape object, a genomic architecture object, and population object, using the current params
dictionary.'''


#set seed, if requested
if params['set_seed']: 
    random.seed(params['seed_num'])
    r.seed(params['seed_num'])

            


land = landscape.build_scape_stack(params = params)
genomic_arch = genome.build_genomic_arch(params = params, land = land)
pop = population.create_population(genomic_arch = genomic_arch, land = land, params = params)

