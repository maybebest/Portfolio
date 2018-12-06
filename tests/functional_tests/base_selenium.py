from selenium import webdriver
from django.core.files import File
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from simfoni_analytics.apps.main.models import User, Company
from simfoni_analytics.apps.data_management.models import DataSpendEntityUpload, TaxonomyEntity, TaxonomyEntitySum
from simfoni_analytics.apps.data_management.tasks import upload_spend_data


class BaseClass(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.base_url = self.live_server_url
        self.url_login = '{}/login/'.format(self.base_url)
        self.url_brand = '{}/brands/{}'\
            .format(self.base_url, self.watch.brand.slug)
        self.comp = Company.objects.create(
                                      name='test_company',
                                      tickertape_message='',
                                      is_power_bi_synced=True,
                                      synced_dataset_id='',
                                      data_spend_type=Company.DATA_SPEND_TYPE_DEFAULT,
                                      show_powerbi_filters_panel=True,
                                      show_tawk_to_chat=False,
                                      show_twitter_widget=False,
                                      show_data_spend_analytics_section=True,
                                      show_q_and_a=True)
        self.user = User.objects.create(
                                        email='test_app@a8.com',
                                        name='test_app',
                                        role=User.APP_USER,
                                        is_active=True,
                                        company=self.comp)
        self.user.set_password('test')
        self.user.save()
        self.data_spend_entity = DataSpendEntityUpload.objects.create(
            company=self.comp,
            file=File(open('simfoni_analytics/apps/data_management/tests/test_files/255_test_file_data_spend.xlsx')))
        upload_spend_data(self.data_spend_entity.id)


    def tearDown(self):
        self.driver.quit()
