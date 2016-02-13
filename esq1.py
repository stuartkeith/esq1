from random import randint


def simple_patch():
    """Return a one-oscillator patch."""
    patch = ESQ1Patch()

    patch.oscillators[0].dca_enable.set_maximum()
    patch.oscillators[0].dca_level.set_maximum()

    patch.miscellaneous.frequency.set_maximum()
    patch.miscellaneous.dca4_modulation_amount.set_maximum()

    patch.envelopes[3].levels[0].set_maximum()
    patch.envelopes[3].levels[2].set_maximum()

    return patch


class Parameter(object):
    """A patch parameter.

    Prevents the user from specifying an out-of-range value and allows the
    parameter to be set to its minimum, maximum, default, or random value.

    Attributes:

    minimum -- the minimum value. Must be <= maximum.

    maximum -- the maximum value. Must be >= minimum.

    default -- the default value (if None, set to minimum). Must be >= minimum
        and <= maximum.

    value -- the current value.
    """

    def __init__(self, minimum, maximum, default=None):
        if minimum > maximum:
            raise ValueError('Minimum (%d) must be less than maximum (%d).' %
                             (minimum, maximum))

        self.minimum = minimum
        self.maximum = maximum

        if default is not None:
            self.default = default
        else:
            self.default = self.minimum

        self.reset()

    def __eq__(self, other):
        return self.value == other.value

    def __ne__(self, other):
        return self.value != other.value

    def __repr__(self):
        return str(self.value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        """Set the value property.

        value -- the new value. Must be >= minimum and <= maximum.
        """
        if value < self.minimum:
            raise ValueError('Value (%d) is less than minimum (%d).' %
                             (value, self.minimum))
        elif value > self.maximum:
            raise ValueError('Value (%d) is more than maximum (%d).' %
                             (value, self.maximum))
        else:
            self._value = value

    def randomize(self):
        """Randomize the value property.

        Sets the value to a random number >= minimum and <= maximum.
        """
        self.value = randint(self.minimum, self.maximum)

    def reset(self):
        """Reset the value property to its default value."""
        self.value = self.default

    def set_minimum(self):
        self.value = self.minimum

    def set_maximum(self):
        self.value = self.maximum


class ModulationSource(Parameter):
    """A parameter representing a modulation source.

    The value must be one of the class properties specified below.
    Defaults to OFF.
    """

    LFO_1 = 0
    LFO_2 = 1
    LFO_3 = 2
    ENV_1 = 3
    ENV_2 = 4
    ENV_3 = 5
    ENV_4 = 6
    VEL = 7  # linear keyboard velocity.
    VEL_2 = 8  # non-linear keyboard velocity.
    KYBD = 9  # position of note on keyboard (partial range, 0 to 127).
    KYBD_2 = 10  # position of note on keyboard, -63 to 63.
    WHEEL = 11
    PEDAL = 12
    XCTRL = 13
    PRESS = 14  # aftertouch (not sent by ESQ-1!).
    OFF = 15

    def __init__(self):
        super(ModulationSource, self).__init__(self.LFO_1, self.OFF, self.OFF)


class ModulationAmount(Parameter):
    """A parameter representing a modulation amount."""

    def __init__(self):
        super(ModulationAmount, self).__init__(-63, 63, 0)


class Boolean(Parameter):
    """A parameter representing a boolean."""

    def __init__(self):
        super(Boolean, self).__init__(False, True)


def display_to_pcb(value):
    """Convert the value as shown on the ESQ-1's display (-63 to 63) to the
    value stored in the bytearray (65 to 127, 0 to 63).
    """
    if value < -63:
        raise ValueError('Display value (%d) must be >= -63.' % value)
    elif value < 0:
        return 128 + value
    elif value <= 63:
        return value
    else:
        raise ValueError('Display value (%d) must be <= -63.' % value)


def pcb_to_display(value):
    """Convert the value as stored in the PCB (65 to 127, 0 to 63) to the
    value shown on the ESQ-1's display (-63 to 63).
    """
    if value < 0:
        raise ValueError('PCB value (%d) must be >= 0.' % value)
    elif value < 64:
        return value
    if value == 64:
        raise ValueError('PCB value must not be 64.')
    elif value <= 127:
        return -128 + value
    else:
        raise ValueError('PCB value (%d) must be <= 127.' % value)


class ParameterCollection(object):
    """A collection of parameters, grouped for easy randomization
    and comparison.

    A comparison between two instances will compare each instance's parameters
    when determining if they are equal.
    """
    def randomize(self):
        """Walk through each attribute and randomize."""
        for attribute in self.__dict__:
            attr = getattr(self, attribute)

            if getattr(attr, "randomize", None):
                attr.randomize()
            elif type(attr) is list:
                for item in attr:
                    item.randomize()

    def __eq__(self, other):
        """Comparison operator for one == two"""
        for attribute in self.__dict__:
            if getattr(self, attribute) != getattr(other, attribute):
                return False

        return True

    def __ne__(self, other):
        """Comparison operator for one != two"""
        for attribute in self.__dict__:
            if getattr(self, attribute) != getattr(other, attribute):
                return True

        return False


class Envelope(ParameterCollection):
    """The parameters for one envelope. There are four envelopes in each ESQ-1
    patch.

    Attributes:

    levels -- a list of each level in the envelope. Three in total.

    times -- a list of each time in the envelope. Four in total.

    velocity_level -- the amount by which the envelope's levels will be lowered
      by the velocity of a note.

    velocity_attack_control -- the amount by which the envelope's time[0] is
      decreased by the velocity of a note.

    keyboard_decay_scaling -- the amount by which the envelope's time[1] and
      time[2] are decreased by the height of a note.
    """
    def __init__(self):
        self.levels = [ModulationAmount() for i in range(3)]
        self.times = [Parameter(0, 63) for i in range(4)]
        self.velocity_level = Parameter(0, 63)
        self.velocity_attack_control = Parameter(0, 63)
        self.keyboard_decay_scaling = Parameter(0, 63)

    def serialize(self):
        """Serialize the class's attributes into a bytearray."""
        bytes = bytearray()

        for level in self.levels:
            bytes.append(display_to_pcb(level.value) << 1)

        for time in self.times:
            bytes.append(time.value)

        bytes.append(self.velocity_level.value << 2)
        bytes.append(self.velocity_attack_control.value)
        bytes.append(self.keyboard_decay_scaling.value)

        return bytes

    def deserialize(self, bytes):
        """Deserialize the bytearray into the class's attributes."""
        for level in self.levels:
            level.value = pcb_to_display(next(bytes) >> 1)

        for time in self.times:
            time.value = next(bytes)

        self.velocity_level.value = next(bytes) >> 2
        self.velocity_attack_control.value = next(bytes)
        self.keyboard_decay_scaling.value = next(bytes)


class LFO(ParameterCollection):
    """The parameters for one LFO. There are three LFOs in each ESQ-1 patch.

    Attributes:

    levels -- a list of each level in the LFO. Two in total.
      levels[0] is the level when the key is struck.
      levels[1] is the level reached at the end of the ramp defined by the
        delay (see below).

    frequency -- the frequency of the LFO.

    reset -- enable/disable whether the LFO returns to the beginning of its
      cycle each time a new key is struck.

    human -- enable/disable random element being introduced to the frequency.

    waveform -- either TRIANGLE, SAW, SQR, or NOISE.

    delay -- determines the rate at which the LFO's amplitude will go from
      level[0] to level[1]. This is a rate of change, not a fixed time.
      A value of 0 causes the LFO to remain at level[0].

    modulation_source -- modulation source for LFO depth.
    """

    TRIANGLE = 0
    SAW = 1
    SQR = 2
    NOISE = 3

    def __init__(self):
        self.levels = [Parameter(0, 63), Parameter(0, 63)]
        self.frequency = Parameter(0, 63)
        self.reset = Boolean()
        self.humanize = Boolean()
        self.waveform = Parameter(self.TRIANGLE, self.NOISE)
        self.delay = Parameter(0, 63)
        self.modulation_source = ModulationSource()

    def serialize(self):
        """Serialize the class's attributes into a bytearray."""
        bytes = bytearray()

        waveform = (self.waveform.value & 0b00000011) << 6
        modulation_source_0 = (self.modulation_source.value & 0b00000011) << 6
        modulation_source_1 = (self.modulation_source.value & 0b00001100) << 4
        reset = (self.reset.value & 0b00000001) << 7
        humanize = (self.humanize.value & 0b00000001) << 6

        bytes.append(waveform + self.frequency.value)
        bytes.append(modulation_source_1 + self.levels[0].value)
        bytes.append(modulation_source_0 + self.levels[1].value)
        bytes.append(reset + humanize + self.delay.value)

        return bytes

    def deserialize(self, bytes):
        """Deserialize the bytearray into the class's attributes."""
        byte = next(bytes)

        self.waveform.value = (byte & 0b11000000) >> 6
        self.frequency.value = byte & 0b00111111

        byte = next(bytes)

        modulation_source_0 = (byte & 0b11000000) >> 6
        self.levels[0].value = byte & 0b00111111

        byte = next(bytes)

        modulation_source_1 = (byte & 0b11000000) >> 6
        self.levels[1].value = byte & 0b00111111

        self.modulation_source.value = modulation_source_1 +\
            (modulation_source_0 << 2)

        byte = next(bytes)

        self.reset.value = (byte & 0b10000000) >> 7
        self.humanize.value = (byte & 0b01000000) >> 6
        self.delay.value = byte & 0b00111111


class Oscillator(ParameterCollection):
    """The parameters for one oscillator. There are three oscillators in each
    ESQ-1 patch.

    Attributes:

    semitone -- the semitone. Can also be modified using set_octave().

    fine_tune -- the finetune/detune.

    frequency_modulation_sources -- a list containing the two frequency
      modulation sources.

    frequency_modulation_amounts -- a list containing the two frequency
      modulation amounts.

    waveform -- the waveform of the oscillator. SAW, BELL, etc. See class
      properties below.

    dca_enable -- enable/disable this oscillator.

    dca_level -- the amplitude level of this oscillator.

    dca_modulation_sources -- a list containing the two amplitude modulation
      sources.

    dca_modulation_amounts -- a list containing the two amplitude modulation
      amounts.
    """

    SAW = 0
    BELL = 1
    SINE = 2
    SQUARE = 3
    PULSE = 4
    NOISE_1 = 5
    NOISE_2 = 6
    NOISE_3 = 7
    BASS = 8
    PIANO = 9
    EL_PNO = 10
    VOICE_1 = 11
    VOICE_2 = 12
    VOICE_3 = 13
    KICK = 14
    REED = 15
    ORGAN = 16
    SYNTH_1 = 17
    SYNTH_2 = 18
    SYNTH_3 = 19
    FORMT_1 = 20
    FORMT_2 = 21
    FORMT_3 = 22
    FORMT_4 = 23
    FORMT_5 = 24
    PULSE2 = 25
    SQR_2 = 26
    FOUR_OCTS = 27
    PRIME = 28
    BASS_2 = 29
    E_PNO2 = 30
    OCTAVE = 31
    OCT_5 = 32

    def __init__(self):
        self.semitone = Parameter(0, 96, 36)
        self.fine_tune = Parameter(0, 31)

        self.frequency_modulation_sources = [ModulationSource(),
                                             ModulationSource()]

        self.frequency_modulation_amounts = [ModulationAmount(),
                                             ModulationAmount()]

        self.waveform = Parameter(self.SAW, self.OCT_5)
        self.dca_enable = Boolean()
        self.dca_level = Parameter(0, 63)
        self.dca_modulation_sources = [ModulationSource(), ModulationSource()]
        self.dca_modulation_amounts = [ModulationAmount(), ModulationAmount()]

    def set_octave(self, value):
        """Set the semitone value using an octave value (-3 to 5)."""
        self.semitone.value = (value + 3) * 12

    def serialize(self):
        """Serialize the class's attributes into a bytearray."""
        bytes = bytearray()

        fine_tune = self.fine_tune.value << 3

        frequency_modulation_sources =\
            (self.frequency_modulation_sources[1].value << 4) +\
            self.frequency_modulation_sources[0].value

        frequency_modulation_amounts = [
            display_to_pcb(self.frequency_modulation_amounts[0].value) << 1,
            display_to_pcb(self.frequency_modulation_amounts[1].value) << 1
        ]

        dca_enable = (self.dca_enable.value & 0b00000001) << 7
        dca_level = self.dca_level.value << 1

        dca_modulation_sources =\
            (self.dca_modulation_sources[1].value << 4) +\
            self.dca_modulation_sources[0].value

        dca_modulation_amounts = [
            display_to_pcb(self.dca_modulation_amounts[0].value) << 1,
            display_to_pcb(self.dca_modulation_amounts[1].value) << 1
        ]

        bytes.append(self.semitone.value)
        bytes.append(fine_tune)
        bytes.append(frequency_modulation_sources)
        bytes.append(frequency_modulation_amounts[0])
        bytes.append(frequency_modulation_amounts[1])
        bytes.append(self.waveform.value)
        bytes.append(dca_enable + dca_level)
        bytes.append(dca_modulation_sources)
        bytes.append(dca_modulation_amounts[0])
        bytes.append(dca_modulation_amounts[1])

        return bytes

    def deserialize(self, bytes):
        """Deserialize the bytearray into the class's attributes."""
        self.semitone.value = next(bytes)
        self.fine_tune.value = next(bytes) >> 3

        byte = next(bytes)

        self.frequency_modulation_sources[1].value = byte >> 4
        self.frequency_modulation_sources[0].value = byte & 0b00001111

        self.frequency_modulation_amounts[0].value = pcb_to_display(
            next(bytes) >> 1)

        self.frequency_modulation_amounts[1].value = pcb_to_display(
            next(bytes) >> 1)

        self.waveform.value = next(bytes)

        byte = next(bytes)

        self.dca_enable.value = (byte & 0b10000000) >> 7
        self.dca_level.value = (byte & 0b01111111) >> 1

        byte = next(bytes)

        self.dca_modulation_sources[1].value = byte >> 4
        self.dca_modulation_sources[0].value = byte & 0b00001111

        self.dca_modulation_amounts[0].value = pcb_to_display(
            next(bytes) >> 1)
        self.dca_modulation_amounts[1].value = pcb_to_display(
            next(bytes) >> 1)


class Miscellaneous(ParameterCollection):
    """The miscellaneous section of the ESQ-1 patch.

    Attributes:

    sync -- enable/disable syncing of phase between oscillator 2 and
      oscillator 1; when oscillator 1 finishes one complete cycle of its
      waveform and begins another, oscillator 2 will reset too.

    am -- enable/disable amplitude of oscillator 1 modulating amplitude of
      oscillator 2.

    mono -- enable/disable monophonic mode.

    glide -- set glide/portamento.

    reset_voice -- enable/disable 'voice stealing' when same note is played
      twice.

    reset_envelope -- when True, all envelopes will restart when a key is
      re-struck. When False, each envelope will start its cycle at the present
      level.

    reset_oscillator -- enable/disable the oscillators restarting when a key
      is struck.

    cycle -- when True, all envelopes are run through their full cycles,
      ignoring the key being released.

    pan -- pan.

    pan_modulation_source -- pan modulation source.

    pan_modulation_amount -- pan modulation amount.

    dca4_modulation_amount -- the amount dca 4 is modulated by envelope 4.

    frequency -- filter cut-off frequency.

    resonance -- filter resonance.

    filter_modulation_sources -- a list containing the two
      filter modulation sources.

    filter_modulation_amounts -- a list containing the two
      filter modulation amounts.

    filter_keyboard_tracking -- the amount the location a note on the keyboard
      modulates the the filter cut-off frequency.

    The following attributes deal with splitting/layering programs:
      split_direction
      split_point
      layer_flag
      layer_program
      split_flag
      split_program
      split_layer_flag
      split_layer_program
    """

    def __init__(self):
        self.sync = Boolean()
        self.am = Boolean()
        self.mono = Boolean()
        self.glide = Parameter(0, 63)
        self.reset_voice = Boolean()
        self.reset_envelope = Boolean()
        self.reset_oscillator = Boolean()
        self.cycle = Boolean()
        self.pan = Parameter(0, 15, 8)
        self.pan_modulation_source = ModulationSource()
        self.pan_modulation_amount = ModulationAmount()
        self.dca4_modulation_amount = Parameter(0, 63)
        self.frequency = Parameter(0, 127)
        self.resonance = Parameter(0, 31)

        self.filter_modulation_sources = [ModulationSource(),
                                          ModulationSource()]

        self.filter_modulation_amount = [ModulationAmount(),
                                         ModulationAmount()]

        self.filter_keyboard_tracking = Parameter(0, 63)
        self.split_direction = Boolean()
        self.split_point = Parameter(0, 108)
        self.layer_flag = Boolean()
        self.layer_program = Parameter(0, 39)
        self.split_flag = Boolean()
        self.split_program = Parameter(0, 39)
        self.split_layer_flag = Boolean()
        self.split_layer_program = Parameter(0, 39)

    def serialize(self):
        """Serialize the class's attributes into a bytearray."""
        bytes = bytearray()

        am = (self.am.value & 0b00000001) << 7
        dca4_modulation_amount = self.dca4_modulation_amount.value << 1
        sync = (self.sync.value & 0b00000001) << 7

        filter_modulation_sources = [
            self.filter_modulation_sources[0].value,
            self.filter_modulation_sources[1].value << 4
        ]

        reset_voice = (self.reset_voice.value & 0b00000001) << 7
        mono = (self.mono.value & 0x01) << 7
        reset_envelope = (self.reset_envelope.value & 0b00000001) << 7
        filter_keyboard_tracking = self.filter_keyboard_tracking.value << 1
        reset_oscillator = (self.reset_oscillator.value & 0b00000001) << 7
        split_direction = (self.split_direction.value & 0b00000001) << 7
        layer_flag = (self.layer_flag.value & 0b00000001) << 7
        split_flag = (self.split_flag.value & 0b00000001) << 7
        split_layer_flag = (self.split_layer_flag.value & 0b00000001) << 7
        pan = self.pan.value << 4
        cycle = (self.cycle.value & 0b00000001) << 7

        bytes.append(am + dca4_modulation_amount)
        bytes.append(sync + self.frequency.value)
        bytes.append(self.resonance.value)

        bytes.append(filter_modulation_sources[0] +
                     filter_modulation_sources[1])

        bytes.append(reset_voice + display_to_pcb(
                     self.filter_modulation_amount[0].value))

        bytes.append(mono + display_to_pcb(
                     self.filter_modulation_amount[1].value))

        bytes.append(reset_envelope + filter_keyboard_tracking)
        bytes.append(reset_oscillator + self.glide.value)
        bytes.append(split_direction + self.split_point.value)
        bytes.append(layer_flag + self.layer_program.value)
        bytes.append(split_flag + self.split_program.value)
        bytes.append(split_layer_flag + self.split_layer_program.value)
        bytes.append(pan + self.pan_modulation_source.value)
        bytes.append(cycle +
                     display_to_pcb(self.pan_modulation_amount.value))

        return bytes

    def deserialize(self, bytes):
        """Deserialize the bytearray into the class's attributes."""
        byte = next(bytes)

        self.am.value = (byte & 0b10000000) >> 7
        self.dca4_modulation_amount.value = (byte & 0b01111111) >> 1

        byte = next(bytes)

        self.sync.value = (byte & 0b10000000) >> 7
        self.frequency.value = byte & 0b01111111

        self.resonance.value = next(bytes)

        byte = next(bytes)

        self.filter_modulation_sources[0].value = byte & 0b00001111
        self.filter_modulation_sources[1].value = byte >> 4

        byte = next(bytes)

        self.reset_voice.value = (byte & 0b10000000) >> 7
        self.filter_modulation_amount[0].value = pcb_to_display(
            byte & 0b01111111)

        byte = next(bytes)

        self.mono.value = (byte & 0b10000000) >> 7
        self.filter_modulation_amount[1].value = pcb_to_display(
            byte & 0b01111111)

        byte = next(bytes)

        self.reset_envelope.value = (byte & 0b10000000) >> 7
        self.filter_keyboard_tracking.value = (byte & 0b01111111) >> 1

        byte = next(bytes)

        self.reset_oscillator.value = (byte & 0b10000000) >> 7
        self.glide.value = byte & 0b01111111

        byte = next(bytes)

        self.split_direction.value = (byte & 0b10000000) >> 7
        self.split_point.value = byte & 0b01111111

        byte = next(bytes)

        self.layer_flag.value = (byte & 0b10000000) >> 7
        self.layer_program.value = byte & 0b01111111

        byte = next(bytes)

        self.split_flag.value = (byte & 0b10000000) >> 7
        self.split_program.value = byte & 0b01111111

        byte = next(bytes)

        self.split_layer_flag.value = (byte & 0b10000000) >> 7
        self.split_layer_program.value = byte & 0b01111111

        byte = next(bytes)

        self.pan.value = (byte & 0b11110000) >> 4
        self.pan_modulation_source.value = byte & 0b00001111

        byte = next(bytes)

        self.cycle.value = (byte & 0b10000000) >> 7
        self.pan_modulation_amount.value = pcb_to_display(byte & 0b01111111)


class ESQ1Patch(ParameterCollection):
    """The entire ESQ-1 patch.

    Attributes:

    name -- the name of the patch.

    envelopes -- a list of four Envelope instances.

    lfos -- a list of three LFO instances.

    oscillators -- a list of three Oscillator instances.

    miscellaneous -- a Miscellaneous instance.
    """

    NAME_LENGTH = 6  # name must be 6 characters long.

    def __init__(self):
        self.name = '      '
        self.envelopes = [Envelope() for i in range(4)]
        self.lfos = [LFO() for i in range(3)]
        self.oscillators = [Oscillator() for i in range(3)]
        self.miscellaneous = Miscellaneous()

    def clean_name(self):
        """Ensure the patch name is six characters long and uppercase.

        Return a bytearray.
        """
        if len(self.name) >= self.NAME_LENGTH:
            name_cleaned = self.name[:self.NAME_LENGTH]
        else:
            name_cleaned = self.name.ljust(self.NAME_LENGTH)

        return bytearray([ord(c) for c in name_cleaned.upper()])

    def serialize(self):
        """Serialize the class's attributes into a bytearray."""
        bytes = self.clean_name()

        for envelope in self.envelopes:
            bytes += envelope.serialize()

        for lfo in self.lfos:
            bytes += lfo.serialize()

        for oscillator in self.oscillators:
            bytes += oscillator.serialize()

        bytes += self.miscellaneous.serialize()

        return bytes

    def deserialize(self, bytes):
        """Deserialize the bytearray into the class's attributes."""
        name = [chr(next(bytes)) for i in range(self.NAME_LENGTH)]

        self.name = "".join(name)

        for envelope in self.envelopes:
            envelope.deserialize(bytes)

        for lfo in self.lfos:
            lfo.deserialize(bytes)

        for oscillator in self.oscillators:
            oscillator.deserialize(bytes)

        self.miscellaneous.deserialize(bytes)


def sysex_to_esq1_patches(filename):
    """Read a SYSEX file and return a list of patches.

    If the SYSEX file is in the 'single program dump' format, the list will
    contain one patch. If the SYSEX file is in the 'all program dump' format,
    the list will contain 40 patches.
    """
    with open(filename, 'rb') as sysex_file:
        sysex = iter(bytearray(sysex_file.read()))

    # SYSEX, Ensoniq ID, ESQ-1 ID.
    assert next(sysex) == 0xF0
    assert next(sysex) == 0x0F
    assert next(sysex) == 0x02

    # the channel is not used.
    channel = next(sysex)

    dump_type = next(sysex)

    if dump_type == 0x01:
        # single program format.
        patch_count = 1
    elif dump_type == 0x02:
        # all program dump.
        patch_count = 40
    else:
        raise ValueError('Invalid dump type - %s' % dump_type)

    patches = []

    # use a generator to combine the two bytes into one.
    def _unpacker(sysex):
        while True:
            low = next(sysex)
            high = next(sysex)

            yield low + (high << 4)

    unpacker = _unpacker(sysex)

    # create a patch and unpack the bytes into it.
    for i in range(patch_count):
        patch = ESQ1Patch()
        patches.append(patch)

        patch.deserialize(unpacker)

    # ensure the end of the SYSEX file has been reached.
    assert next(sysex) == 0xF7

    return patches


def esq1_patches_to_sysex(patches, filename, channel=0):
    """Write a list of patches to the specified filename as a SYSEX file.

    If list contains one patch, the SYSEX file will be in the 'single program
    dump' format.

    Otherwise it will be in the 'all program dump' format. If the list contains
    fewer than 40 patches, it will be padded with blank patches. If the list
    contains more than 40 patches, only the first 40 will be saved.
    """
    # SYSEX, Ensoniq ID, ESQ-1 ID, channel.
    result = bytearray([0xF0, 0x0F, 0x02, channel])

    # create copy of patches in local scope.
    patches = list(patches)

    if len(patches) == 1:
        # single program dump.
        result.append(0x01)

        number_of_patches = 1
    elif len(patches) > 1:
        # all program dump.
        result.append(0x02)

        number_of_patches = 40
    else:
        raise ValueError('Must supply at least one patch.')

    # add blank patches, if necessary.
    patches += [ESQ1Patch() for i in range(number_of_patches - len(patches))]

    # if there are more than 40 patches, ignore them.
    for patch in patches[:40]:
        for bytes in patch.serialize():
            # append last four bits...
            result.append(bytes & 0b00001111)
            # ...then first four bits.
            result.append(bytes >> 4)

    # end of SYSEX.
    result.append(0xF7)

    with open(filename, 'wb') as output_file:
        output_file.write(result)
