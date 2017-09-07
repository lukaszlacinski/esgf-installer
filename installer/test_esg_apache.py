#!/usr/bin/local/env python

import unittest
import esg_apache_manager
import esg_functions
import os
import shutil
import yaml
import pip

with open('esg_config.yaml', 'r') as config_file:
    config = yaml.load(config_file)

class test_ESG_apache(unittest.TestCase):

    @classmethod
    def tearDownClass(cls):
        esg_functions.stream_subprocess_output("yum remove -y httpd")
        pip.main(["uninstall", "mod_wsgi"])


    def test_install_apache_httpd(self):
        esg_apache_manager.install_apache_httpd()
        output = esg_functions.call_subprocess("httpd -version")["stdout"]
        print "output:", output
        self.assertIsNotNone(output)


        esg_apache_manager.install_mod_wsgi()
        self.assertTrue(os.path.isfile("/etc/httpd/modules/mod_wsgi-py27.so"))


        esg_apache_manager.make_python_eggs_dir()
        self.assertTrue(os.path.isdir("/var/www/.python-eggs"))
        owner, group = esg_functions.get_dir_owner_and_group("/var/www/.python-eggs")
        self.assertEqual(owner, "apache")
        self.assertEqual(group, "apache")



if __name__ == '__main__':
    unittest.main()
