import string
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from vitesse_prod.apps.web.selenium_test.selenium_base_class import SeleniumBaseClass


class HelpUtils(SeleniumBaseClass):

    def get_random_string(length):
        random_list = []
        for i in xrange(length):
            random_list.append(random.choice(string.ascii_uppercase + string.digits))
        return ''.join(random_list)

        # ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in xrange(10))
        # '35WO8ZYKFV'

        # ''.join(random.choices(string.ascii_uppercase + string.digits), k=10)
        # '35WO8ZYKFV'

    def find_by_xpath(self, xpath):
        return WebDriverWait(self.driver, 30).until(EC.visibility_of_element_located((By.XPATH, xpath)))

    # click_in_line = WebDriverWait(self.driver, 30).until(
    #             EC.visibility_of_element_located((By.XPATH,'//*[@id="company_spend_list_table"]/tbody/tr/td[text()= "769783"]')), "Cant click in line to suggest taxonomy").click()
