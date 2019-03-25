#!/usr/bin/python
# viz.py

'''
##########################################

Module name:          utils.viz


Module contains:
                      - basic visualization functions, to be
                        inherited by classes of model components


Author:               Drew Ellison Hart
Email:                drew.hart@berkeley.edu
Github:               URL
Start date:           06-18-18
Documentation:        URL


##########################################
'''

import numpy as np
# import numpy.random as r
# import random
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
# from collections import Counter as C
# from operator import itemgetter as ig
# from shapely import geometry as g
# from operator import itemgetter
# from operator import attrgetter
# import sys


######################################
# -----------------------------------#
# FUNCTIONS -------------------------#
# -----------------------------------#
######################################

def _choose_cmap(lyr_num):
    cols = {0: 'coolwarm',
            1: 'BrBG_r',
            2: 'PRGn',
            3: 'PiYG_r',
            4: 'PuOr_r',
            }
    col = cols[lyr_num % len(cols)]
    return col


def _plot_rasters(land, lyr_num=None, cbar=True,
                  im_interp_method='nearest', cmap=None, plt_lims=None,
                  vmin=None, vmax=None, lyr_name=None, ticks=None, mask_rast=None):
    # if a figure is already open, force colorbar to False
    if plt.get_fignums() and plt.gcf().get_axes():
        cbar = False

    # create a list to hold all colobar ticks (and their min/max vals on the 0-1
    # raster), and a list to hold all colorbar labels, if cbar == True
    lyr_cbar_ticks = []
    lyr_cbar_labs = []
    # if just a numpy.ndarray or a Layer (not a Landscape object) is
    # provided, or if just a single raster is desired, grab
    # the raster into a list
    if isinstance(land, np.ndarray):
        rasters = [land]
        if lyr_name is not None:
            lyr_names = [lyr_name]
        else:
            lyr_names = ['n/a']
        if lyr_num is not None:
            cmaps = [_choose_cmap(lyr_num)]
        else:
            cmaps = [_choose_cmap(0)]
        lyr_type = ''
    # elif isinstance(land, gnx.landscape.Layer):
    elif 'Layer' in str(type(land)):
        if land.type == 'file':
            rasters = [land._get_rast_in_native_units()]
        else:
            rasters = [land.rast]
        lyr_names = [land.name]
        cmaps = [_choose_cmap(land.idx)]
        lyr_type = land.type
        if cbar:
            lyr_cbar_ticks.append(land._get_cbar_ticks_and_minmax_scaled_vals(
                                                                             ))
            lyr_cbar_labs.append(land.units)
    # elif isinstance(land, gnx.landscape.Landscape):
    elif 'Landscape' in str(type(land)):
        if lyr_num is not None:
            if land[lyr_num].type == 'file':
                rasters = [land[lyr_num]._get_rast_in_native_units()]
            else:
                rasters = [land[lyr_num].rast]
            lyr_names = [land[lyr_num].name]
            cmaps = [_choose_cmap(lyr_num)]
            lyr_cbar_ticks.append(
                        land[lyr_num]._get_cbar_ticks_and_minmax_scaled_vals())
            lyr_cbar_labs.append(land[lyr_num].units)
        # else just create a list of all rasters
        else:
            rasters = [lyr.rast if (
                lyr.type != 'file') else lyr._get_rast_in_native_units(
                                                    ) for lyr in land.values()]
            lyr_names = [lyr.name for lyr in land.values()]
            cmaps = [_choose_cmap(lyr.idx) for lyr in land.values()]
            [lyr_cbar_ticks.append(
                land[lyr_num]._get_cbar_ticks_and_minmax_scaled_vals(
                                                    )) for lyr_num in [*land]]
            [lyr_cbar_labs.append(land[lyr_num].units) for lyr_num in [*land]]
        # else just create a list of all rasters
        lyr_types = [lyr.type for lyr in land.values()]
        lyr_type = 'file' * ('file' in lyr_types)

    # plot all with the same cmap, if the cmap argument was provided
    if isinstance(cmap, str):
        # get the requested cmap
        cmap = getattr(plt.cm, cmap)
        cmaps = [cmap] * len(rasters)

    # mask all arrays, and set cmaps' bad values to gray,
    # if mask_rast is provided
    if mask_rast is not None:
        rasters = [np.ma.masked_where(np.isnan(mask_rast),
                                      rast) for rast in rasters]
        cmaps = [getattr(plt.cm, cm) for cm in cmaps]
        [cm.set_bad('#8C8C8C') for cm in cmaps]

    # create alphas list
    alphas = [1] + [0.5] * (len(rasters)-1)
    # plot all the rasters...
    for n in range(len(rasters)):
        # pull out the zoomed raster, if requested
        # if zoom is not None:
        #    min_i, max_i = zoom[0]
        #    min_j, max_j = zoom[1]
        #    rasters[n] = np.array([row[
                    # min_j:max_j] for row in rasters[n][min_i:max_i]])
        plt.imshow(rasters[n], interpolation=im_interp_method, cmap=cmaps[n],
                   vmin=vmin, vmax=vmax, alpha=alphas[n])
        if ((lyr_type != 'file' and not ticks) or
           (lyr_type == 'file' and ticks is False)):
            plt.xticks([])
            plt.yticks([])
        else:
            # add geo-coordinate ticks, if this is a raster from a file
            if lyr_type == 'file':
                (x_ticks, x_tick_labs,
                 y_ticks, y_tick_labs) = land._get_coord_ticks()
                # format at ticklabels to the same decimal place
                float_fmt = ('%0.' + str(max([len(str(n).split(
                        '.')[1]) for n in x_tick_labs + y_tick_labs])) + 'f')
                x_tick_labs = [float_fmt % n for n in x_tick_labs]
                y_tick_labs = [float_fmt % n for n in y_tick_labs]
                plt.xticks(x_ticks, x_tick_labs, rotation=90)
                plt.yticks(y_ticks, y_tick_labs)
                ax = plt.gca()
                plt.xlabel('lon')
                plt.ylabel('lat')
        if plt_lims is not None:
            plt.xlim(plt_lims[0])
            plt.ylim(plt_lims[1])
        # and their colorbars, if requested
        if cbar:
            if len(lyr_cbar_ticks) == 0:
                cbar_max_bound = max(rasters[n].max(),
                    [1 if vmax is None else vmax][0])
                cbar_bounds = np.linspace(0, cbar_max_bound, 51)
                cbar = plt.colorbar(boundaries=cbar_bounds)
            else:
                cbar = plt.colorbar(ticks=np.linspace(lyr_cbar_ticks[n][1],
                                                      lyr_cbar_ticks[n][2], 5))
                cbar.ax.set_yticklabels(lyr_cbar_ticks[n][0])
                cbar.set_label(lyr_cbar_labs[n], rotation=270,
                                     labelpad=15, y=0.5)
            cbar.ax.set_title("layer: %s" % lyr_names[n])
            title = cbar.ax.title
            font = mpl.font_manager.FontProperties(family='sans-serif',
                                                   style='normal', size=10)
            title.set_font_properties(font)


