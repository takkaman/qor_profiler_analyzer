#!/remote/us01home40/phyan/depot/Python-2.7.11/bin/python
from qor_web import app
import unittest
import urllib2
import json
# from flask.ext.testing import TestCase
from flask_testing import TestCase, LiveServerTestCase
import unittest
import flask
# from flask import Flask, url_for
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

# class TestBase(TestCase):
#     def create_app(self):
#         app = Flask(__name__)
#         app.config['TESTING'] = True
#         # Default port is 5000
#         app.config['LIVESERVER_PORT'] = 8087
#         # Default timeout is 5 seconds
#         app.config['LIVESERVER_TIMEOUT'] = 10
#         return app

#     # def setUp(self):
#     #     # binary = FirefoxBinary('/usr/bin/firefox')
#     #     self.driver = webdriver.Firefox()
#     #     # self.driver.get(self.get_server_url())

#     # def tearDown(self):
#     #     self.driver.quit()

#     # def test_server_is_up_and_running(self):
#     #     response = urllib2.urlopen(self.get_server_url())
#     #     self.assertEqual(response.code, 200)

#     def test_index(self):
#         response = self.client.get('/index')
#         print response
#         self.assertEqual(response.code, 200)

class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_log_mode_entry(self):
        with app.test_request_context('index/?mode=log&compress=1&input_num=1&input1=&script_num=0'):
            assert flask.request.args['compress'] == '1'
        response = self.app.get('index/?mode=log&compress=1&input_num=1&input1=&script_num=0', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        # assert b'Invalid password' in response.data  

    def test_log_w_multi_pattern(self):
        response = self.app.get('profile?mode=log&pattern=all&compress=1&input_list=%2Fu%2Fphyan%2Fworkspace%2Fpython%2Fqor_analyzer%2Ftest%2FDaedalus_TS16FFP.icpopt.out&cmd=full_flow&active_pattern=ROPT&prev_d=0&prev_p=8&crnt_d=0&crnt_p=10', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        # print response.get_data('compress')
        # self.assertEqual(response.data['compress'], '1')
        # there should be 6 patterns displayed
        assert '<a href="#ROPT" class="ROPT" aria-controls="ROPT" role="tab" data-toggle="tab" onclick="activePatternNav(this);"><strong>ROPT</strong></a>' in response.data
        assert '<a href="#PREROUTE" class="PREROUTE" aria-controls="PREROUTE" role="tab" data-toggle="tab" onclick="activePatternNav(this);"><strong>PREROUTE</strong></a>' in response.data
        assert '<a href="#ELAPSE_MEM" class="ELAPSE_MEM" aria-controls="ELAPSE_MEM" role="tab" data-toggle="tab" onclick="activePatternNav(this);"><strong>ELAPSE_MEM</strong></a>' in response.data
        assert '<a href="#FUNC_DIST" class="FUNC_DIST" aria-controls="FUNC_DIST" role="tab" data-toggle="tab" onclick="activePatternNav(this);"><strong>FUNC_DIST</strong></a>' in response.data
        assert '<a href="#DF_GROPT" class="DF_GROPT" aria-controls="DF_GROPT" role="tab" data-toggle="tab" onclick="activePatternNav(this);"><strong>DF_GROPT</strong></a>' in response.data
        assert '<a href="#PREROUTE_STG" class="PREROUTE_STG" aria-controls="PREROUTE_STG" role="tab" data-toggle="tab" onclick="activePatternNav(this);"><strong>PREROUTE_STG</strong></a>' in response.data
        # ROPT should be the 1st active pattern
        # assert '<div class="panel panel-danger pattern_nav ROPT_nav ">' in response.data
        # assert '<div class="col-md-1 nav-target pattern_nav ROPT_nav" role="complementary">' in response.data

if __name__ == '__main__':
    unittest.main()