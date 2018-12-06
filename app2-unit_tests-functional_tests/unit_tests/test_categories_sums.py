from django.core.files import File
from simfoni_analytics.apps.data_management.models import DataSpendEntityUpload, TaxonomyEntity, TaxonomyEntitySum
from simfoni_analytics.apps.data_management.tasks import upload_spend_data
from simfoni_analytics.apps.data_management.tests.base import TestBaseClass


class TestCategoriesSum(TestBaseClass):
    def setUp(self):
        super(TestCategoriesSum, self).setUp()
        self.data_spend_entity = DataSpendEntityUpload.objects.create(
            company=self.comp,
            file=File(open('simfoni_analytics/apps/data_management/tests/test_files/255_test_file_taxonomy(few_categories).xlsx')))

    def test_cat_sum_level_1(self):
        taxonomy_entity_level_1 = TaxonomyEntity.objects.create(
                    index=1,
                    content='Cat 1',
                    company_id=self.comp.id,
                    order_index=1)

        upload_spend_data(self.data_spend_entity.id)
        category_sum_level_1 = TaxonomyEntitySum.objects.get(taxonomy_entity_id=taxonomy_entity_level_1.id)

        self.assertEqual(category_sum_level_1.sum, 27855)

    def test_cat_sum_level_2(self):
        taxonomy_entity_level_1 = TaxonomyEntity.objects.create(
                    index=1,
                    content='Cat 1',
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_2 = TaxonomyEntity.objects.create(
                    index=2,
                    content='Cat 2',
                    parent_id=taxonomy_entity_level_1.id,
                    parent_entity_id=taxonomy_entity_level_1.id,
                    company_id=self.comp.id,
                    order_index=1)

        upload_spend_data(self.data_spend_entity.id)
        category_sum_level_2 = TaxonomyEntitySum.objects.get(taxonomy_entity_id=taxonomy_entity_level_2.id)

        self.assertEqual(category_sum_level_2.sum, 26570)

    def test_cat_sum_level_3(self):
        taxonomy_entity_level_1 = TaxonomyEntity.objects.create(
                    index=1,
                    content='Cat 1',
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_2 = TaxonomyEntity.objects.create(
                    index=2,
                    content='Cat 2',
                    parent_id=taxonomy_entity_level_1.id,
                    parent_entity_id=taxonomy_entity_level_1.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_3 = TaxonomyEntity.objects.create(
                    index=3,
                    content='Cat 3',
                    parent_id=taxonomy_entity_level_2.id,
                    parent_entity_id=taxonomy_entity_level_2.id,
                    company_id=self.comp.id,
                    order_index=1)

        upload_spend_data(self.data_spend_entity.id)
        category_sum_level_3 = TaxonomyEntitySum.objects.get(taxonomy_entity_id=taxonomy_entity_level_3.id)

        self.assertEqual(category_sum_level_3.sum, 25880)

    def test_cat_sum_level_4(self):
        taxonomy_entity_level_1 = TaxonomyEntity.objects.create(
                    index=1,
                    content='Cat 1',
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_2 = TaxonomyEntity.objects.create(
                    index=2,
                    content='Cat 2',
                    parent_id=taxonomy_entity_level_1.id,
                    parent_entity_id=taxonomy_entity_level_1.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_3 = TaxonomyEntity.objects.create(
                    index=3,
                    content='Cat 3',
                    parent_id=taxonomy_entity_level_2.id,
                    parent_entity_id=taxonomy_entity_level_2.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_4 = TaxonomyEntity.objects.create(
                    index=4,
                    content='Cat 4',
                    parent_id=taxonomy_entity_level_3.id,
                    parent_entity_id=taxonomy_entity_level_3.id,
                    company_id=self.comp.id,
                    order_index=1)

        upload_spend_data(self.data_spend_entity.id)
        category_sum_level_4 = TaxonomyEntitySum.objects.get(taxonomy_entity_id=taxonomy_entity_level_4.id)

        self.assertEqual(category_sum_level_4.sum, 13710)

    def test_cat_sum_level_5(self):
        taxonomy_entity_level_1 = TaxonomyEntity.objects.create(
                    index=1,
                    content='Cat 1',
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_2 = TaxonomyEntity.objects.create(
                    index=2,
                    content='Cat 2',
                    parent_id=taxonomy_entity_level_1.id,
                    parent_entity_id=taxonomy_entity_level_1.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_3 = TaxonomyEntity.objects.create(
                    index=3,
                    content='Cat 3',
                    parent_id=taxonomy_entity_level_2.id,
                    parent_entity_id=taxonomy_entity_level_2.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_4 = TaxonomyEntity.objects.create(
                    index=4,
                    content='Cat 4',
                    parent_id=taxonomy_entity_level_3.id,
                    parent_entity_id=taxonomy_entity_level_3.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_5 = TaxonomyEntity.objects.create(
                    index=5,
                    content='Cat 5',
                    parent_id=taxonomy_entity_level_4.id,
                    parent_entity_id=taxonomy_entity_level_4.id,
                    company_id=self.comp.id,
                    order_index=1)

        upload_spend_data(self.data_spend_entity.id)
        category_sum_level_5 = TaxonomyEntitySum.objects.get(taxonomy_entity_id=taxonomy_entity_level_5.id)

        self.assertEqual(category_sum_level_5.sum, 12457)

    def test_cat_sum_level_6(self):
        taxonomy_entity_level_1 = TaxonomyEntity.objects.create(
                    index=1,
                    content='Cat 1',
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_2 = TaxonomyEntity.objects.create(
                    index=2,
                    content='Cat 2',
                    parent_id=taxonomy_entity_level_1.id,
                    parent_entity_id=taxonomy_entity_level_1.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_3 = TaxonomyEntity.objects.create(
                    index=3,
                    content='Cat 3',
                    parent_id=taxonomy_entity_level_2.id,
                    parent_entity_id=taxonomy_entity_level_2.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_4 = TaxonomyEntity.objects.create(
                    index=4,
                    content='Cat 4',
                    parent_id=taxonomy_entity_level_3.id,
                    parent_entity_id=taxonomy_entity_level_3.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_5 = TaxonomyEntity.objects.create(
                    index=5,
                    content='Cat 5',
                    parent_id=taxonomy_entity_level_4.id,
                    parent_entity_id=taxonomy_entity_level_4.id,
                    company_id=self.comp.id,
                    order_index=1)
        taxonomy_entity_level_6 = TaxonomyEntity.objects.create(
                    index=6,
                    content='Cat 6',
                    parent_id=taxonomy_entity_level_5.id,
                    parent_entity_id=taxonomy_entity_level_5.id,
                    company_id=self.comp.id,
                    order_index=1)

        upload_spend_data(self.data_spend_entity.id)
        category_sum_level_6 = TaxonomyEntitySum.objects.get(taxonomy_entity_id=taxonomy_entity_level_6.id)

        self.assertEqual(category_sum_level_6.sum, 420)
