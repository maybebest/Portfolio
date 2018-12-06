from selenium.webdriver.support.ui import Select
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from functional_tests.base_test_class import BaseClass
from chronowiz.watches.tests.factories import DiscountFactory


class TestAdminPanelDiscount(BaseClass):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        user = User.objects.create(username='retailer')
        user.set_password('retailer')
        user.is_active = True
        user.is_staff = True
        user.save()

        permission = Permission.objects.get(name='Can change watch')
        user.user_permissions.add(permission)

        self.discount = DiscountFactory(brand=self.watch.brand, value=10)

    def test_retailer_discount(self):
        self.driver.get(self.url_watch_admin)

        self.driver.find_element_by_id('id_username').send_keys('retailer')
        self.driver.find_element_by_id('id_password').send_keys('retailer')
        self.driver.find_element_by_css_selector(
            'div.submit-row > input[type="submit"]').click()

        price_without_discount = self.driver.find_element_by_class_name(
            'price').text.strip('$')
        # Select discount in drop-down
        Select(self.driver.find_element_by_class_name(
            'row__discount-select')).select_by_value('1')
        existing_price_with_discount = self.driver.find_element_by_class_name(
            'selling-price').text.strip('$')
        expected_price_with_discount = int(price_without_discount)*0.9

        self.assertAlmostEqual(int(existing_price_with_discount),
                               expected_price_with_discount, delta=1)


class TestAdminPanelInStock(BaseClass):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        user = User.objects.create(username='retailer')
        user.set_password('retailer')
        user.is_active = True
        user.is_staff = True
        user.save()

        permission = Permission.objects.get(name='Can change watch')
        user.user_permissions.add(permission)

        self.discount = DiscountFactory(brand=self.watch.brand, value=10)
        self.url_watch_admin_in_stock = \
            '{}/admin/watches/watch/?available=1'.format(self.base_url)

    def test_retailer_in_stock(self):
        self.driver.get(self.url_watch_admin_in_stock)

        self.driver.find_element_by_id('id_username').send_keys('retailer')
        self.driver.find_element_by_id('id_password').send_keys('retailer')
        self.driver.find_element_by_css_selector(
            'div.submit-row > input[type="submit"]').click()

        amount_watches_in_stock_default = \
            self.driver.find_elements_by_class_name('row')
        # Check that watch not in stock by default
        self.assertEqual(len(amount_watches_in_stock_default), 0,
                         'Watch is In Stock by default, that incorrect')

        self.driver.get(self.url_watch_admin)
        self.driver.find_element_by_class_name('slider').click()

        self.driver.get(self.url_watch_admin_in_stock)
        amount_watches_in_stock = self.driver.find_elements_by_class_name(
                                                                        'row')
        # Check that watched can be added to stock
        self.assertEqual(len(amount_watches_in_stock), 1,
                         'Watch was not added to Stock')

        self.driver.find_element_by_class_name('slider').click()
        self.driver.refresh()
        amount_watches_in_stock_after_remove = \
            self.driver.find_elements_by_class_name('row')
        # Check that watches can be removed from stock
        self.assertEqual(len(amount_watches_in_stock_after_remove), 0,
                         'Watch was not removed from Stock')
