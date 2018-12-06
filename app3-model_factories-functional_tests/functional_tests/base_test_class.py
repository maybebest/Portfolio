from selenium import webdriver
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from chronowiz.watches.tests.factories import WatchFactory, \
    WatchDescriptionFactory, FamilyFactory, WatchFunction, BrandFactory


class BaseClass(StaticLiveServerTestCase):

    def setUp(self):
        self.driver = webdriver.Firefox()
        self.base_url = self.live_server_url

        self.watch = WatchFactory()
        self.description = WatchDescriptionFactory(watch=self.watch)
        self.function = WatchFunction(watch=self.watch)
        self.family = FamilyFactory()
        self.brand = BrandFactory()
        self.driver.implicitly_wait(2)

        self.url_watch = '{}/watches/{}'\
            .format(self.base_url, self.watch.slug)
        self.url_watch_admin = '{}/admin/watches/watch/'.format(self.base_url)
        self.url_collection = '{}/collections/{}'\
            .format(self.base_url, self.watch.family.slug)
        self.url_brand = '{}/brands/{}'\
            .format(self.base_url, self.watch.brand.slug)

        self.water_resistance ='to {} atm'.format(self.watch.water_resistance)
        self.watch_attributes = [

            self.watch.case_back.back, self.watch.case_diameter,
            self.watch.case_shape.shape,

            self.watch.reference,

            self.watch.movement_name.name, self.watch.movement_type,
            self.watch.movement_diameter,

            self.watch.case_material.material, self.watch.band_material.material,
            self.watch.gender, self.watch.production_year.year,

            self.watch.movement_name.name, self.watch.movement_type,
            self.watch.movement_diameter,

            self.watch.caliber, self.function.watch_function_name.name,
            self.watch.power_reserve, self.watch.movement_jewels,
            self.watch.movement_vph_frequency,

            self.watch.case_material.material, self.watch.case_diameter,
            self.water_resistance, self.watch.case_bezel.bezel,
            self.watch.case_front_crystal.front_crystal,

            self.watch.certification.certification,

            self.watch.band_material.material, self.watch.band_color.color,
            self.watch.clasp.clasp, self.watch.clasp_material.material,

            self.watch.dial_color.color, self.watch.dial_finish.finish,
            self.watch.dial_index.index, self.watch.dial_hands.hands,
            ]

    def tearDown(self):
        self.driver.quit()

    def create_watches(self):
        self.list_of_watches = []
        for index in range(13):
            index = WatchFactory(family=self.family)
            self.list_of_watches.append(index)
