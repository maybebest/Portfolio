import json
from django.test import Client
from simfoni_analytics.apps.data_management.tests.base import TestBaseClass
from simfoni_analytics.apps.main.models import Company, Currency


class TestCreateCompany(TestBaseClass):
    def setUp(self):
        super(TestCreateCompany, self).setUp()
        self.c = Client()
        self.currency = Currency.objects.create(name='test_currecy',
                                                code='test_currecy_code',
                                                symbol='CURRENCY',
                                                decimal_digits=1)

    def test_company_creation_default(self):
        create_company = self.c.post('/company/save/ajax/', {
        'name': 'a8_test_company', 'data_spend_type': Company.DATA_SPEND_TYPE_DEFAULT,
        'currency': self.currency.id, 'section_reports': {}
        })
        response = json.loads(create_company.content)
        company_qs = Company.objects.filter(name='a8_test_company')
        company_attrs = Company.objects.get(name='a8_test_company')

        self.assertEqual(True, response['success'])

        self.assertTrue(company_qs.exists())

        self.assertEqual(company_attrs.currency.name, 'test_currecy')
        self.assertEqual(company_attrs.get_data_spend_type_display(), 'Default')

    def test_company_creation_EKFC(self):
        create_company = self.c.post('/company/save/ajax/', {
        'name': 'a8_test_company', 'data_spend_type': Company.DATA_SPEND_TYPE_SECOND,
        'currency': self.currency.id, 'section_reports': {}
        })
        response = json.loads(create_company.content)
        company_qs = Company.objects.filter(name='a8_test_company')
        company_attrs = Company.objects.get(name='a8_test_company')

        self.assertEqual(True, response['success'])

        self.assertTrue(company_qs.exists())

        self.assertEqual(company_attrs.currency.name, 'test_currecy')
        self.assertEqual(company_attrs.get_data_spend_type_display(), 'EKFC')

    def test_company_creation_default_all_fields_filled(self):
        create_company = self.c.post('/company/save/ajax/', {
        'name': 'a8_test_company', 'data_spend_type': Company.DATA_SPEND_TYPE_DEFAULT,
        'currency': self.currency.id, 'section_reports': {}, 'show_data_spend_analytics_section':True,
        'show_q_and_a':True, 'tickertape_message': 'some tickertape_message here ! 12345', 'show_powerbi_filters_panel': True
        })
        response = json.loads(create_company.content)
        company_qs = Company.objects.filter(name='a8_test_company')
        company_attrs = Company.objects.get(name='a8_test_company')

        self.assertEqual(True, response['success'])

        self.assertTrue(company_qs.exists())

        self.assertEqual(company_attrs.currency.name, 'test_currecy')
        self.assertEqual(company_attrs.get_data_spend_type_display(), 'Default')
        self.assertEqual(company_attrs.tickertape_message, 'some tickertape_message here ! 12345')
        self.assertTrue(company_attrs.show_powerbi_filters_panel)
        self.assertTrue(company_attrs.show_q_and_a)
        self.assertTrue(company_attrs.show_data_spend_analytics_section)
