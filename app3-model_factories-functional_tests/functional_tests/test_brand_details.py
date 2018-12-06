import time
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys

from functional_tests.base_test_class import BaseClass
from chronowiz.watches.tests.factories import WatchFactory, FamilyFactory, \
    BrandFactory, GenderFactory


class TestBrandDetailsElements(BaseClass):
    def test_that_all_elements_displayed(self):
        self.driver.get(self.url_brand)

        # import pdb; pdb.set_trace()
        brand_name = self.driver.find_element_by_class_name(
            'page-header').text.lower()
        brand_subtitle = self.driver.find_element_by_class_name(
            'page-subheader').text.lower()
        family_name = self.driver.find_element_by_class_name(
            'collection-row__header').text.lower()
        preview_watch_attributes = self.driver.find_element_by_class_name(
            'watch-list-item__description').text.lower()
        preview_watch_attributes_to_compare = ', '.join(
            [str(self.watch.case_diameter),
             str(self.watch.case_material)])
        preview_watch_model = self.driver.find_element_by_class_name(
            'watch-list-item__title').text.lower()

        self.assertEqual(brand_name, self.watch.brand.name)
        self.assertEqual(brand_subtitle, 'the collections')
        self.assertEqual(family_name, self.watch.family.name)
        self.assertEqual(preview_watch_attributes,
                         preview_watch_attributes_to_compare)
        self.assertEqual(preview_watch_model, self.watch.model)


class TestBrandDetailsFilters(BaseClass):
    def setUp(self):
        super().setUp()

        self.watches_male = WatchFactory(
            family=self.family,
            gender=GenderFactory(gender='Man'),
            brand=self.brand,
            model="man")
        self.watches_female = WatchFactory(
            family=self.family,
            gender=GenderFactory(gender='Woman'),
            brand=self.brand,
            model='woman')
        self.watches_unisex = WatchFactory(
            family=self.family,
            gender=GenderFactory(gender='Unisex'),
            brand=self.brand,
            model='unisex')

        self.url_brand = '{}/brands/{}'\
            .format(self.base_url, self.watches_male.brand.slug)

    def test_brand_details_filters(self):
        self.driver.get(self.url_brand)

        # Check filter by "all"
        self.driver.find_element_by_xpath('//label[@for="all"]').click()
        elements_all = self.driver.find_elements_by_class_name(
            'watch-list-item')
        self.assertEqual(len(elements_all), 3)

        # Check filter by "men"
        self.driver.find_element_by_xpath('//label[@for="man"]').click()
        men_filter_title = self.driver.find_element_by_xpath(
            '//label[@for="man"]').text.lower()
        elements_men = self.driver.find_elements_by_class_name(
            'watch-list-item')
        for element_men in elements_men:
            element_men = element_men.find_element_by_class_name(
                'watch-list-item__title').text.lower()
            self.assertEqual(element_men, men_filter_title)

        # Check filter by "woman"
        self.driver.find_element_by_xpath('//label[@for="woman"]').click()
        woman_filter_title = self.driver.find_element_by_xpath(
            '//label[@for="woman"]').text.lower()
        elements_woman = self.driver.find_elements_by_class_name(
            'watch-list-item')
        for element_woman in elements_woman:
            element_woman = element_woman.find_element_by_class_name(
                'watch-list-item__title').text.lower()
            self.assertEqual(element_woman, woman_filter_title)


class TestBrandDetailsShowMore(BaseClass):
    def setUp(self):
        super().setUp()
        self.brand = BrandFactory()
        self.family_list = []
        self.watch_family_list = []
        #Create 5 families with 5 watches in each
        for some in range(5):
            self.family_list.append(FamilyFactory())
            self.watch_family_list.append(
                WatchFactory.create_batch(
                    5, family=self.family_list[some], brand=self.brand))

        self.url_brand = '{}/brands/{}'\
            .format(self.base_url, self.watch_family_list[0][0].brand.slug)

    def test_brand_show_more(self):
        self.driver.get(self.url_brand)

        elements_displayed_before = self.driver.find_elements_by_class_name(
            'collection-row')
        self.driver.find_element_by_tag_name('html').send_keys(Keys.END)
        time.sleep(1)
        self.driver.find_element_by_class_name('button').click()
        elements_displayed_after = self.driver.find_elements_by_class_name(
            'collection-row')

        self.assertEqual(len(elements_displayed_before), 4)
        self.assertEqual(len(elements_displayed_after), 5)


class TestBrandDetailsHorizontalScroller(BaseClass):
    def setUp(self):
        super().setUp()
        self.watches = WatchFactory.create_batch(
            5, brand=self.brand, family=self.family)
        self.url_brand_by_index = '{}/brands/{}'\
            .format(self.base_url, self.watches[0].brand.slug)

    def test_brand_horizontal_scroll(self):
        self.driver.get(self.url_brand_by_index)

        self.driver.find_element_by_css_selector(
            'div[data-index="0"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="1"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="2"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="3"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="4"][aria-hidden="true"]')

        self.driver.find_element_by_class_name('slick-next').click()

        try:
            self.driver.find_element_by_css_selector(
                'div[data-index="4"][aria-hidden="false"]')
        except NoSuchElementException:
            raise NoSuchElementException(
                'Fifth element in the scroller didnt change aria-hidden '
                'attribute value to false, probably it is not working')
