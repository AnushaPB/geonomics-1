#!/usr/bin/python
#selection.py


'''
##########################################

Module name:          ops.selection


Module contains:
                      - Functions to implement fitness and selection
 

Author:               Drew Ellison Hart
Email:                drew.hart@berkeley.edu
Github:               URL
Start date:           04-28-17
Documentation:        URL


##########################################
'''


import numpy as np
from collections import OrderedDict as OD


######################################
# -----------------------------------#
# FUNCTIONS -------------------------#
# -----------------------------------#
######################################

#Get the phenotypic values of all individuals for a given trait
def calc_phenotype(ind, trait):
    #get number of loci and their allelic effect sizes
    n_loci = trait.n_loci
    alpha = trait.alpha

    #if monogenic, then divide genotype by 2, 
    #but if polygenic then multiply genotype by alpha (i.e. effect size) 
    #at all loci, sum across loci, then add to 0.5 (the null phenotypic value)
    phenotype = np.float32(ind.genome[trait.loci,:].sum(axis = 1))
    if n_loci > 1:
        phenotype = 0.5 + sum(phenotype*alpha)
    else:
        phenotype = phenotype[0]/2

    return(phenotype)


def calc_fitness_one_trait(t, e, z, pop):
    fit = 1 - t.get_phi(pop)*(abs((e[:,t.scape_num]**(not t.univ_advant)) - z[:,t.idx])**t.gamma)
    return(fit)


def calc_fitness_traits(pop, trait_num = None, set_fit = False):
    traits = pop.gen_arch.traits.values()
    #subset for single trait, if indicated
    if trait_num is not None:
        traits = [list(traits)[trait_num]]
    #get all individuals' environmental values
    e = pop.get_habitat()
    #get all individuals' phenotypes
    z = pop.get_phenotype()
    #create lambda function with current e, z, and pop objects
    calc_fitness_lambda = lambda t: calc_fitness_one_trait(t, e, z, pop)
    #map the calc_sngl_trait_fitness function to all traits, then calculate overall fitness as product of
    #fitness for each trait
    fit = np.stack(list(map(calc_fitness_lambda, traits))).prod(axis = 0)
    #for polygenic traits, loci with very large effect sizes can generate fitnesses less than 0; correct for this
    fit = np.clip(fit, a_min = 0.001, a_max = None)
    #set individuals' fitness attributes, if indicated
    [ind.set_fitness(f) for ind,f in zip(pop.values(), fit)];
    #if set_fit:
    #    indices = [*pop]
    #    [pop[indices[n]].set_fitness(f) for n,f in enumerate(fit)];
    return(fit)


def calc_fitness_deleterious_mutations(pop):
    #create an np.array that has individuals in rows and their diploid genotypes for each of
    #the deleterious loci in the cols (0, 1, or 2, to facilitate the fitness math, because s values
    #(i.e. selection coefficients) are expressed per allele)
    deletome = np.sum(np.stack([ind.genome[[*pop.gen_arch.delet_loci.keys()],:] for ind in pop.values()]), axis = 2)
    fit = 1 - np.multiply(deletome, np.array([*pop.gen_arch.delet_loci.values()]))
    fit = fit.prod(axis = 1)
    return(fit)


#Get the vector of mortalities (probabilies of death) for a given density-dependent Pr(death) at a cell, the
#environmental value(s) at that cell, the phenotype(s) of the trait(s) for the individuals found there, and the selection
#coefficient(s) on the trait(s)
def calc_prob_death(pop, d):

    #set a default w array
    w = np.array([1]*len(pop))

    #get trait-related fitness, if traits
    if len(pop.gen_arch.traits) > 0:
        w = w * calc_fitness_traits(pop)

    #if the population has deleterious mutations, get fitnesses related to them (i.e. operationalize background selection)
    if len(pop.gen_arch.delet_loci) > 0:
        w = w * calc_fitness_deleterious_mutations(pop) 

    #[death_probs.update({i: 1-(1-d[i])*w}) for i, w in W.items()];
    death_probs = 1-(1-d)*w
   
    #assert np.alltrue(np.array(list(death_probs.values()))>=0)
    #assert np.alltrue(np.array(list(death_probs.values()))<=1)

    #assert False not in [w >= 0 and w <= 1 for w in death_probs.values()], 'ERROR: Some fitness values outside the 0-to-1 range.'
    assert (death_probs > 0).all() and (death_probs < 1).all(), 'ERROR: Some fitness values outside the 0-to-1 range.'

    #return
    return(death_probs)

