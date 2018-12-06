from django.db import models
from django.contrib.auth import get_user_model

from chronowiz.watches.managers import WatchManager
# from .watch_attributes import *
# from .case import *
# from .dial import *

User = get_user_model()

SLUG_HELP_TEXT = 'Identifier used in url'


class Gender(models.Model):
    gender = models.CharField(max_length=6, unique=True)

    def __str__(self):
        return self.gender


def watch_foreign_key_field_factory(relation_model_name):
    return models.ForeignKey(
        relation_model_name,
        related_name='watches',
        on_delete=models.SET_NULL,
        null=True)


class Watch(models.Model):

    model = models.CharField(max_length=100)
    reference = models.CharField(max_length=100)
    caliber = models.CharField(max_length=100)
    caliber_type = models.CharField(null=True, max_length=100)
    power_reserve = models.PositiveIntegerField(help_text='Hours')
    production_year = models.DateField(help_text='')
    retails_price = models.PositiveIntegerField()
    tourbillon = models.CharField(max_length=100)
    limitation = models.PositiveIntegerField(
        blank=True, null=True, help_text='pcs')
    preview_image = models.ImageField(upload_to='watch_previews')
    water_resistance = models.PositiveIntegerField(help_text='atm')
    slug = models.SlugField(
        unique=True, help_text=SLUG_HELP_TEXT, max_length=100)

    certification = watch_foreign_key_field_factory('Certification')

    clasp = watch_foreign_key_field_factory('Clasp')
    clasp_material = watch_foreign_key_field_factory('ClaspMaterial')

    case_height = models.FloatField(help_text='mm')
    case_diameter = models.FloatField(help_text='mm')

    gender = watch_foreign_key_field_factory('Gender')
    case_back = watch_foreign_key_field_factory('CaseBack')
    case_bezel = watch_foreign_key_field_factory('CaseBezel')
    case_front_crystal = watch_foreign_key_field_factory('CaseFrontCrystal')
    case_material = watch_foreign_key_field_factory('CaseMaterial')
    case_shape = watch_foreign_key_field_factory('CaseShape')

    movement_type = models.CharField(max_length=100)
    movement_height = models.FloatField()
    movement_diameter = models.FloatField()
    movement_jewels = models.PositiveIntegerField()
    movement_name = watch_foreign_key_field_factory('MovementName')
    movement_assembly = watch_foreign_key_field_factory('MovementAssembly')
    movement_vph_frequency = models.PositiveIntegerField()

    dial_color = watch_foreign_key_field_factory('DialColor')
    dial_index = watch_foreign_key_field_factory('DialIndex')
    dial_finish = watch_foreign_key_field_factory('DialFinish')
    dial_hands = watch_foreign_key_field_factory('DialHands')

    brand = watch_foreign_key_field_factory('Brand')
    family = watch_foreign_key_field_factory('Family')

    band_color = watch_foreign_key_field_factory('BandColor')
    band_material = watch_foreign_key_field_factory('BandMaterial')

    retailers = models.ManyToManyField(User, through='watches.RetailerWatchInfo')

    class Meta:
        verbose_name_plural = 'Watches'

    objects = WatchManager()

    def __str__(self):
        return self.model

    def get_available_discounts(self):
        return self.brand.discounts.filter(is_active=True)

    def get_absolute_url(self):
        return f'/watches/{self.slug}'
