from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from functional_tests.base_test_class import BaseClass
from chronowiz.watches.tests.factories import BrandFactory


class TestHomeShowMore(BaseClass):

    def test_show_more(self):
        self.brands = BrandFactory.create_batch(30)
        self.driver.get(self.base_url)

        vait_for_brands_loaded = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                            "div.brands-list__item-enter-done:nth-child(12)")))

        elements_in_grid_default = self.driver.find_elements_by_class_name(
            'brands-list__item-enter-done')
        self.assertEqual(len(elements_in_grid_default), 12)

        self.driver.find_element_by_class_name('button').click()
        vait_for_show_more_brand_loaded = WebDriverWait(self.driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR,
                            "div.brands-list__item-enter-done:nth-child(31)")))

        elements_in_grid_show_more = self.driver.find_elements_by_class_name(
            'brands-list__item-enter-done')
        self.assertGreaterEqual(len(elements_in_grid_show_more), 31)


class TestHomeSearch(BaseClass):

    def test_search(self):
        self.driver.get(self.base_url)

        exprected_brand_name = self.brand.name
        self.driver.find_element_by_class_name(
            'text-input').send_keys(exprected_brand_name)
        self.driver.find_element_by_class_name(
            'brands-list__item-enter-done').click()

        self.driver.refresh()
        existing_brand_name = self.driver.find_element_by_class_name(
            'page-header').text.lower()

        self.assertEqual(exprected_brand_name, existing_brand_name)
