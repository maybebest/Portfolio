from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from functional_tests.base_test_class import BaseClass
from chronowiz.watches.tests.factories import WatchDescriptionFactory, WatchFactory


class TestWatchDetailsElements(BaseClass):

    def test_that_all_elements_displayed(self):
        self.driver.get(self.url_watch)

        watch_family = self.driver.find_element_by_class_name(
            'page-header').text.lower()

        # There are two "add to tray button, so find_elementS function was used
        add_to_tray = self.driver.find_elements_by_class_name(
            'watch-preview-button')

        technical_info_anchor = self.driver.find_element_by_class_name(
            'button-link')

        # Scroll to the page bottom and wait for anchor link to appear
        self.driver.find_element_by_tag_name('html').send_keys(Keys.END)
        return_to_top_anchor = self.driver.find_element_by_class_name(
            'scroller')

        vait_for_return_to_top_anchor = WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "scroller")))

        self.assertEqual(watch_family, self.watch.family.name)
        # Check amount of watch tray elements find, because there are two buttons
        self.assertEqual(len(add_to_tray), 2)
        self.assertTrue(technical_info_anchor.is_displayed())
        self.assertTrue(return_to_top_anchor.is_displayed())


class TestWatchDetailsShowPrice(BaseClass):

    def test_watch_details_show_price(self):
        self.driver.get(self.url_watch)

        self.driver.find_element_by_class_name('watch-details__price').click()
        watch_price = self.driver.find_element_by_class_name(
            'watch-details__price').text

        self.assertIn(str(self.watch.retails_price), watch_price)


class TestWatchDetailsStaticDescription(BaseClass):

    def test_watch_static_description(self):
        self.driver.get(self.url_watch)

        description_subtitle = self.driver.find_element_by_class_name(
            'watch-text-description__subtitle').text.lower()
        description_title = self.driver.find_element_by_class_name(
            'watch-text-description__title').text.lower()
        description_text = self.driver.find_element_by_class_name(
            'watch-text-description__text').text.lower()

        self.assertEqual(description_subtitle, self.description.subtitle)
        self.assertEqual(description_title, self.description.title)
        self.assertEqual(description_text, self.description.description)


class TestWatchDetailsDynamicDescription(BaseClass):

    def setUp(self):
        super().setUp()
        self.watch_dynamic = WatchFactory()
        self.description_dynamic = WatchDescriptionFactory(
            is_carousel_item=True, watch=self.watch_dynamic, image=None)
        self.url_watch_dynamic = '{}/watches/{}'\
            .format(self.base_url, self.watch_dynamic.slug)

    def test_watch_dynamic_description(self):
        self.driver.get(self.url_watch_dynamic)

        description_subtitle = self.driver.find_element_by_class_name(
            'watch-text-description__subtitle').text.lower()
        description_title = self.driver.find_element_by_class_name(
            'watch-text-description__title').text.lower()
        description_text = self.driver.find_element_by_class_name(
            'watch-text-description__text').text.lower()

        self.assertEqual(description_subtitle, self.description_dynamic.subtitle)
        self.assertEqual(description_title, self.description_dynamic.title)
        self.assertEqual(description_text, self.description_dynamic.description)


class TestWatchDetailsViewAllModels(BaseClass):

    def test_watch_view_family_models(self):
        self.driver.get(self.url_watch)

        watch_details_family_name = self.driver.find_element_by_class_name(
            'page-header').text.lower()
        self.driver.find_element_by_class_name(
            'watch-preview__link-text').click()
        collection_details_family_name = self.driver.find_element_by_class_name(
            'page-header').text.lower()

        self.assertEqual(watch_details_family_name,
                         collection_details_family_name)


class TestWatchDetailsPreview(BaseClass):

    def test_watch_preview(self):
        self.driver.get(self.url_watch)

        preview_info = self.driver.find_element_by_class_name(
            'watch-preview__description').text.lower()
        info_to_compare = ', '.join(
            [self.watch.model, str(self.watch.case_diameter),
             str(self.watch.case_material)])

        self.assertIn(info_to_compare, preview_info)


class TestWatchDetailsHorizontalScroller(BaseClass):

    def setUp(self):
        super().setUp()

        self.description_dynamic = WatchDescriptionFactory.create_batch(
            4, is_carousel_item=True, watch=self.watch, image=None)

    def test_watch_horizontal_scroller(self):
        self.driver.get(self.url_watch)

        self.driver.find_element_by_css_selector(
            'div[data-index="0"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="1"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="2"][aria-hidden="false"]')
        self.driver.find_element_by_css_selector(
            'div[data-index="3"][aria-hidden="true"]')

        self.driver.find_element_by_class_name('slick-next').click()

        try:
            self.driver.find_element_by_css_selector(
                'div[data-index="3"][aria-hidden="false"]')
        except NoSuchElementException:
            raise NoSuchElementException(
                'Fifth element in the scroller didnt change aria-hidden '
                'attribute value to false, probably it is not working')


class TestWatchDetailsTechnicalInfo(BaseClass):

    def test_watch_technical_info(self):
        self.driver.get(self.url_watch)

        attribute_values = self.driver.find_elements_by_class_name(
            'watch-technical-info__value')

        attributes_displayed = []
        for value in attribute_values:
            values = value.text.lower().split(', ')
            attributes_displayed.extend(filter(None, values))

        watch_attributes_to_compare = []
        for attribute in self.watch_attributes:
            attributes = str(attribute).lower()
            watch_attributes_to_compare.append(attributes)

        self.assertListEqual(attributes_displayed, watch_attributes_to_compare)
