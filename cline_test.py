#!/usr/bin/python
# cline_test.py
import geonomics as gnx

import os
import re
import shutil
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import vcf

# set some plotting params
img_dir = ('/home/drew/Desktop/stuff/berk/research/projects/sim/methods_paper/'
                      'img/final/')
ax_fontdict = {'fontsize': 12,
               'name': 'Bitstream Vera Sans'}
ttl_fontdict = {'fontsize': 15,
                'name': 'Bitstream Vera Sans'}

#set the data directory, and delete it if it already exists (so that we don't
#create mutliple, conflicting sets of data files)
data_dir = './GEONOMICS_mod-cline_params'
if os.path.isdir(data_dir):
    shutil.rmtree(data_dir)


mod = gnx.make_model('./geonomics/tests/validation/cline/cline_params.py')
#landscape and community will not be randomized between iterations, so I can
#just extract the non-neutral loci now
nonneutral_loci = mod.comm[0].gen_arch.traits[0].loci
mod.run(verbose = True)

#define a function for the classic tanh cline
def tanh_cline(x, c, w):
    p = 0.5 * (1 + np.tanh(((2*(x-c))/w)))
    return p

#for each iteration
its_dirs = os.listdir(data_dir)
for it_dir in its_dirs:
    #read in the data
    files_dir = os.path.join(data_dir, it_dir, 'spp-spp_0')
    files = os.listdir(files_dir)
    vcf_file = [f for f in files if os.path.splitext(f)[1] == '.vcf']
    assert len(vcf_file) == 1, 'More than one VCF file!'
    vcf_file = vcf_file[0]
    vcf_reader = vcf.Reader(open(os.path.join(files_dir, vcf_file), 'r'))
    csv_file = [f for f in files if re.search('spp_0\.csv$', f)]
    assert len(csv_file) == 1, 'More than one CSV file!'
    csv_file = csv_file[0]
    csv = pd.read_csv(os.path.join(files_dir, csv_file))
    #grab all individuals' genotypes into an n_individs x n_loci array
    genotypes = np.ones((len(csv),
        mod.params.comm.species['spp_0'].gen_arch.L))*99
    try:
        for loc in range(genotypes.shape[1]):
            print('Calculating genotypes for locus %i' % loc)
            rec = next(vcf_reader)
            for n, ind in enumerate(csv['idx']):
                genotype = sum([int(base) for base in rec.genotype(
                    str(ind)).data.GT.split('|')])/2
                genotypes[n, loc] = genotype
    except StopIteration:
        pass
    assert 99 not in genotypes
    #get the non-neutral locus
    nonneut_loc = mod.comm[0].gen_arch.traits[0].loci[0]
    # get environmental values from across the cline,
    # for making cline predictions
    x_to_predict = mod.land[0].rast[0,:].reshape((50,1))
    glms = {}
    tanh_params = {}
    tanh_predictions = {}
    #parse the csv's 'e' column
    csv['env'] = [float(row.split(',')[0].lstrip('[')) for row in csv.e]
    #add each column of the genotypes array as a locus column in the csv
    for loc in range(genotypes.shape[1]):
        csv['loc%i' % loc] = genotypes[:,loc]
        #run a GLM for each locus
        try:
            glm = sm.GLM(csv['env'], csv['loc%i' % loc])#,
                #family = sm.families.Binomial())
            glm_results = glm.fit()
            glms[loc] = glm_results
        except Exception as e:
            print(e)
        # fit a tanh cline to this locus' data
        # (stealing code from here: https://stats.stackexchange.com/
        # questions/66199/maximum-likelihood-curve-model-fitting-in-python)
        tanh_params[loc] = curve_fit(tanh_cline, csv['env'],
                                     csv['loc%i' % loc])
        # then predict y values (i.e. genotypes) across the cline,
        # using the fitted cline
        tanh_predictions[loc] = np.array([tanh_cline(
                            x, *tanh_params[loc][0]) for x in x_to_predict])

    #grab all pvalues
    pvals = {loc:glm.pvalues[0] for loc, glm in glms.items()}
    loc = []
    pval = []
    for l, p, in pvals.items():
        loc.append(l)
        #divide by number of loci, as a simple correction for mutliple-testing
        pval.append(p/genotypes.shape[1])
    res = pd.DataFrame.from_dict({'loc':loc, 'pval':pval})
    #sort ascending, so that most significant loci should appear at top of res
    res = res.sort_values(by = 'pval')

#print non-neutral locus and top 25 test results
print('NON-NEUTRAL LOCUS: %i' % nonneut_loc)
print(res.head(25))

#plot all fitted clines
x_to_plot_for_predicted = np.linspace(0.5,49.5,50)
plt.rcParams['figure.figsize'] = [6,6]
fig1 = plt.figure()
#plt.suptitle(('Adaptation to a cline\n(monogenic trait with phi = s = 0.01,'
#              '2500 timesteps'))
plt.xlabel('Distance along cline')
ax = fig1.add_subplot(111)
#ax.set_title('Fitted tanh clines for all loci\n(non-neutral locus in red)',
#             fontdict=ttl_fontdict)
plt.xlim((0,50))
plt.ylim((0,50))
#ax.set_aspect('equal')
ax.get_xaxis().set_ticks([])
ax.get_yaxis().set_ticks([])
plt.ylabel(('Genotypes predicted by logit GLM\n'
    '(0.0 = 0|0; 0.5 = 0|1; 1.0 = 1|1'), fontdict=ax_fontdict)
plt.imshow(mod.land[0].rast, cmap = 'terrain', interpolation = 'nearest')
ax2 = ax.twinx()
#ax2.set_aspect('equal')
plt.ylim((0,1))
for loc, y_prediction in tanh_predictions.items():
    colors = {True: 'red', False: 'black'}
    linetypes = {True: '-', False: ':'}
    linewidths = {True: 2, False: 1}
    plt.plot(x_to_plot_for_predicted, y_prediction,
        linetypes[loc == nonneut_loc],
        linewidth = linewidths[loc == nonneut_loc],
        color= colors[loc == nonneut_loc])
plt.show()
plt.savefig(os.path.join(img_dir, 'CLINE_fitted_clines.pdf'))

fig2 = plt.figure()
ax3 = fig2.add_subplot(111)
#ax3.set_title(('Final population,\ncolored by phenotype (outer circle) and '
#               'fitness (inner circle)'), fontdict=ttl_fontdict)
mod.plot_fitness(0,0,0, fitness_cbar=False)
plt.show()
plt.savefig(os.path.join(img_dir, 'CLINE_pop_plot.pdf'))

#ANALYSIS IDEAS:

#try to pick out the correct (i.e. non-neutral) loci as outliers in a GLM
#spp = mod.comm[0]
#for locus in range(spp.gen_arch.L):
#    logit_model = sm.GLM(genotypes[:,locus], csv['env'],
#        family=sm.families.Binomial())


#also test hypothesis that mean fitness incrases and plateaus over model time