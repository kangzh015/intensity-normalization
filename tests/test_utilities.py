#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
tests.test_utilties

test the functions located in utilities submodule for runtime errors

Author: Jacob Reinhold (jacob.reinhold@jhu.edu)
Created on: May 01, 2018
"""

import os
import unittest

import numpy as np

from intensity_normalization.utilities import io, mask


class TestUtilities(unittest.TestCase):

    def setUp(self):
        self.wd = os.path.dirname(os.path.abspath(__file__))
        self.test_fn = 'test.nii.gz'
        self.mask_fn = 'mask.nii.gz'
        self.img = io.open_nii(os.path.join(self.wd, 'test_data/', self.test_fn))
        self.brain_mask = io.open_nii(os.path.join(self.wd, 'test_data/', self.mask_fn))

    def test_mask(self):
        m = mask.fcm_class_mask(self.img, self.brain_mask, hard_seg=True)
        self.assertEqual(len(np.unique(m)), 4)

    def tearDown(self):
        del self.img, self.brain_mask


if __name__ == '__main__':
    unittest.main()
