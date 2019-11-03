esq1
====

esq1 is a Python module used to generate and edit patches for the Ensoniq ESQ-1
synthesizer. The patches can be read from and written to SYSEX files,
either in *single program dump* mode (one patch) or *all program dump* mode
(40 patches).

Each parameter, section (an envelope, LFO, etc), or the entire patch can be
randomised.

See `example.py` for usage.

This module was inspired by [Noah Vawter's 'Ensoniq PCB Code and Data
Structure C code'](http://www.gweep.net/~shifty/music/esq.html), which gave me
a far better idea of how the PCB data was stored than the ESQ-1 manual.

Thanks to [Rainer Buchty's Section Ensoniq](http://www.buchty.net/ensoniq/) for
hosting the ESQ-1 manual.


Note
----

The ESQ-1 manual is incorrect regarding the order of bytes in the LFO section.

The manual specifies (in Appendix 6, 'Program Control Block Structure', under
'Low Frequency Oscillators'):

    1   2   3   4   5   6   7   8
    M1  M0  LFO Frequency.........
    M3  M2  Level 1...............
    W1  W0  Level 2...............

It is actually:

    1   2   3   4   5   6   7   8
    W1  W0  LFO Frequency.........
    M1  M0  Level 1...............
    M3  M2  Level 2...............
