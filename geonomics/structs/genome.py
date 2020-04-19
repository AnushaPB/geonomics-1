#!/usr/bin/python
# genome.py

# flake8: noqa


'''
Classes, associated methods, and supporting functions for all genomic
components
'''

# geonomics imports
from geonomics.ops import mutation
from geonomics.utils.viz import _check_display

# other imports
import numpy as np
import pandas as pd
from numpy import random as r
import matplotlib as mpl
_check_display()
import matplotlib.pyplot as plt
from collections import OrderedDict as OD
import warnings
import random
import bisect

######################################
# -----------------------------------#
# CLASSES ---------------------------#
# -----------------------------------#
######################################


# an error to raise if a simulation is not given enough neutral loci to fit
# the total number of expected mutations over the total parameterized runtime
# under the infinite sites model
class MutationRateError(Exception):
    pass


class Recombinations:
    def __init__(self, L, positions, n, r_distr_alpha, r_distr_beta,
                 recomb_rates):
        # genome length
        self._L = L
        # organize the potential recombination breakpoint positions
        if positions is None:
            positions = np.arange(self._L)
        else:
            positions.sort()
        # number of recombination events to simulate and cache for the model
        # NOTE: the higher this number, the more accurately geonomics
        #       will simulate the stipulated recombination rates
        self._n = n
        # alpha and beta parameters for the beta distribution from which
        # recombination rates can be drawn
        self._r_distr_alpha = r_distr_alpha
        self._r_distr_beta = r_distr_beta
        # set the potential recombination breakpoints, their recombination
        # rates, and the cache of simulated recombination events to be used
        # by the model
        (self._positions,
         self._rates,
         self._events) = _draw_recombination_events(self._n, positions,
                                                    self._r_distr_alpha,
                                                    self._r_distr_beta,
                                                    recomb_rates,
                                                    self._L)

    def _get_events(self, size):
        events = random.sample(self._events, size)
        return events


   # take a recombination event key and a parent's node ids,
   # return a zip object containing 
        # 1.) node id for parent's id (corresponding to the id in the
        # tskit.TableCollection.nodes table);
        # 2.) left end of the segment (inclusive, according to tskit)
        # 3.) right end (exclusive)
    def _get_recombination_seg_info(self, start_homologue, event_key,
                                    node_ids):
        # NOTE: adding 0.5 to all recombination breakpoints, to indicate
        # that reocmbination 'actually' happens halfway between a pair of loci,
        # (i.e. it actually subsets Individuals' genomes in that way)
        # without having the hold all the 0.5's in the Recombinations._events
        # data struct (to save on memory)
        left = np.array([0] + [*self._events[event_key] + 0.5])
        right = np.array([*self._events[event_key] + 0.5] + [self._L])
        homologue_nodes = node_ids[[(i + start_homologue) % 2 for i in range(
                                                                   len(left))]]
        seg_info = zip(homologue_nodes, left, right)
        return seg_info


    def _get_recombination_subsetter(self, start_homologue, locs, event_key):
        homol_idxs = [(start_homologue + bisect.bisect_left(
                        self._events[event_key], loc) % 2) % 2 for loc in locs]
        locus_idxs = range(len(locs))
        subsetter = (locus_idxs, homol_idxs)
        return subsetter


