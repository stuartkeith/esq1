#!/usr/bin/env python

from copy import deepcopy

from esq1 import (Oscillator, LFO, ModulationSource, simple_patch,
                  esq1_patches_to_sysex, sysex_to_esq1_patches)


# read the provided 'tribel.syx' SYSEX file into a list.
tribel = sysex_to_esq1_patches('tribel.syx')

# this file is in 'single program dump' format, so the list will only have one
# patch.
print('"tribel.syx" contains %d patch(es).' % len(tribel))
print('the first patch is named "%s".' % tribel[0].name)

# create a simple patch...
patch = simple_patch()

# ...and name it. the ESQ-1 only supports six letter, uppercase names, so this
# will be truncated.
patch.name = 'Example'

# set some values.
patch.oscillators[0].waveform.value = Oscillator.SQUARE

# randomize all of the second LFO's values.
patch.lfos[1].randomize()

# copy the first oscillator's values into the second oscillator.
patch.oscillators[1] = deepcopy(patch.oscillators[0])
# set some values on the second oscillator.
patch.oscillators[1].waveform.value = Oscillator.FORMT_5
patch.oscillators[1].set_octave(1)
patch.oscillators[1].fine_tune.value = 4

# modulate the second oscillator's frequency with the randomized LFO.
patch.oscillators[1].frequency_modulation_sources[0].value =\
    ModulationSource.LFO_2
patch.oscillators[1].frequency_modulation_amounts[0].value = 4

# set some more values.
patch.envelopes[0].levels[1].value = 42
patch.envelopes[0].times[0].value = 52
patch.envelopes[3].times[0].value = 29

# randomize the frequency of the first LFO.
patch.lfos[0].frequency.randomize()

# set some more values.
patch.lfos[0].humanize.value = True
patch.lfos[0].levels[0].value = 32
patch.lfos[0].waveform.value = LFO.SAW

patch.miscellaneous.frequency.value = 119
patch.miscellaneous.resonance.value = 14
patch.miscellaneous.filter_modulation_sources[0].value = ModulationSource.LFO_1
patch.miscellaneous.filter_modulation_amount[0].value = -15

# write the patch to a SYSEX file.
esq1_patches_to_sysex([patch], 'saved.syx')

# read the SYSEX file into a list.
read_patches = sysex_to_esq1_patches('saved.syx')

# the truncated, uppercase name will be shown.
print('read patch "%s".' % read_patches[0].name)
