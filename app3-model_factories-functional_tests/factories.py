import factory
import random
from datetime import date

year = random.choice(range(1900, 2019))
month = random.choice(range(1, 13))
day = random.choice(range(1, 29))
random_date = date(year, month, day)


def watch_attribute_fabric_factory(model_name, field_name):
    class Meta:
        model = f'watches.{model_name}'

    field_value = factory.sequence(lambda n: f'{field_name}_{n}')

    return type(model_name, (factory.django.DjangoModelFactory, ), {
        field_name: field_value,
        'Meta': Meta
    })


GenderFactory = watch_attribute_fabric_factory('Gender', 'gender')

BrandFactory = watch_attribute_fabric_factory('Brand', 'name')

CertificationFactory = watch_attribute_fabric_factory('Certification',
                                                      'certification')

ClaspFactory = watch_attribute_fabric_factory('Clasp', 'clasp')

ClaspMaterialFactory = watch_attribute_fabric_factory('ClaspMaterial',
                                                      'material')

BandColorFactory = watch_attribute_fabric_factory('BandColor', 'color')

BandMaterialFactory = watch_attribute_fabric_factory('BandMaterial',
                                                     'material')

CaseBackFactory = watch_attribute_fabric_factory('CaseBack', 'back')

CaseBezelFactory = watch_attribute_fabric_factory('CaseBezel', 'bezel')

CaseFrontCrystalFactory = watch_attribute_fabric_factory(
    'CaseFrontCrystal', 'front_crystal')

CaseMaterialFactory = watch_attribute_fabric_factory('CaseMaterial',
                                                     'material')

CaseShapeFactory = watch_attribute_fabric_factory('CaseShape', 'shape')

MovementAssemblyFactory = watch_attribute_fabric_factory(
    'MovementAssembly', 'assembly')

MovementNameFactory = watch_attribute_fabric_factory('MovementName', 'name')

DialColorFactory = watch_attribute_fabric_factory('DialColor', 'color')

DialIndexFactory = watch_attribute_fabric_factory('DialIndex', 'index')

DialFinishFactory = watch_attribute_fabric_factory('DialFinish', 'finish')

DialHandsFactory = watch_attribute_fabric_factory('DialHands', 'hands')


class DiscountFactory(factory.django.DjangoModelFactory):
    value = factory.sequence(lambda _: random.randint(10, 100))
    is_active = True

    class Meta:
        model = 'watches.Discount'


class FamilyFactory(factory.django.DjangoModelFactory):
    name = factory.sequence(lambda n: f'family_{n}')
    description = factory.sequence(lambda n: f'family_description_{n}')

    class Meta:
        model = 'watches.Family'


class WatchFactory(factory.django.DjangoModelFactory):

    model = factory.sequence(lambda n: f'model_{n}')
    reference = factory.sequence(lambda n: f'ref_number_{n}')
    caliber = factory.sequence(lambda n: f'caliber_{n}')
    power_reserve = factory.sequence(lambda _: random.randint(1, 100))
    production_year = random_date
    retails_price = factory.sequence(lambda n: n)
    tourbillon = factory.sequence(lambda n: f'tourbillon_{n}')
    limitation = factory.sequence(lambda _: random.randint(1, 100))
    preview_image = 'img'
    water_resistance = factory.sequence(lambda _: random.randint(1, 100))
    slug = factory.sequence(lambda n: f'watch-slug-{n}')

    certification = factory.SubFactory(CertificationFactory)

    gender = factory.SubFactory(GenderFactory)
    clasp = factory.SubFactory(ClaspFactory)
    clasp_material = factory.SubFactory(ClaspMaterialFactory)

    case_height = factory.sequence(lambda _: random.randint(1, 100))
    case_diameter = factory.sequence(lambda _: random.randint(1, 100))
    case_back = factory.SubFactory(CaseBackFactory)
    case_bezel = factory.SubFactory(CaseBezelFactory)
    case_front_crystal = factory.SubFactory(CaseFrontCrystalFactory)
    case_material = factory.SubFactory(CaseMaterialFactory)
    case_shape = factory.SubFactory(CaseShapeFactory)

    movement_height = factory.sequence(lambda _: random.randint(1, 100))
    movement_diameter = factory.sequence(lambda _: random.randint(1, 100))
    movement_jewels = factory.sequence(lambda _: random.randint(1, 100))
    movement_name = factory.SubFactory(MovementNameFactory)
    movement_assembly = factory.SubFactory(MovementAssemblyFactory)
    movement_vph_frequency = factory.sequence(lambda _: random.randint(1, 100))
    movement_type = factory.sequence(lambda n: f'movement_type_{n}')

    dial_color = factory.SubFactory(DialColorFactory)
    dial_index = factory.SubFactory(DialIndexFactory)
    dial_finish = factory.SubFactory(DialFinishFactory)
    dial_hands = factory.SubFactory(DialHandsFactory)

    brand = factory.SubFactory(BrandFactory)
    family = factory.SubFactory(FamilyFactory)

    band_color = factory.SubFactory(BandColorFactory)
    band_material = factory.SubFactory(BandMaterialFactory)

    class Meta:
        model = 'watches.Watch'


class WatchDescriptionFactory(factory.django.DjangoModelFactory):
    watch = factory.SubFactory(WatchFactory)
    image = 'image'
    is_carousel_item = False
    description = factory.sequence(lambda n: f'watch_description_{n}')
    title = factory.sequence(lambda n: f'watch_descr_title{n}')
    subtitle = factory.sequence(lambda n: f'descr_subtitle{n}')

    class Meta:
        model = 'watches.WatchDescription'


class WatchFunctionNameFactory(factory.django.DjangoModelFactory):
    name = factory.sequence(lambda n: f'watch_func_{n}')

    class Meta:
        model = 'watches.WatchFunctionName'


class WatchFunction(factory.django.DjangoModelFactory):
    watch_function_name = factory.SubFactory(WatchFunctionNameFactory)
    watch = factory.SubFactory(WatchFactory)

    class Meta:
        model = 'watches.WatchFunction'


class WatchMovementDetailsFactory(factory.django.DjangoModelFactory):
    detail = factory.sequence(lambda n: f'movement_detail{n}')
    watch = factory.SubFactory(WatchFactory)

    class Meta:
        model = 'watches.MovementDetail'
