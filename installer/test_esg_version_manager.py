#!/usr/bin/local/env python

import unittest
import esg_version_manager
import os
import semver
import yaml


with open('esg_config.yaml', 'r') as config_file:
    config = yaml.load(config_file)


class test_ESG_version_manager(unittest.TestCase):

    def test_check_module_version(self):
        # output = esg_version_manager.check_module_version("esgcet", "3.0.1")
        # self.assertEqual(output,0)

        output = esg_version_manager.check_module_version("pylint", "1.9")
        self.assertEqual(output,1)

    def test_get_current_esgf_library_version(self):
        output = esg_version_manager.get_current_esgf_library_version("esgf-security")
        self.assertEqual(output, True)

    def test_get_current_webapp_version(self):
        output = esg_version_manager.get_current_webapp_version("esg-orp")
        self.assertEqual(output, "2.9.0")

    def test_check_webapp_version(self):
        output = esg_version_manager.check_webapp_version("esg-orp", "2.0")
        self.assertEqual(output, 0)

        output = esg_version_manager.check_webapp_version("esg-orp", "4.0")
        self.assertEqual(output, 1)


if __name__ == '__main__':
    unittest.main()