class Trait:
    def __init__(self, idx, name, phi, n_loci, mu, layer, alpha_distr_mu,
                 alpha_distr_sigma, max_alpha_mag, gamma, univ_adv):
        self.idx = idx
        self.name = name
        self.phi = phi
        self.n_loci = n_loci
        if mu is None:
            mu = 0
        self.mu = mu
        self.lyr_num = layer
        self.alpha_distr_mu = alpha_distr_mu
        self.alpha_distr_sigma = alpha_distr_sigma
        self.max_alpha_mag = max_alpha_mag
        self.gamma = gamma
        self.univ_adv = univ_adv

        self.loci = np.int64([])
        self.loc_idx = np.int64([])
        self.alpha = np.array([])

    def _get_phi(self, spp):
        if type(self.phi) in (float, int):
            phi = np.array([self.phi]*len(spp))
        else:
            phi = self.phi[spp.cells[:, 1], spp.cells[:, 0]]
        return(phi)

    def _set_loci(self, loci):
        # set the loci
        self.loci = np.hstack((self.loci, np.array([*loci])))
        self.loci.sort()
        # set the number of loci
        self.n_loci = self.loci.size

    def _set_loc_idx(self, nonneut_loci):
        # set an index of the loci's indices in the nonneut_loci object,
        # to use when subsetting for the trait's genotypes
        self.loc_idx = np.array([np.where(
                                nonneut_loci == n)[0][0] for n in self.loci])

    def _add_locus(self, locus, alpha, idx):
        # get insertion index for the locus 
        insert_pt = bisect.bisect_left(self.loci, locus)
        # insert in the loci
        self.loci = np.hstack((self.loci[:insert_pt],
                               locus,
                               self.loci[insert_pt:]))

        # insert the effect size for the locus
        self.alpha= np.hstack((self.alpha[:insert_pt],
                               alpha,
                               self.alpha[insert_pt:]))

        # insert in the loc_idx
        # NOTE: add 1 to all superseding locus indexes, to account for
        # locus newly inserted into genotype arrays
        self.loc_idx = np.hstack((self.loc_idx[:insert_pt],
                                  idx,
                                  self.loc_idx[insert_pt:] + 1))

        # increment the number of loci
        self.n_loci += 1


