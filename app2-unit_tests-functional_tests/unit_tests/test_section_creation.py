import json
from django.test import Client
from simfoni_analytics.apps.data_management.tests.base import TestBaseClass
from simfoni_analytics.apps.main.models import Section


class TestCreateSection(TestBaseClass):
    def setUp(self):
        super(TestCreateSection, self).setUp()
        self.c = Client()

    def test_section_creation(self):
        create_section = self.c.post('/section/save/ajax/', {
                'name': 'test_section',
                'index': 1,
                'company': self.comp.id,
                'subsections': '{"update": [],"delete": []}'
            },)
        response = json.loads(create_section.content)
        section_qs = Section.objects.filter(name='test_section')
        section_attrs = Section.objects.get(name='test_section')

        self.assertEqual(True, response['success'])
        self.assertTrue(section_qs.exists())
        self.assertEqual(section_attrs.index, 1)

    def test_subsection_creation(self):
        create_subsection = self.c.post('/section/save/ajax/', {
                'name': 'test_section_2',
                'index': 2,
                'company': self.comp.id,
                'subsections': '{"update": [{"name": "test_subsection", "index": 3},'
                               '{"name": "test_subsection_2", "index": 4}], "delete": []}'
            },)
        response = json.loads(create_subsection.content)
        section_qs = Section.objects.filter(name='test_subsection_2')
        subsection_attrs = Section.objects.get(name='test_subsection_2')

        self.assertEqual(True, response['success'])
        self.assertTrue(section_qs.exists())
        self.assertEqual(subsection_attrs.index, 4)
