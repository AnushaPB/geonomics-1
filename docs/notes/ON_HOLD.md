# IDEAS / TO-DO
- create an 'examples' submodule, where I can keep the three examples from the methods paper as well as other ones I build out (e.g. the one for the Biogeo class demo where a barrier arises, or a wind-dispersal one I spin up for Matt Kling)
- add a module for easily creating basic geometric landscapes, then create a landscape type 'geometric' (along with 'defined', 'random', 'nlmpy') that links to it!
- in order to model plants/sessile organisms, I think all I'd need to do is, when movement is not used, have gametes be created, then moved using some movement mechanism (either unimodal or multimodal von mises, or isotropic), where movement can be distinct for male and female gametes, then find gamete-pairs within its radius, then create a new offspring AT the mid-point between the resulting parental gametes. --> note that this uses the same functions that I already have written, just in a different order/for different purposes!
- consider adding ability to use/output tree sequence of spatial pedigree, then building tools to facilitate calculations of emergent properties of interest (e.g. migration rate/gene flow/dispersal flux across specific lines) from the spatial pedigree
- add functionality to model male dispersal of gametes (i.e. sperm/pollen) for modeling of plants, etc
- add any helper functions for manually resetting the landscape rasters of a model after it's created but before it's run?
- add any functions for stipulating 'island'-type landscapes?
- problems with closures, and mutable and/or reassigned attributes could still arise, even though I went through all classes and closures and double-checked for any obvious possible problems, and got rid of any attributes that pointed to big, changing classes (e.g. Landscape.mod, which pointed to Model)
- make "run_default_model" into more of a vignette (which stops and plots things along the way; and possibly which takes different arguments to demonstrate a simple model, a model with selection,
          a model with landscape change, etc)
- assortative mating (based on some trait)
- add module for interactions between populations
- fecundity selection:
        - need to add a params option for fecundity selection
        - should I also then make viability selection optional?
        - already added a fecundity option to draw_n_births, defaulting to 1, but this should instead
          be able to take a 1d array of parents' avg fitness, equal in length to the number of mating
          pairs, in which case each pair's poisson draw will be based on a lambda < (if pair mean 
          fitness is < 1) or = (if = 1) the params-file's lambda value
        - if I do implement this then it is very worth it to make it so that fitness is calculated once
          per turn, perhaps right after movement and before mating, and then memoized (in which case 
          pop.calc_fitness should calculate it, and should call pop.set_fitness to set it, and then 
          pop.get_fitness should get it obviously)
- change Population back from a class that inherits from an OrderedDict to one that inherits from a 
  plain old dict (since dicts are now ordered, as of Py 3.6 [reliable starting Py 3.7])                                                                                                                   
- pick through all the notes in demography.py and decide which are taken care of, which need to stay, which I still need to take care of, etc. 
- update species.plot_pop_growth to account for demographic changes (either because of demographic changes parameterized by the user, or because of
  landscape changes in the K_layer) (use a species.K_sum dict attribute that gets updated with the timestep (as key) of each change in the K raster, as a starting point)
- add a clear little line-break between Layers, Species, Traits, Change events in params files with more than one of them
- write a function for plotting the community (where each pop has a different color) (how about some way for each population to have its fitness
  plotted with colors as usual, but SHAPE to be population indicator?)
- read through and consider rewriting mating.find_mates() (i.e. consider how to re-implement repro_age and sex to speed it up)
- write a Land.plot_land_changes method (akin to Population.plot_demographic_changes)??
- generalize the change fns some more, so that landscape changes can also be made cyclical, random, etc (like pop-dem changes)


 