class GenomicArchitecture:
    def __init__(self, dom, g_params, land, recomb_rates=None,
                 recomb_positions=None):
        # ploidy (NOTE: for now will be 2 by default; later could consider
        # enabling polyploidy)
        self.x = 2
        # total length (i.e. number of markers)
        self.L = g_params.L
        # placeholder for the starting allele freqs for all loci
        self.p = None
        # True/False regarding whether to allow a locus to affect the
        # phenotype of more than one trait; defaults to False
        self.pleiotropy = g_params.pleiotropy
        # array of dominance values for all loci
        self.dom = dom
        # set the _use_dom attribute based on whether any loci have a 1 for
        # their dominance value
        self._use_dom = np.any(self.dom)
        # whether or not to use sexes for this species
        self.sex = g_params.sex

        # genome-wide neutral mutation rate
        self.mu_neut = g_params.mu_neut
        # array to keep track of all loci that don't influence the
        # phenotypes of any trait; defaults to all loci, then will be updated
        self.neut_loci = np.array(range(self.L))
        # array to keep track of all loci that influence the phenotype of at
        # least one trait; after burn-in, will be updated as needed
        self.nonneut_loci = np.array([])

        # genome-wide deleterious mutation rate
        self.mu_delet = g_params.mu_delet
        self.delet_alpha_distr_shape = g_params.delet_alpha_distr_shape
        self.delet_alpha_distr_scale = g_params.delet_alpha_distr_scale


        # arrays to track deleterious loci, their genotype indices, and their
        # strengths of selection
        self.delet_loci = np.int64([])
        self.delet_loc_idx = np.int64([])
        self.delet_loci_s = np.array([])

        # add a dict of Trait objects, if necessary
        self.traits = None
        if 'traits' in [*g_params]:
            self.traits = _make_traits(g_params.traits, land)

        # set self._mu_tot, the total per-site, per-generation mutation rate
        mus = [mu for mu in (self.mu_neut, self.mu_delet) if mu is not None]
        if self.traits is not None:
            mus = mus + [trt.mu for trt in self.traits.values()]
        self._mu_tot = sum(mus)

        # set a placeholder for the species' mutable loci
        # (to be filled after burn-in)
        self._mutables = None

        # attribute that will be replaced with the estimated total number of
        # mutations per iteration, once it's estimated at the end of the first
        # burn-in
        self._mut_fns = self._make_mut_fns_dict()
        # set ._planned_muts to None, for now (this is not yet implemented,
        # but thinking about it
        self._planned_muts = None

        # The recombination-paths object will be assigned here; used to
        # speed up large quantities of binomial draws needed for recombination
        self.recombinations = Recombinations(self.L, recomb_positions,
                                             g_params.n_recomb_sims,
                                             g_params.r_distr_alpha,
                                             g_params.r_distr_beta,
                                             recomb_rates)

    # method to make a _mut_fns dict, containing a function
    # for each type of mutation for this species
    def _make_mut_fns_dict(self):
        mut_fns = {}
        if self.mu_neut > 0:
            def neut_fn(spp, offspring):
                return(mutation._do_neutral_mutation(spp, offspring))
            mut_fns.update({'neut': neut_fn})
        if self.mu_delet > 0:
            def delet_fn(spp, offspring):
                return(mutation._do_deleterious_mutation(spp, offspring))
            mut_fns.update({'delet': delet_fn})
        if self.traits is not None:
            for trait_num in self.traits:
                if self.traits[trait_num].mu > 0:
                    def trait_fn(spp, offspring, trait_num=trait_num):
                        return(mutation._do_trait_mutation(spp, offspring,
                                                           [trait_num]))
                    mut_fns.update({'t%i' % trait_num: trait_fn})
        return mut_fns

    # method to draw mutation types for any number of mutations chosen
    # to occur in a given timestep
    def _draw_mut_types(self, num):
        type_dict = {'neut': self.mu_neut,
                     'delet': self.mu_delet}
        if self.traits is not None:
            trait_dict = {'t%i' % (k): v.mu for k, v in self.traits.items()}
            type_dict.update(trait_dict)
        types = []
        probs = []
        for k, v in type_dict.items():
            types.append(k)
            probs.append(v)
        probs = [p/sum(probs) for p in probs]
        choices = r.choice(types, p=probs, size=num, replace=True)
        return(choices)

    # method for drawing an effect size for one or many loci
    def _draw_trait_alpha(self, trait_num, n=1):
        mu = self.traits[trait_num].alpha_distr_mu
        sigma = self.traits[trait_num].alpha_distr_sigma
        max_alpha_mag = self.traits[trait_num].max_alpha_mag
        if max_alpha_mag is not None:
            min_alpha = -1 * max_alpha_mag
            max_alpha = max_alpha_mag
        else:
            min_alpha = max_alpha = max_alpha_mag
        # use mu value as the fixed effect size, if sigma is 0
        if sigma == 0:
            alpha = mu * np.array([1 - (i % 2)*2 for i in range(n)])
        else:
            alpha = r.normal(self.traits[trait_num].alpha_distr_mu,
                             self.traits[trait_num].alpha_distr_sigma, n)
            if max_alpha_mag is not None:
                alpha = np.clip(alpha, min_alpha, max_alpha)
        # otherwise use mu and sigma to draw effects from
        # (because effects will be added to 0)
        if self.traits[trait_num].n_loci == 1:
            alpha = np.abs(alpha)
        return(alpha)

    # method for drawing new deleterious mutational fitness effects
    def _draw_delet_s(self):
        s = r.gamma(self.delet_alpha_distr_shape, self.delet_alpha_distr_scale)
        s = min(s, 1)
        return(s)

    # method for assigning loci to traits
    def _set_trait_loci(self, trait_num, mutational=False,
                        loci=None, alpha=None):
        # if this is not the result of a point mutation, but instead
        # either an initial setup or manually introduced, then grab the
        # number of loci to be assigned
        if not mutational:
            n = self.traits[trait_num].n_loci
            assert n <= self.L, ("The number of loci parameterized for "
                                 "trait number %i ('n_loci') is greater "
                                 "than the length of the genome!")
        # otherwise, assign a single locus
        else:
            n = 1
        if loci is not None:
            if not np.iterable(loci):
                loci = [loci]
            assert len(set([*loci])) == len(loci), ("Some of the trait "
                                                    "loci provided appear "
                                                    "to be repeated.")
        # else, draw loci randomly, either allowing pleiotropy or not
        elif not self.pleiotropy:
            loci = set(r.choice(self.neut_loci, size=n, replace=False))
        elif self.pleiotropy:
            loci = set(r.choice(range(self.L), size=n, replace=False))
        # update the trait's loci
        self.traits[trait_num]._set_loci(loci)
        # add these loci to self.non-neutral and remove from
        # self.neut_loci, to keep track of all loci underlying any
        # traits (for purpose of avoiding pleiotropy)
        self.nonneut_loci = np.array(sorted([*self.nonneut_loci] + [*loci]))
        self.neut_loci = np.array(sorted([*set(self.neut_loci).difference(
                                                    set(self.nonneut_loci))]))
        # if the effect size(s) is/are provided, use those
        if alpha is not None:
            if not np.iterable(alpha):
                alpha = np.array([alpha])
            effects = np.array([*alpha])
        # else, draw effects from a Gaussian dist with mean 0 and sigma
        # provided by trait params (as per e.g. Yeaman and Whitlock 2011)
        else:
            effects = self._draw_trait_alpha(trait_num, n)
        # if this is drawing the effect of a monogenic trait's locus (i.e. if
        # it's drawing only one value, but it's not mutational), then coerce
        # the effects to [0.5]
        if not mutational and n == 1:
            effects = np.array([0.5])
        # check that loci and effects are of equal length
        assert len(loci) == len(effects), ('Lengths of the two arrays '
                                           'containing the new trait loci and '
                                           'their effects are not equal.')
        # then add the effects to the trait's alpha array
        self.traits[trait_num].alpha = np.hstack((self.traits[trait_num].alpha,
                                                  effects))

    # add a nonneutral locus to the genomic architecture
    # NOTE: either trait_nums or delet_s must be non-None,
    # and trait_nums must be iterable (if not None)
    def _add_nonneut_locus(self, locus, trait_nums=None, delet_s=None):
        # remove from the neut_loci array
        self.neut_loci = np.delete(self.neut_loci,
                                   np.where(self.neut_loci == locus))
        # add the locus to the nonneut_loci array
        idx = bisect.bisect_left(self.nonneut_loci, locus)
        self.nonneut_loci = np.hstack((self.nonneut_loci[:idx],
                                       locus,
                                       self.nonneut_loci[idx:]))

        # add the locus to either trait loci, if necessary
        if trait_nums is not None and delet_s is None:
            for n in trait_nums:
                alpha = self._draw_trait_alpha(n)[0]
                self.traits[n]._add_locus(locus, alpha, idx)
        # or else add to the deleterious loci
        elif delet_s is not None and trait_nums is None:
            del_idx = bisect.bisect_left(self.delet_loci, locus)
            # add the locus, its genome-index (for subsetting individuals'
            # genomes when calculating fitness), and its strength of selection
            # to the deleterious locus trackers
            self.delet_loci = np.hstack((self.delet_loci[:del_idx],
                                         locus,
                                         self.delet_loci[del_idx:]))
            self.delet_loc_idx = np.hstack((self.delet_loc_idx[:del_idx],
                                         idx,
                                         self.delet_loc_idx[del_idx:]))
            self.delet_loci_s = np.hstack((self.delet_loci_s[:del_idx],
                                         delet_s,
                                         self.delet_loci_s[del_idx:]))

        #TODO REMOVE NEXT 2 LINES AFTER TESTING
        else:
            assert True == False, "BOTH TRAITS_NUMS AND DELET_S CANT BE NONE!"

        return idx


    # method for plotting all allele frequencies for the species
    def _plot_allele_frequencies(self, spp):
        speciome = np.stack([ind.g for ind in spp.values()])
        freqs = speciome.sum(axis=2).sum(axis=0) / (2*speciome.shape[0])
        plt.plot(range(self.L), self.p, ':r', label='start freq.')
        plt.plot(range(self.L), freqs, '-b', label='curr. freq.')
        plt.xlabel('locus')
        plt.ylabel('frequency')
        plt.legend()
        plt.show()

    # method for pickling a genomic architecture
    def _write_pickle(self, filename):
        import cPickle
        with open(filename, 'wb') as f:
            cPickle.dump(self, f)


