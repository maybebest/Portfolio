import factory
from vitesse_prod.apps.db.models import User, Company, DeliveryLocation, Country, City, Measurement, \
    Category, Product, ProductAttribute, ProductMeasurementGroup, ProductMeasurement, NLPProductAttribute, ProductAttributeValueThrough, ProductAttributeValue
import string
import random

class MeasurementFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Measurement
        #django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: 'UOM_{0}'.format(n))


class CompanyFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Company

    name = factory.Sequence(lambda n: "Company_{0}".format(n))


class UserFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = User

    email = factory.Sequence(lambda n: "user_{0}@example.com".format(n))
    name = factory.Faker("name")
    password = factory.PostGenerationMethodCall('set_password', 'admin')
    is_active = True
    is_superuser = False
    #role = User.APP_USER
    role = User.APP_USER
    #company = factory.SubFactory(CompanyFactory)


class CountryFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Country

    name = factory.Sequence(lambda n: "Country_{0}".format(n))


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = City

    name = factory.Sequence(lambda n: "City_{0}".format(n))
    country = factory.SubFactory(CountryFactory)


class DeliveryLocationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = DeliveryLocation

    name = factory.Sequence(lambda n: "Delivery location_{0}".format(n))
    address = factory.Faker("street_name")
    country = factory.SubFactory(CountryFactory)
    city = factory.SubFactory(CityFactory)
    company = factory.SubFactory(CompanyFactory)
    creator = factory.SubFactory(UserFactory)


class CategoryFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Category

    name = factory.Sequence(lambda n: "Category_{0}".format(n))


class ProductMeasurementGroupFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ProductMeasurementGroup

    title = factory.Sequence(lambda n: "Measurement Group {0}".format(n))


class ProductMeasurementFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ProductMeasurement

    title = factory.Sequence(lambda n: "Measurement_{0}".format(n))
    group = factory.SubFactory(ProductMeasurementGroup)


class ProductAttributeFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ProductAttribute

    title = factory.Sequence(lambda n: "Attribute_{0}".format(n))
    is_custom = False
    #measurements = factory.SubFactory(ProductMeasurementGroupFactory)
    #measurement_items = factory.SubFactory(ProductMeasurementFactory)

    @factory.post_generation
    def measurements(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for measurement in extracted:
                self.measurements.add(measurement)

    @factory.post_generation
    def measurement_items(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for measurement_item in extracted:
                self.measurement_items.add(measurement_item)


class ProductFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Product

    title = factory.Sequence(lambda n: "Product_{0}".format(n))
    #attributes = factory.SubFactory(ProductAttributeFactory)

    category = factory.SubFactory(CategoryFactory)

    @factory.post_generation
    def attributes(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for attribute in extracted:
                self.attributes.add(attribute)


class NLPProductAttributeFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = NLPProductAttribute

    product = factory.SubFactory(ProductFactory)
    attribute = factory.SubFactory(ProductAttributeFactory)


class ProductAttributeValueFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ProductAttributeValue

    value = factory.Sequence(lambda n: "attr_value_{0}".format(n))
    is_manual = False
    product_attribute = factory.SubFactory(ProductAttributeFactory)


class ProductAttributeValueThroughFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = ProductAttributeValueThrough

    product = factory.SubFactory(ProductFactory)
    attribute = factory.SubFactory(ProductAttributeFactory)
    value = factory.SubFactory(ProductAttributeValueFactory)