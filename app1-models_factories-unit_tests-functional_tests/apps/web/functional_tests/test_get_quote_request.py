import time
from vitesse_prod.apps.web.selenium_test.selenium_base_class import SeleniumBaseClass
from vitesse_prod.apps.web.selenium_test.selenium_factories import MeasurementFactory, CompanyFactory, UserFactory, \
    CountryFactory, DeliveryLocationFactory, CategoryFactory, ProductAttributeFactory, ProductFactory, \
    NLPProductAttributeFactory, ProductAttributeValueFactory, ProductAttributeValueThroughFactory, CityFactory

from vitesse_prod.apps.db.models import User, Company, DeliveryLocation, Country, City, \
    Measurement, Category, Product, ProductAttribute, NLPProductAttribute, ProductAttributeValue, ProductAttributeValueThrough


class TestNew(SeleniumBaseClass):

    def test_new(self):
        uom = MeasurementFactory.create_batch(5)

        company = CompanyFactory()

        user = UserFactory(email="ggglol@mail.com", company=company)

        country = CountryFactory()

        city = CityFactory(country=country)

        delivery_location = DeliveryLocationFactory.create_batch(5, company=company, creator=user, country=country, city=city)

        category = CategoryFactory.create_batch(5)

        attr = ProductAttributeFactory()

        product = ProductFactory.create(attributes=(attr,), category=category[0])

        nlp = NLPProductAttributeFactory(product=product, attribute=attr)

        prod_att_value = ProductAttributeValueFactory(product_attribute=attr)

        prod_attr_value_through = ProductAttributeValueThroughFactory(product=product, attribute=attr, value=prod_att_value)

        for attribute in ProductAttribute.objects.all():
            attribute.nlp_rules()

        for product in Product.objects.all():
            for attribute in product.attributes.all():
                nlp_rule, _ = NLPProductAttribute.objects.get_or_create(product=product, attribute=attribute)
                nlp_rule.nlp_rules()
	# Check that all models initialized correctly without unwanted instances
        print(Measurement.objects.all())
        print(Company.objects.all())
        print(Category.objects.all())
        print(ProductAttribute.objects.all())
        print(Product.objects.all())
        print(NLPProductAttribute.objects.all())
        print(ProductAttributeValue.objects.all())
        print(ProductAttributeValueThrough.objects.all())
        print(DeliveryLocation.objects.all())
        print(User.objects.all())
        print(Country.objects.all())

        self.driver.get(self.url_login)
        self.driver.find_element_by_id("exampleInputEmail1").send_keys("ggglol@mail.com")
        self.driver.find_element_by_id("exampleInputPassword1").send_keys(("admin"))
        self.driver.find_element_by_xpath("//input[@onclick='loginProcess();']").click()
