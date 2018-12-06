from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from chronowiz.watches.tests.factories import WatchFactory
from bs4 import BeautifulSoup


class TestAdminWatchDetail(TestCase):

    def setUp(self):
        User = get_user_model()
        user = User.objects.create(username='admin')
        user.set_password('admin')
        user.is_active = True
        user.is_superuser = True
        user.is_staff = True
        user.save()
        watch = WatchFactory()

    def test_can_fetch_all_necessary_fields(self):
        self.client.login(username='admin', password='admin')

        response = self.client.get('/admin/watches/watch/').content
        soup = BeautifulSoup(response, 'html.parser')

        expected_field_names_in_left_menu = [
            'dial finishs', 'band colors', 'users', 'band materials',
            'certifications', 'families', 'dial handss', 'discounts',
            'movement names', 'groups', 'case shapes', 'case materials',
            'brands', 'dial indexs', 'clasps', 'email addresses', 'watches',
            'dial colors', 'movement assemblys', 'watch function names',
            'retailer watch infos', 'case backs', 'sites', 'themes',
            'clasp materials', 'social accounts', 'social applications',
            'case bezels', 'social application tokens', 'case front crystals']
        expected_field_in_content_section = [
            'brand', 'family', 'model', 'reference', 'go to watch details',
            'gender', 'production year', 'limitation', 'power reserve',
            'water resistance', 'retail price']

        existing_field_names_in_left_menu = \
            [t.text.lower() for t in soup.select('ul li a')]
        for field_name_menu in expected_field_names_in_left_menu:
            self.assertIn(field_name_menu, existing_field_names_in_left_menu)

        existing_field_in_content_section = \
            [t.text.lower().strip(' :') for t in soup.select('.row span, .row a')]
        for field_name_content in expected_field_in_content_section:
            self.assertIn(field_name_content, existing_field_in_content_section)


class TestRetailerWatchList(TestCase):

    def setUp(self):
        User = get_user_model()
        user = User.objects.create(username='retailer')
        user.set_password('retailer')
        user.is_active = True
        user.is_staff = True
        user.save()
        watch = WatchFactory()

        permission = Permission.objects.get(name='Can change watch')
        user.user_permissions.add(permission)

    def test_can_fetch_all_necessary_fields(self):
        self.client.login(username='retailer', password='retailer')

        response = self.client.get('/admin/watches/watch/').content
        soup = BeautifulSoup(response, 'html.parser')

        expected_field_names_in_left_menu = ['watches', 'in stock']
        expected_field_in_content_section = [
            'brand', 'family', 'model', 'reference', 'go to watch details',
            'gender', 'production year', 'limitation', 'power reserve',
            'water resistance', 'retail price', 'discount', 'selling price',
            '0', '1']

        existing_field_names_in_left_menu = \
            [t.text.lower() for t in soup.select('ul li a')]
        for field_name_menu in expected_field_names_in_left_menu:
            self.assertIn(field_name_menu, existing_field_names_in_left_menu)

        existing_field_in_content_section = \
            [t.text.lower().strip(' :') for t in soup.select('.row span, .row a')]
        for field_name_content in expected_field_in_content_section:
            self.assertIn(field_name_content, existing_field_in_content_section)

