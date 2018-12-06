from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver

from chronowiz.watches.tests.factories import WatchFactory


class TestWatchTray(StaticLiveServerTestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()
        self.WATCHES_COUNT = 5
        self.watches = WatchFactory.create_batch(self.WATCHES_COUNT)

        self.WATCH_BASE_URL = f'{self.live_server_url}/watches/'
        self.TRAY_URL = f'{self.live_server_url}/tray/'

        self.TOP_BUTTON_SELECTOR = '.watch-preview .button-group .button'
        self.BOTTOM_BUTTON_SELECTOR = '#technicalInfo ~ .button-group .button:not(first-child)'

    def tearDown(self):
        self.browser.close()

    def get_watch_url(self, watch_index):
        if (watch_index in range(self.WATCHES_COUNT)):

            return self.WATCH_BASE_URL + self.watches[watch_index].slug

    def add_watch_to_tray(self, button_selector=None):
        button_selector = (self.TOP_BUTTON_SELECTOR
                           if button_selector is None else button_selector)
        self.browser.find_element_by_css_selector(button_selector).click()

    def populate_tray(self):
        for watch in self.watches:
            self.browser.get(self.WATCH_BASE_URL + watch.slug)
            self.add_watch_to_tray()

    def test_user_can_use_tray_feature(self):
        # a user navigates to some detail watch page
        # and use the top button to add the watch to tray

        FIRST_WATCH_INDEX = 0
        SECOND_WATCH_INDEX = 1
        LAST_WATCH_INDEX = len(self.watches) - 1
        LAST_SLIDE_SELECTOR = f'.slick-slide[data-index="{LAST_WATCH_INDEX}"]'

        self.browser.get(self.get_watch_url(FIRST_WATCH_INDEX))
        self.add_watch_to_tray(self.TOP_BUTTON_SELECTOR)
        # TODO he can see the button text has changed

        # the user navigates to the tray page and sees his watch there
        self.browser.get(self.TRAY_URL)
        self.assertEqual(
            len(self.browser.find_elements_by_class_name('slick-slide')), 1)
        self.assertEqual(
            self.browser.find_element_by_css_selector('.slick-slide a')
            .text.lower(), self.watches[FIRST_WATCH_INDEX].model)

        # the user decides to add more watches to tray
        self.populate_tray()
        # he goes to the tray page and can use carousel to compare watches
        self.browser.get(self.TRAY_URL)
        self.assertEqual(
            len(self.browser.find_elements_by_css_selector('.slick-slide')),
            self.WATCHES_COUNT)
        last_slide = self.browser.find_element_by_css_selector(
            LAST_SLIDE_SELECTOR)
        self.assertFalse(last_slide.is_displayed())

        # the user can delete a watch
        self.browser.find_element_by_css_selector(
            '.slick-slide:first-child button').click()
        self.assertEqual(
            len(self.browser.find_elements_by_css_selector('.slick-slide')),
            self.WATCHES_COUNT - 1)