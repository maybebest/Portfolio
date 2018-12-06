from simfoni_analytics.apps.data_management.tests.functional_test.base_selenium import BaseClass
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestTaxonomyPopup(BaseClass):

    def test_suggest_taxonomy_popup(self):
        self.driver.get(self.url_login)
        self.driver.find_element_by_id('exampleInputEmail1').send_keys('test_app@a8.com')
        self.driver.find_element_by_id('exampleInputPassword1').send_keys('test')
        self.driver.find_element_by_class_name('mt-lg').click()

        self.driver.get('{}/data_management/app/company_spend/list/'.format(self.base_url))

        amount_of_lines_shown = WebDriverWait(self.driver, 30).until(
            EC.text_to_be_present_in_element((By.ID,"company_spend_list_table_info"), 'Showing 1 to 16 of 16 entries'), 'Wrong amount of lines shown')

        amount_of_lines_ec = self.driver.find_element_by_id('company_spend_list_table_info').text
        self.assertIn('16', amount_of_lines_ec)

        click_in_line = WebDriverWait(self.driver, 30).until(
            EC.visibility_of_element_located((By.XPATH,'//*[@id="company_spend_list_table"]/tbody/tr/td[text()= "769783"]')), "Cant click in line to suggest taxonomy").click()

        click_in_suggets_taxonomy_button = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#company_spend_list_table_wrapper > div.row.row-sm > div.col-xs-3.pull-right.abtns'))).click()

        popup_title = WebDriverWait(self.driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@id="taxonomy_level_expandable_list_popup_id"]'
                                                  '/div[@class="modal-dialog"]/div[@class="modal-content"]'
                                                  '/div[@class="modal-header"]/h4'))).get_attribute('textContent')
        self.assertIn('Taxonomy Levels', popup_title)

        search_box = WebDriverWait(self.driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR,
                                              '#taxonomy_level_expandable_list_popup_id > '
                                              'div.modal-dialog > div.modal-content > '
                                              'div.modal-body > div.row.form-group > '
                                              'div.col-sm-3 > input.form-control.input-sm')), 'Search box not found')

        category_levels = self.driver.find_elements_by_xpath('//*[@id="taxonomy_level_expandable_list_popup_id"]'
                                                             '/div[@class="modal-dialog"]/div[@class="modal-content"]'
                                                             '/div[@class="modal-body"]/div[@class="row"]/div[@class="col-sm-12"]/div')

        levels_displayed = []
        for level in category_levels:
            levels_displayed.append(level.text)

        levels_to_compare = ['LEVEL 1', 'LEVEL 2', 'LEVEL 3', 'LEVEL 4', 'LEVEL 5', 'LEVEL 6', 'TOTAL SUM']
        self.assertListEqual(levels_displayed, levels_to_compare)

        categories_lvl1 = self.driver.find_element_by_css_selector(
                            '#taxonomy_level_expandable_list_popup_id > '
                            'div.modal-dialog > div > div.modal-body > '
                            'div.taxonomy-levels-container > div.taxonomy-level-item > '
                            'input[value="Medical"]').find_element_by_xpath('../a').click()

        categories_lvl2 = self.driver.find_element_by_css_selector(
                            '#taxonomy_level_expandable_list_popup_id > '
                            'div.modal-dialog > div > div.modal-body > '
                            'div.taxonomy-levels-container > div.taxonomy-level-item > '
                            'input[value="Medical"]').find_element_by_xpath(
                            '../div[@class="children"]/div[@class="taxonomy-level-item"]/input[@value="Medical Consumables"]/../a').click()