def _plot_points(points, lyr_num=None, color='black',
            edge_color='face', text_color='black', linewidth=0.5,
            pt_cmap=None, size=25, text_size=9, alpha=False, text=None,
            plt_lims=None, vmin=None, vmax=None):
    #get the x and y coordinates from the points (and subtract 0.5
    #to line the points up with the plt.imshow() grid of a
    #landscape raster; imshow plots each pixel centered on its 
    #index, but the points then plot on those indices, so wind up
    #shifted +0.5 on each axis
    x = points[:, 0] - 0.5
    y = points[:, 1] - 0.5
    #handle the alpha value as necessary
    if alpha == True and type(alpha) == bool:
        alpha = 0.6
    elif alpha != False and type(alpha) in (int, float):
        assert alpha >= 0 and alpha <= 1, ("Values of 'alpha' must be between "
            "0 and 1.")
        alpha = alpha
    else:
        alpha = 1.0

    #plot the points, as stipulated by arguments
    if pt_cmap is not None:
        if pt_cmap == 'terrain':
            colors = ['#3C22B4', '#80A6FF', '#FFFFFF']
            # colors to match matplotlib colormap 'terrain' palette
            #extremes, but with hybrid a mix of the extremes
            # rather than the yellow at the middle of the palette,
            #for nicer viewing
            cmap = LinearSegmentedColormap.from_list('my_cmap', colors, N=50)
        elif type(pt_cmap) == str:
            cmap = getattr(plt.cm, pt_cmap)
        elif isinstance(pt_cmap, LinearSegmentedColormap):
            cmap = pt_cmap
        plt.scatter(x, y, s=size, c=color, cmap=cmap, linewidth=linewidth,
                edgecolor=edge_color, alpha=alpha, vmin = vmin, vmax = vmax)
    else:
        plt.scatter(x, y, s=size, c=color, linewidth=linewidth,
                edgecolor=edge_color, alpha=alpha, vmin = vmin, vmax = vmax)

    #add text, if requested
    if text is not None:
        plot_text = []
        for n,t in enumerate(text):
            if plt_lims is not None:
                if (plt_lims[0][0] <= x[n] <= plt_lims[0][1]
                    and plt_lims[1][0] <= y[n] <= plt_lims[1][1]):
                    plot_text.append((x[n], y[n], t))
            else:
                plot_text.append((x[n], y[n], t))
        [plt.text(*item, color=text_color, size=text_size,
                                        alpha=alpha) for item in plot_text];

    if (plt_lims is not None
        and len(plt_lims) == 2
        and [len(item) for item in plt_lims] == [2,2]):
        plt.xlim(plt_lims[0])
        plt.ylim(plt_lims[1])
    else:
        print(("plt_lims appears not to be a valid argument "
               "(i.e. a 2-tuple of 2-tuples)"))