######################################
# -----------------------------------#
# FUNCTIONS -------------------------#
# -----------------------------------#
######################################

# generate allele_freqs
def _draw_allele_freqs(l):
    return(r.beta(1, 1, l))


def _make_traits(traits_params, land):
    params_copy = {**traits_params}
    # and set each Layer number using Layer names
    for k, v in params_copy.items():
        # the first time this is run during a model with random
        # communities at each iteration, the layer identified in
        # the traits_params will be a string indicating the layer's name
        if isinstance(v.layer, str):
            lyr_num = [num for num, lyr in land.items(
                                                ) if lyr.name == v.layer]
        # the second and later times it's run during such a model (see
        # previous comment), it will already have been swapped out for an int
        # indicating the layer's index num
        elif isinstance(v.layer, int):
            lyr_num = [num for num, lyr in land.items(
                                                ) if lyr.idx == v.layer]
        assert len(lyr_num) == 1, ("Expected to find a single Layer with "
                                   "the Layer name indicated for Trait %s, "
                                   "but instead found "
                                   "%i.") % (k, len(lyr_num))
        v['layer'] = lyr_num[0]
    # then for each of i traits, unpack the ith components of the remaining
    # params to create the trait dict
    traits = {n: Trait(n, k_v[0], **k_v[1]) for n, k_v in enumerate(
                                                        params_copy.items())}
    # for all monogenic traits, if the trait doesn't already have a 0 mutation
    # rate then coerce it to 0
    # NOTE: this is the because there is a good reason to use 0 as the 
    # baseline phenotype for monogenic traits but 0.5 as the baseline
    # for multilocus traits (to preserve symmetry of ability for individuals
    # to have phenotypes beyond 0 and 1 for a multilocus trait and thus
    # experience stabilizing selection within their optimal habitat), but
    # this means that there would be a huge problem if a monogenic trait
    # underwent an adaptive mutation and became polyenic bceause all of the
    # individuals' phenotypes would suddenly have to be recalculated and would
    # suddenly completely change
    for n, trt in traits.items():
        if trt.n_loci == 1:
            if trt.mu != 0:
                warnings.warn(("Coercing Trait %i ('%s') to a "
                               "0 mutation rate because it is monogenic."))
                trt.mu = 0
    return(traits)


