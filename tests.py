#!/usr/bin/env python

import unittest

from esq1 import (Parameter, Envelope, LFO, Oscillator, Miscellaneous,
                  ESQ1Patch)


class TestParameter(unittest.TestCase):
    def test_minimum(self):
        parameter = Parameter(3, 7)
        self.assertEqual(parameter.minimum, 3)

    def test_maximum(self):
        parameter = Parameter(1, 153)
        self.assertEqual(parameter.maximum, 153)

    def test_default(self):
        parameter = Parameter(6, 43)
        self.assertEqual(parameter.default, 6)
        self.assertEqual(parameter.value, 6)

        parameter = Parameter(6, 43, 32)
        self.assertEqual(parameter.default, 32)
        self.assertEqual(parameter.value, 32)

    def test_less_than_minimum(self):
        parameter = Parameter(5, 10)

        with self.assertRaises(ValueError):
            parameter.value = 4

    def test_more_than_maximum(self):
        parameter = Parameter(5, 10)

        with self.assertRaises(ValueError):
            parameter.value = 11

    def test_minimum_more_than_maximum(self):
        with self.assertRaises(ValueError):
            Parameter(4, 3)


class TestParity(object):
    cls = None
    maxDiff = None

    def test_parity(self):
        original = self.cls()

        for i in range(5):
            original.randomize()

            original_bytes = iter(original.serialize())
            new = self.cls()
            new.deserialize(original_bytes)

            self.assertEqual(original, new)

            original = new


class TestEnvelopeParity(TestParity, unittest.TestCase):
    cls = Envelope


class TestLFOParity(TestParity, unittest.TestCase):
    cls = LFO


class TestOscillatorParity(TestParity, unittest.TestCase):
    cls = Oscillator


class TestMiscellaneousParity(TestParity, unittest.TestCase):
    cls = Miscellaneous


class TestESQ1PatchParity(TestParity, unittest.TestCase):
    cls = ESQ1Patch


if __name__ == '__main__':
    unittest.main()
