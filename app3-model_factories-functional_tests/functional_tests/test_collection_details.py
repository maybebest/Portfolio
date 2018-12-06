from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from functional_tests.base_test_class import BaseClass


class TestCollectionElements(BaseClass):

    def test_that_all_elements_displayed(self):
        self.driver.get(self.url_collection)

        family_name = self.driver.find_element_by_class_name(
            'page-header').text.lower()
        family_brand = self.driver.find_element_by_class_name(
            'page-subheader').text.lower()
        family_description = self.driver.find_element_by_class_name(
            'collection-page__description').text.lower()

        self.assertEqual(self.watch.family.name, family_name)
        self.assertEqual(self.watch.brand.name, family_brand)
        self.assertEqual(self.watch.family.description, family_description)


class TestCollectionFilters(BaseClass):

    def filter_test_preparation(self, number):
        self.driver.get(self.url_collection)
        # Wait for filter list is loaded
        self.driver.find_element_by_class_name('watch-filter')

        # Open filter list
        self.driver.find_element_by_class_name('filters-btn').click()

        vait_for_filters_loaded = WebDriverWait(self.driver, 5).until(
            EC.visibility_of_all_elements_located((By.CLASS_NAME,
                                                   "watch-filter__checkmark")))
        # Store fiter name that going to be used
        filter_name = self.driver.find_element_by_css_selector(
            'div.watch-filter:nth-child({}) > div:nth-child(3) > label:nth-child(2)'
            .format(number)).text.lower()

        # User filter
        self.driver.find_element_by_css_selector(
            'div.watch-filter:nth-child({}) > div:nth-child(3) > label:nth-child(2)'
            .format(number)).click()

        # Click on the first filter result (go to some watch details page)
        self.driver.find_element_by_css_selector(
            'div.watches-grid > div:nth-child(1)').click()

        # Store watch attributes
        attr_list = self.driver.find_element_by_id(
            'technicalInfo').text.split('\n')
        attr_list = [line.lower() for line in attr_list]

        self.assertIn(filter_name, attr_list)

    def test_filters(self):
        for x in range(1, 6):
            self.filter_test_preparation(x)


class TestCollectionGrid(BaseClass):

    def setUp(self):
        super().setUp()
        self.create_watches()
        self.url_collection = '{}/collections/{}'\
            .format(self.base_url, self.list_of_watches[0].family.slug)

    def test_collection_grid(self):
        self.driver.get(self.url_collection)

        found_elements = self.driver.find_element_by_class_name(
            'watches-grid').find_elements_by_tag_name('div')
        amount = len(found_elements)

        self.assertEqual(amount, 12)


class TestCollectionShowMore(BaseClass):

    def setUp(self):
        super().setUp()
        self.create_watches()
        self.url_collection = '{}/collections/{}'\
            .format(self.base_url, self.list_of_watches[0].family.slug)

    def test_show_more_button(self):
        self.driver.get(self.url_collection)

        self.driver.find_element_by_class_name('main-button').click()

        found_elements_after = self.driver.find_element_by_class_name(
            'watches-grid').find_elements_by_tag_name('div')
        amount_after = len(found_elements_after)

        self.assertEqual(amount_after, 13)


class TestCollectionWatchPreview(BaseClass):

    def test_watch_preview(self):
        self.driver.get(self.url_collection)

        preview_info = self.driver.find_element_by_class_name(
            'grid-watch-preview__description').text.lower()
        info_to_compare = ', '.join(
            [self.watch.model, str(self.watch.case_diameter),
             str(self.watch.case_material)])

        self.assertEqual(preview_info, info_to_compare)
