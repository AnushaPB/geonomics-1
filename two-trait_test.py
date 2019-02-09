#!/usr/bin/python
# two-trait_test.py

import geonomics as gnx
import matplotlib.pyplot as plt

# RUN THE MODEL WITHOUT LINKAGE
# make the model
mod = gnx.make_model(('./geonomics/tests/validation/two-trait/'
                      'two-trait_params.py'))
# run it
mod.run(verbose=True)
# plot the resulting species on top of each layer
fig = plt.figure()
ax1 = fig.add_subplot(121)
mod.plot_phenotype(0, 0, 0)
ax2 = fig.add_subplot(122)
mod.plot_phenotype(0, 1, 1)
ax1.set_title('trait_0')
ax2.set_title('trait_1')
plt.suptitle(('Resulting phenotypes for a species undergoing simultaneous '
              'selection on two, 10-locus traits\n'
              'unlinked loci (recombination rates $=0.5$)\n'
              '(each trait\'s phenotype '
              'plotted on top of the landscape layer that serve as the '
              'trait\'s selective force)\n'
              '($\phi_{trait_0}=\phi_{trait_1}=0.01$; 1000 timesteps)'))


# RUN THE MODEL WITH LINKAGE
# read in the parameters and change the recombination rate to 0.05
params = gnx.read_parameters_file(('./geonomics/tests/validation/two-trait/'
                                   'two-trait_params.py'))
params['comm']['species']['spp_0']['gen_arch']['r_distr_alpha'] = 0.05
params['comm']['species']['spp_0']['gen_arch']['r_distr_beta'] = 10000
# make the model
mod = gnx.make_model(params)
# run it
mod.run(verbose=True)
# plot the resulting species on top of each layer
fig = plt.figure()
ax1 = fig.add_subplot(121)
mod.plot_phenotype(0, 0, 0)
ax2 = fig.add_subplot(122)
mod.plot_phenotype(0, 1, 1)
ax1.set_title('trait_0')
ax2.set_title('trait_1')
plt.suptitle(('Resulting phenotypes for a species undergoing simultaneous '
              'selection on two, 10-locus traits\n'
              'linked loci (recombination rates ~= 0.05)\n'
              '(each trait\'s phenotype '
              'plotted on top of the landscape layer that serve as the '
              'trait\'s selective force)\n'
              '($\phi_{trait_0}=\phi_{trait_1}=0.01$; 1000 timesteps)'))
