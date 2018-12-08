--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

# CODE CHANGES (ranked in priority from 1 (least) to 5):

        6 decide whether or not to add a switch determining whether movement surafces are calculated up front, before model is run, or are calculated during the model run (b/c of the memory/compute time ttrade-off)

        5 ASK IAN: draws of effect sizes for trait mutations should actually come froma strictly positive distribution and then multiplied by a random -1 or +1 (and that distr
          should be able to have its draws fixed at mu when sigma == 0) ---> THEN UPDATE THE DOCS!

        5 not at all sure that a gamma is the right distribution for drawing the deleterious mutations' effects

        5 consider adding a generalized function for making a distribution's draw be a function of phenotype, then apply that to movement, dispersal, fecundity, etc?

        5 consider adding ability for life-history parameters to be determined by a trait's phenotype

        5 touch up all comments (only keep necessary, non-obvious comments; and maybe separate each comment-topped section by a single line break?)

        5 add type annotation to all functions

        5 write lots of checks on the types of all the data in the params file, with informative errors

        2 finalize nice string representations for all classes


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

# DOCS CHANGES:
- make clearer that "dispersal" means "offspring" and is differentiated from "movement"
- make clear that a Species' K will change because of landscape changes in the Layer it's based on, or because of parameterized changes, OR BOTH (BUT BOTH WILL BE A MESS,
  so user should either include a Layer in the Landscape that won't change, just to start off a Pop's K raster, then tweak that K raster with demo changes, OR plan Landscape
  changes knowing that the Species' K raster will be affected, but NOT BOTH!)
- write docstrings for remaining classes
- add images
- explain dist-parameters' name format somewhere
- put together some examples (from simplest upward), in a Cookbook section of the docs
      - and use one of them as an off-the-bat example that can serve as a vehicle for continuing to discuss all the additional possible parts of a model?
- add to the Intro (or somewhere near there) in the docs a list of the sorts of questions the package could answer???
- rework Intro based on feedback from lab meeting, and on Nick's notes (see his email)
- add mention of "geonomics" the philosophical movememnt (and disambiguation)
- add a graphical representation of the model components to the docs (Species composed of Individuals, optionally having genomes, optionally subtending phenotypes, and living on a Landscape with multiple Layers)


--------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------

# FINAL STEPS:

- write popgen-based theoretical validations-tests

- add docstrings to all functions (look up current standards first)

- add an ./ex directory, which will contain a Yosemite simulation

- finalize pkg structure

- prep for PyPi release

- script and run sims for the first study
        - genomic conflict and adaptation to climate change (2 traits, 2 environmental gradients, 1 static, 1 dynamic)
        - LOOK INTO YOSEMITE CHIPMUNKS

- put together analyses and manuscript

- send out for publication