# simulate recombination events
def _draw_recombination_events(n, positions, alpha=None, beta=None,
                               recomb_rates=None, genome_length=None):
    """
    NOTE: Positions and recomb_rates must be provided already sorted!
    """
    positions = [*positions]
    # optimize the data type, to save some memory
    if len(positions) <= 2**16:
        positions = np.int16(np.array(positions))
    else:
        positions = np.int32(np.array(positions))
    if recomb_rates is not None:
        assert len(recomb_rates) == len(positions), ("Lengths of provided "
                                                     "recombination "
                                                     "rates and recombination "
                                                     "positions don't match!")
    elif (alpha is not None and beta is not None):
        recomb_rates = np.clip(np.random.beta(a=alpha, b=beta,
                                              size=len(positions)),
                               a_min=0, a_max=0.5)
    elif alpha is not None:
        recomb_rates = np.ones(len(positions)) * alpha
    else:
        #NOTE: if no alpha and beta values were provided for the recomb-rate
        # beta distribution, set all interlocus recomb rates to a value that
        # results in an average of one recombination per gamete produced
        homog_recomb_rate = 1 / genome_length
        recomb_rates = np.ones(len(positions)) * homog_recomb_rate
    events = [positions[np.where(r.binomial(1,
                                            recomb_rates))] for _ in range(n)]
    # recast it as an int-keyed dict, so that when I use the recombination
    # events to simulate recombination I don't have to pass around the long
    # arrays, but instead can just random keys to index them out on the fly
    events = dict(zip(range(len(events)), events))
    return (np.array([*positions]), recomb_rates, events)


