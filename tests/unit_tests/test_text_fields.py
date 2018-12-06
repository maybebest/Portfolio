from django.core.files import File
from simfoni_analytics.apps.data_management.models import DataSpendEntityUpload, DataSpendEntity
from simfoni_analytics.apps.data_management.tasks import upload_spend_data
from simfoni_analytics.apps.data_management.tests.base import TestBaseClass


class TestUploadFileTextFieLds(TestBaseClass):
    def setUp(self):
        super(TestUploadFileTextFieLds, self).setUp()
        self.data_spend_entity = DataSpendEntityUpload.objects.create(
            company=self.comp,
            file=File(open('simfoni_analytics/apps/data_management/tests/test_files/255_test_file_data_spend.xlsx')))

    def test_file_processing(self):
        upload_spend_data(self.data_spend_entity.id)
        self.assertEqual(DataSpendEntity.objects.filter(company_id=self.comp.id).count(), 500)

    def test_file_processed_lines(self):
        upload_spend_data(self.data_spend_entity.id)

        data = DataSpendEntity.objects.filter(company_id=self.comp.id).first()

        self.assertEqual(self.invoice_voucher_number,
                         data.invoice_voucher_number)
        self.assertEqual(self.currency_code, data.currency_code)
        self.assertEqual(self.supplier_name, data.supplier_name)
        self.assertEqual(self.period, data.period)
        self.assertEqual(self.invoice_voucher_line_description,
                         data.invoice_voucher_line_description)
        self.assertEqual(self.gl_description, data.gl_description)
