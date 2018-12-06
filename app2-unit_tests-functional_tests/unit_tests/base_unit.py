from django.test import TestCase
from simfoni_analytics.apps.main.models import Company
from simfoni_analytics.apps.data_management.models import DataSpendEntityUpload, DataSpendEntity
from simfoni_analytics.apps.data_management.tasks import upload_spend_data


class TestBaseClass(TestCase):
    def setUp(self):
        self.comp = Company.objects.create(
                                      name='test_company',
                                      tickertape_message='',
                                      is_power_bi_synced=False,
                                      synced_dataset_id='',
                                      data_spend_type=Company.DATA_SPEND_TYPE_DEFAULT,
                                      show_powerbi_filters_panel=False,
                                      show_tawk_to_chat=False,
                                      show_twitter_widget=False,
                                      show_data_spend_analytics_section=False,
                                      show_q_and_a=False,
                                      )

        self.invoice_voucher_number = '131231231231231004238589138661712553044030823705715890233519127704642861444312031152304083360606810834852577101923869825786789972350891196422532041305202501913025770859616205637788550546773907524165987536263261908747020463293525279457101342231058999049780403678128513553165251387038084795381875381016461312'
        self.currency_code = 'AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBPAEDUSD GBP AEDUSD GBP AEDUSD GBP AEDUSD GBP '
        self.supplier_name = 'MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS MERINA THOMAS '
        self.period = 'Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data Invoice Data '
        self.invoice_voucher_line_description = 'Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office Repairs and Maintenance - Supply & fixing of Lights in FInace Office '
        self.gl_description = 'TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified TECOM Investments FZ LLC.Unspecified.Accounts Payable - Non Project.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified.Unspecified '



        # print ('currency_code=', d.currency_code)
        # print ('payment_terms=' , d.payment_terms)
        # print ('invoice_number=' + d.invoice_number)
        # print ('invoice_voucher_header_description=', d.invoice_voucher_header_description)
        # print ('invoice_voucher_line_description=', d.invoice_voucher_line_description)
        # print ('supplier_code=', d.supplier_code)
        # print ('supplier_name=', d.supplier_name)
        # print ('supplier_address_1=', d.supplier_address_1)
        # print ('supplier_address_2=', d.supplier_address_2)
        # print ('city=', d.city)
        # print ('country=', d.country)
        # print ('gl_number=', d.gl_number)
        # print ('gl_description=', d.gl_description)
        # print ('cost_centre_code=', d.cost_centre_code)
        # print ('cost_centre_description=', d.cost_centre_description)
        # print ('company_code=', d.company_code)
        # print ('company_description=', d.company_description)
        # print ('material_code=', d.material_code)
        # print ('material_description=', d.material_description)
        # print ('material_group_code=', d.material_group_code)
        # print ('material_group_description=', d.material_group_description)
        # print ('tax_code=', d.tax_code)
        # print ('tax_description=', d.tax_description)
        # print ('period=', d.period)
        # print ('po_number=', d.po_number)
        # print ('po_creator_code=', d.po_creator_code)
        # print ('po_creator_description=', d.po_creator_description)
        # print ('po_currency_code=', d.po_currency_code)
        # print ('po_header_description=', d.po_header_description)
        # print ('po_line_description=', d.po_line_description)
        # print ('po_line_unit_of_measure=', d.po_line_unit_of_measure)
        # print ('pr_number=', d.pr_number)
        # print ('pr_creator=', d.pr_creator)
        # print ('pr_header_description=', d.pr_header_description)
        # print ('pr_line_description=', d.pr_line_description)
        # print ('pr_unit_of_measure=', d.pr_unit_of_measure)
        # print ('po_receipt_qty=', d.po_receipt_qty)
        # print ('gl_code=', d.gl_code)
        # print ('requestor_name=', d.requestor_name)
        # print ('business_unit=', d.business_unit)
        # print ('discount_terms=', d.discount_terms)
        # print ('discounts_received=', d.discounts_received)
        # print ('vendor_group=', d.vendor_group)
        # print ('s80_20=', d.s80_20)
        # print ('price_variance_percent=', d.price_variance_percent)