# build the genomic architecture
def _make_genomic_architecture(spp_params, land):
    # get the genome parameters
    g_params = spp_params.gen_arch
    # get the custom genomic-architecture file, if provided
    gen_arch_file = None
    if 'gen_arch_file' in g_params.keys():
        if g_params.gen_arch_file is not None:
            gen_arch_file = pd.read_csv(g_params.gen_arch_file)
            # ensure that trait and alpha columns are strings to start (because
            # in many cases alpha would likely read in as a float, if each row
            # has at most one alpha value because there's no pleiotropy, but in
            # case of pleiotropy I need to be able to use the str.split method
            # on each row's values further down)
            gen_arch_file['trait'] = [str(v) for v in gen_arch_file['trait']]
            gen_arch_file['alpha'] = [str(v) for v in gen_arch_file['alpha']]
            assert (np.all(
                (gen_arch_file['dom'] == 0) + gen_arch_file['dom'] == 1)), (
                "The 'dom' column of the custom genomic architecture file "
                "must contain only 0s and 1s (where 0 indicates codominance "
                "of the 0 and 1 alleles, 1 indicates that the 1 allele "
                "is dominant).")
            # check that each trait has in that file the number of loci
            # indicated by n_loci in that trait's params dict
            if 'traits' in [*g_params]:
                all_traits = [trt.strip() for row in [val.split(
                    ',') for val in gen_arch_file['trait']] for trt in row]
                for trt_name, trt in g_params.traits.items():
                    n_loci_in_file = sum(
                                    [trt == trt_name for trt in all_traits])
                    assert_msg = ("The number of times a Trait is appears "
                                  "in the custom genomic architecture file "
                                  "must be equivalent to the number of loci "
                                  "subtending that Trait as indicated by the "
                                  "'n_loci' key in its section of the "
                                  "parameters file.")
                    assert n_loci_in_file == trt.n_loci, assert_msg

    # get the sex parameter and add it as an item in g_params
    g_params['sex'] = spp_params.mating.sex

    # get the custom recomb_rates and recomb_positions from the
    # custom gen-arch file, if provided
    # NOTE: add 0.5 to each locus' position, because each recombination rate
    #       stipulated in gen_arch file is construed as the recombination rate
    #       at the midway point between that locus and the subsequent one
    recomb_rates = None
    recomb_positions = None
    if gen_arch_file is not None:
        recomb_rates = gen_arch_file['r'].values[:-1]
        recomb_positions = gen_arch_file['locus'].values[:-1] + 0.5

    # set locus-wise dominance values for the 1-alleles, using the 'dom' value
    # in the gen_arch params, unless a gen_arch_file was provided
    if gen_arch_file is None:
        # create an L-length array of boolean integers (where 0 = codominance,
        # 1 = dominance)
        dom = np.array([int(g_params.dom)] * g_params.L)
    else:
        # get the 'dom' column from the gen_arch_file
        dom = gen_arch_file['dom'].values

    # now make the gen_arch object
    gen_arch = GenomicArchitecture(dom, g_params, land,
                                   recomb_rates, recomb_positions)

    # set the loci and effect sizes for each trait, using the custom gen-arch
    # file, if provided
    if gen_arch_file is not None:
        # convert the trait names in the 'trait' column of the file into
        # lists of their trait numbers (i.e. their keys in the gen_arch
        # traits dict)
        trt_names_nums = {
            trt.name: num for num, trt in gen_arch.traits.items()}
        gen_arch_file['trait'] = [[trt_names_nums[
            val] for val in [x.strip() for x in row.split(
            ',')] if val in trt_names_nums] for row in gen_arch_file['trait']]
        # turn the values in the 'alpha' column into lists of
        # values, by splitting on commas
        # (this will allow people to assign a single locus
        # to more than one trait, i.e. to model pleiotropy)
        gen_arch_file['alpha'] = [
            [*map(float, row.split(','))] for row in gen_arch_file['alpha']]
        # get the loci and effect sizes for each trait
        loci = {}
        alphas = {}
        for trt_num in gen_arch.traits.keys():
            loci[trt_num] = np.array([*gen_arch_file['locus']])[
                [trt_num in row for row in gen_arch_file['trait']]]
            alphas[trt_num] = np.concatenate([np.array(row['alpha'])[
                [n == trt_num for n in row[
                    'trait']]] for i, row in gen_arch_file.iterrows()])
        # check that we got the same length of loci and effect sizes for
        # a trait, for all traits
        for trt_num in loci.keys():
            assert_msg = ("Expected to receive the same number of loci and "
                          "alphas (i.e. effect sizes) for trait number %i, "
                          "but instead got %i loci and %i "
                          "alphas.") % (trt_num, len(loci[trt_num]),
                                        len(alphas[trt_num]))

            assert len(loci[trt_num]) == len(alphas[trt_num]), assert_msg

        # add the loci and effect sizes for each of the traits to the
        # Trait object in the GenomicArchitecture
        for trait_num in gen_arch.traits.keys():
            gen_arch._set_trait_loci(trait_num, mutational=False,
                                     loci=loci[trait_num],
                                     alpha=alphas[trait_num])
    # or else randomly set the loci and effect sizes for each trait
    else:
        if gen_arch.traits is not None:
            for trait_num in gen_arch.traits.keys():
                gen_arch._set_trait_loci(trait_num, mutational=False)

    # now that all nonneutral loci have been selected, 
    # set each trait's loc_idx (which maps a trait's numeric loci to
    # their index positions in individuals' genomes)
    if gen_arch.traits is not None:
        for trt in gen_arch.traits.values():
            trt._set_loc_idx(gen_arch.nonneut_loci)

    assert_msg = ("The union of the gen_arch.neut_loci and "
                  "gen_arch.nonneut_loci sets does not contain all loci "
                  "indicated by gen_arch.L")
    assert len(set(range(gen_arch.L)).difference(
        set(gen_arch.neut_loci).union(
        set(gen_arch.nonneut_loci)))) == 0, assert_msg

    # draw locus-wise 1-allele frequencies, unless provided in
    # custom gen-arch file
    if gen_arch_file is None:
        if g_params.start_p_fixed is not None:
            assert 0 <= g_params.start_p_fixed <= 1, ("If a starting allele "
                                                      "frequency value is "
                                                      "provided then it must "
                                                      "be between 0 and 1.")
            gen_arch.p = np.array([g_params.start_p_fixed]*g_params.L)
            if g_params.start_neut_zero:
                gen_arch.p[gen_arch.neut_loci] = 0
        else:
            gen_arch.p = _draw_allele_freqs(g_params.L)
    else:
        gen_arch.p = gen_arch_file['p'].values

    return gen_arch


