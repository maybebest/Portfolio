from django.test import TestCase
from django.contrib.auth import get_user_model
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

    def test_can_fetch_all_necessary_fields(self):
        self.client.login(username='admin', password='admin')

        response = self.client.get('/admin/watches/watch/add/').content
        soup = BeautifulSoup(response, 'html.parser')

        expected_field_names = [
            'model:', 'reference:', 'caliber:', 'power reserve:',
            'retails price:', 'tourbillon:', 'production year:', 'family:',
            'brand:', 'certification:', 'gender:', 'limitation:',
            'preview image:', 'water resistance:', 'slug:', 'clasp:',
            'clasp material:', 'band color:', 'band material:',
            'case material:', 'case shape:', 'case front crystal:',
            'case back:', 'case bezel:', 'case height:', 'case diameter:',
            'movement name:', 'movement assembly:', 'movement type:',
            'movement diameter:', 'movement height:', 'movement jewels:',
            'movement vph frequency:', 'dial color:', 'dial index:',
            'dial finish:', 'dial hands:', 'image:', 'is carousel item',
            'title:', 'subtitle:', 'description:', 'image:', 'detail:',
            'watch function name:'
        ]
        existing_field_names = [
            item.text.lower() for item in soup.find_all('label')
        ]

        for field_name in expected_field_names:
            self.assertIn(field_name, existing_field_names)
