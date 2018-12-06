from django.test import Client
from simfoni_analytics.apps.data_management.tests.base import TestBaseClass
from simfoni_analytics.apps.main.models import User


class TestCreateUser(TestBaseClass):

    def setUp(self):
        super(TestCreateUser, self).setUp()
        self.c = Client()

    def test_app_user_creation(self):
        user_creation = self.c.post('/user/save/ajax/',
        {'company': self.comp.id, 'role': User.APP_USER,
         'name': 'test_app_user', 'email': 'test_app_user@ex.com',
         'password': 'Anvil8team!', 'confirm_password': 'Anvil8team!'})

        user_qs = User.objects.first()
        user_attrs = User.objects.filter(name='test_app_user')

        self.assertTrue(user_attrs.exists())
        self.assertEqual(user_qs.company.name, 'test_company')
        self.assertEqual(user_qs.get_role_display(), 'App User')
        self.assertEqual(user_qs.name, 'test_app_user')
        self.assertEqual(user_qs.email, 'test_app_user@ex.com')
        self.assertTrue(self.c.login(email='test_app_user@ex.com', password='Anvil8team!'))

    def test_company_admin_user_creation(self):
        user_creation = self.c.post('/user/save/ajax/',
        {'company': self.comp.id, 'role': User.COMPANY_ADMIN,
         'name': 'test_company_admin_user', 'email': 'test_company_admin_user@ex.com',
         'password': 'Anvil8team!', 'confirm_password': 'Anvil8team!'})

        user_qs = User.objects.first()
        user_attrs = User.objects.filter(name='test_company_admin_user')

        self.assertTrue(user_attrs.exists())
        self.assertEqual(user_qs.company.name, 'test_company')
        self.assertEqual(user_qs.get_role_display(), 'Company Admin')
        self.assertEqual(user_qs.name, 'test_company_admin_user')
        self.assertEqual(user_qs.email, 'test_company_admin_user@ex.com')
        self.assertTrue(self.c.login(email='test_company_admin_user@ex.com', password='Anvil8team!'))