# reset genomes after burn-in
def _check_mutation_rates(gen_arch, est_tot_muts, burn_T, T):
    # if there do not appear to be enough space in the simulated genome for
    # the expected number of mutations then warn the user of that
    if est_tot_muts > 0.75 * len(
        [loc for loc in range(
                    gen_arch.L) if loc not in gen_arch.nonneut_loci]):
        raise MutationRateError(("This species has been "
                                 "parameterized with too few neutral "
                                 "loci to accommodate the expected "
                                 "number of mutations. (Geonomics only "
                                 "uses an infinite sites model.) "
                                 "Please tweak some combination of "
                                 "the genome length, model run time, "
                                 "or mutation rates."))


    # skip this step and force the neutral mutation rate to 0, if there are no
    # neutral loci in the genome as it was configured
    if len(gen_arch.neut_loci) == 0:
        raise MutationRateError(("This species has been parameterized "
                                 "with non-zero mutation rates but "
                                 "without any neutral loci, leaving no target "
                                 "for mutations. Please tweak the genome "
                                 "length and/or mutation rates."))
        gen_arch.mu_neut = 0
        gen_arch.mu_delet = 0
        for trt in gen_arch.traits.values():
            trt.mu = 0
    # or just outright skip this step if the parameterization included only
    # mutation rates of 0
    elif gen_arch._mu_tot == 0:
        pass
    # otherwise, set the mutable loci
    else:
        mutables = [*set(range(gen_arch.L)).difference(
                                            set(gen_arch.nonneut_loci))]
        r.shuffle(mutables)
        gen_arch._mutables = [*mutables]
    return


# function to generate mutations, after burn-in,
# and to assign them to a species' TableCollection's  current nodes,
# to produce the starting 1-allele frequencies parameterized for the species
def _make_starting_mutations(spp, tables):
    # get the starting frequencies for each site
    start_freqs = spp.gen_arch.p

    # get a set of all homologues, as tuples of (individual id, homologue idx)
    homologues = [*zip(np.repeat([*spp], 2),
                         [*range(spp.gen_arch.x)] * len(spp))]

    # make mutations for each site
    for site, freq in enumerate(start_freqs):
        # generate the number of mutations for this locus
        n_mutations = int(round(2 * len(spp) * freq, 0))
        # make sure we don't mutate either all or none of the population's
        # homologues, unless called for
        if n_mutations == len(spp) * 2 and freq < 1:
            n_mutations -= 1
        if n_mutations == 0 and freq > 0:
            n_mutations = 1
        #randomly choose and mutate n_mutations homologues from the population 
        np.random.shuffle(homologues)
        homologues_to_mutate = homologues[:n_mutations]
        for ind, homol in homologues_to_mutate:
            # create a mutation in the individual's genome, if this is a
            # non-neutral locus
            if site in spp.gen_arch.nonneut_loci:
                spp[ind].g[np.where(spp.gen_arch.nonneut_loci == site),
                           homol] = 1
            # get the homologue's nodes-table id,
            # then add a row to the mutations table
            node_id = spp[ind]._nodes_tab_ids[homol]
            tables.mutations.add_row(site, node=node_id, parent=-1,
                                     derived_state='1')

    # and then reset the individuals' phenotypes, if needed
    if spp.gen_arch.traits is not None:
        [ind._set_z(spp.gen_arch) for ind in spp.values()]

    return


# method for loading a pickled genomic architecture
def read_pickled_genomic_architecture(filename):
    import cPickle
    with open(filename, 'rb') as f:
        gen_arch = cPickle.load(f)
    return gen_arch
