from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase


class SeleniumBaseClass(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.base_url = self.live_server_url
        self.url_login = '{}/login/'.format(self.base_url)

    def tearDown(self):
        self.driver.quit()