def _get_lyr_plt_lims(land):
    #NOTE: these are set up so that 0,0 is in the upper-left corner
    xlim = (-1, land.dim[1])
    ylim = (land.dim[0], -1)
    lims = (xlim, ylim)
    return(lims)


def _get_zoom_plt_lims(x, y, zoom_width):
    #get zoom-half-width
    zhw = zoom_width/2
    xlim = (x- zhw, x+zhw)
    ylim = (y+ zhw, y-zhw)
    lims = (xlim, ylim)
    return(lims)


def _get_plt_lims(land=None, x=None, y=None, zoom_width=None):
    if zoom_width is not None and x is not None and y is not None:
        plt_lims = _get_zoom_plt_lims(x, y, zoom_width)
    else:
        plt_lims = _get_lyr_plt_lims(land)
    return(plt_lims)


def _make_fitness_cmap_and_cbar_maker(min_val, max_val = 1,
                        cmap = 'gray', max_cmap_len = 5, trt_num = None):
    # define the colormap
    cmap = getattr(plt.cm, cmap)
    #extract all the colors into a list
    cmap_list = [cmap(i) for i in range(cmap.N)]
    #create new list, with the majority of the color range expressed for
    #the values between 1 and the min_val, then the remainder stretched
    #out between min_val and 0
    #top = np.int64(np.linspace(0,len(cmap_list)*0.15,max_cmap_len*0.8))
    #bot = np.int64(np.linspace(1+(len(cmap_list)*0.15),
                                    #len(cmap_list)-1, max_cmap_len*0.2))
    new_cmap_inds = np.int64(np.linspace(0, len(cmap_list), max_cmap_len))
    #new_cmap_inds = list(np.hstack((top,bot)))
    new_cmap_inds = list(set(new_cmap_inds))
    new_cmap_list = [col for n,col in enumerate(
                                            cmap_list) if n in new_cmap_inds]
    # create the new map
    #cmap = cmap.from_list('Custom cmap', new_cmap_list, len(cmap_list))
    # define the bin-boundaries 
    #lower_bounds = np.linspace(0,min_val,round((2*cmap.N/3)+1))[:-1]
    #upper_bounds = np.linspace(min_val, max_val,round(cmap.N/3))
    #bounds = np.hstack((lower_bounds, upper_bounds))
    bounds = np.linspace(min_val, max_val, cmap.N)
    assert len(bounds) == cmap.N
    #normalize the colormap
    #norm = mpl.colors.BoundaryNorm(bounds, cmap.N)
    #create ticks for the colorbar
    ticks_inds = np.int64(np.linspace(0, len(bounds)-1, 10))
    ticks = list(bounds[ticks_inds])
    tick_closest_to_min_val = min([abs(tick-min_val) for tick in ticks])
    ind_closest = [n for n,tick in enumerate(ticks) if abs(
                                tick-min_val) == tick_closest_to_min_val][0]
    ticks[ind_closest] = min_val
    ticks = sorted(ticks)
    ticks = [round(tick, 2) for tick in ticks]
    if trt_num is None:
        tick_labs = [(' '*10 + 'min. fit. =\n' + ' ' * 10 + ('$1-\prod_'
                      '{trait=1}^{t} \phi_{t} \prod_{del.mut.=1}'
                      '^{d} \phi_{d}$\n')) if n == ind_closest else str(
                        tick) for n, tick in enumerate(ticks)]
    else:
        tick_labs = [(' ' * 10 + 'min. fit. =\n' + ' ' * 10 + ('$1-\phi_'
                    '{trait=%i}$\n')) % (trt_num) if n == ind_closest else str(
                        tick) for n, tick in enumerate(ticks)]
    #create a function for making the colorbar, to be shipped out to and
    #called within species.Species.plot_fitness()
    def make_cbar(ax):
        cbar = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
            spacing='proportional', ticks=ticks, boundaries=bounds,
            format='%1i')
        cbar.set_ticks(ticks)
        cbar.set_ticklabels(tick_labs)
    return(cmap, make_cbar)

def _make_fitness_cbar(make_cbar_fn, min_fit):
    fig = plt.gcf()
    ax1 = plt.gca()
    ax2 = fig.add_axes([0.84, 0.106, 0.02, 0.7774])
    make_cbar_fn(ax2)
    #ax2.plot([0,1],[round(min_fit,2)]*2, c = 'black', lw = 1)
    ax2.set_title('fitness')
    title = ax2.title
    font = mpl.font_manager.FontProperties(family='sans-serif',
                                                style='normal', size=10)
    title.set_font_properties(font)
