import time

from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from chronowiz.watches.tests.factories import WatchFactory
from chronowiz.watches.models import Watch


class TestSearch(StaticLiveServerTestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(5)
        self.watches = WatchFactory.create_batch(3)

    def enter_text_into_input(self, input, text):
        for char in text:
            input.send_keys(char)

    def test_user_can_search_watches(self):
        watch_model_name = self.watches[0].model
        watch_reference = self.watches[0].reference
        initialResultCount = 12
        load_by = 4
        # a user enters to the search page and sees a header
        self.driver.get(f'{self.live_server_url}/search/')
        self.assertEqual(
            self.driver.find_element_by_class_name('page-header').text.lower(),
            'search')

        # the users enters less than 3 characters, submits the form and can not see result
        search_input = self.driver.find_element_by_css_selector(
            '.search-input .text-input')
        self.enter_text_into_input(search_input, 'ro')
        search_input.send_keys(Keys.ENTER)
        search_results = self.driver.find_elements_by_class_name(
            'grid-watch-preview')
        self.assertEqual(len(search_results), 0)
        search_input.clear()

        # the user enters a search phrase and can see a suggestions list
        self.enter_text_into_input(search_input, watch_model_name[:-2])
        self.assertEqual(
            len(
                self.driver.find_elements_by_class_name(
                    'suggestion-section__option')), 3)
        search_input.clear()

        # the user types a into the search input and submits the form
        WatchFactory.create_batch(30)
        self.enter_text_into_input(search_input, watch_model_name)
        search_input.send_keys(Keys.ENTER)
        search_results = self.driver.find_elements_by_class_name(
            'grid-watch-preview')
        self.assertEqual(len(search_results), 1)
        self.assertIn(self.watches[0].model, search_results[0].text)
        self.assertNotIn(self.watches[1].model, search_results[0].text)
        self.assertNotIn(self.watches[2].model, search_results[0].text)
        search_input.clear()

        # the user also can find a watch by reference number
        self.enter_text_into_input(search_input, watch_reference)
        search_input.send_keys(Keys.ENTER)
        self.assertEqual(
            len(self.driver.find_elements_by_class_name('grid-watch-preview')),
            1)
        search_input.clear()
        self.driver.find_elements_by_class_name('grid-watch-preview')[
            0].click()
        self.assertIn(watch_reference,
                      self.driver.find_element_by_class_name(
                          'watch-technical-info').text)
        self.driver.get(f'{self.live_server_url}/search')

        # the user types only a part of model name and sees 12 watches
        search_input = self.driver.find_element_by_css_selector(
            '.search-input .text-input')
        self.enter_text_into_input(search_input, watch_model_name[:-2])
        search_input.send_keys(Keys.ENTER)
        search_results = self.driver.find_elements_by_class_name(
            'grid-watch-preview')

        self.assertEqual(len(search_results), initialResultCount)
        # he can also click on show more button and enable infinite scroll
        self.driver.find_element_by_class_name('main-button').click()
        self.assertEqual(
            len(self.driver.find_elements_by_class_name('grid-watch-preview')),
            initialResultCount + load_by)
        # the user scrolls down the page and can see more watches
        self.driver.execute_script(
            "window.scrollTo(0, window.outerHeight + 200)")
        time.sleep(0.5)
        self.assertEqual(
            len(self.driver.find_elements_by_class_name('grid-watch-preview')),
            initialResultCount + load_by * 2)
        # the user decides to filter results by case material
        self.driver.execute_script("window.scrollTo(0, 0)")
        self.driver.find_element_by_css_selector(
            '.search-filters-row .button').click()
        self.driver.find_element_by_css_selector(
            '.slick-track div[data-index="2"] .watch-filter__label').click()
        search_results = self.driver.find_elements_by_class_name(
            'grid-watch-preview')
        self.assertEqual(len(search_results), 1)

    def tearDown(self):
        self.driver.close()
