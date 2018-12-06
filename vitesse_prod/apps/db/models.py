from __future__ import unicode_literals
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, Group
)
from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models
from django.db.models import Q, F, Count, Case, When, Value
from django.conf import settings
from django.utils.encoding import python_2_unicode_compatible
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

# EXTENDING DATETIME LOOKUPS
from django.conf import settings
from django.db.models.fields import DateField, DateTimeField, IntegerField, TimeField
from django.db.models.functions import Func, Lower
from django.db.models.lookups import Transform
from django.utils import timezone
from django.utils.functional import cached_property
from django.contrib.humanize.templatetags.humanize import intcomma

from .managers import UserManager

from easy_thumbnails.files import get_thumbnailer

import math
import hashlib
import datetime
import pytz
import json
import urllib2
import requests


class Now(Func):
    template = 'CURRENT_TIMESTAMP'

    def __init__(self, output_field=None, **extra):
        if output_field is None:
            output_field = DateTimeField()
        super(Now, self).__init__(output_field=output_field, **extra)

    def as_postgresql(self, compiler, connection):
        # Postgres' CURRENT_TIMESTAMP means "the time at the start of the
        # transaction". We use STATEMENT_TIMESTAMP to be cross-compatible with
        # other databases.
        self.template = 'STATEMENT_TIMESTAMP()'
        return self.as_sql(compiler, connection)


class DateTransform(Transform):
    def as_sql(self, compiler, connection):
        sql, params = compiler.compile(self.lhs)
        lhs_output_field = self.lhs.output_field
        if isinstance(lhs_output_field, DateTimeField):
            tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None
            sql, tz_params = connection.ops.datetime_extract_sql(self.lookup_name, sql, tzname)
            params.extend(tz_params)
        elif isinstance(lhs_output_field, DateField):
            sql = connection.ops.date_extract_sql(self.lookup_name, sql)
        elif isinstance(lhs_output_field, TimeField):
            sql = connection.ops.time_extract_sql(self.lookup_name, sql)
        else:
            raise ValueError('DateTransform only valid on Date/Time/DateTimeFields')
        return sql, params

    @cached_property
    def output_field(self):
        return IntegerField()


@DateTimeField.register_lookup
class WeekTransform(DateTransform):
    lookup_name = 'week'
    bilateral = True


class Misc(models.Model):

    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True


class HasCompany(models.Model):

    company = models.ForeignKey('Company')

    class Meta:
        abstract = True


class User(AbstractBaseUser, PermissionsMixin):

    MANAGER = 1
    BUYER = 2
    SPONSOR = 3
    APP_USER = 4

    ROLE_CHOICES = (
        (MANAGER, 'Manager'),
        (BUYER, 'Buyer'),
        (SPONSOR, 'Admin User'),
        (APP_USER, 'App User')
    )

    SPONSOR_ROLE_CHOICES = (
        (SPONSOR, 'Sponsor'),
        (APP_USER, 'App User')
    )

    semi_admins = [MANAGER, BUYER, SPONSOR]

    REGISTRATION_TYPE_INVITED = 1
    REGISTRATION_TYPE_REGISTERED = 2
    REGISTRATION_TYPE_DECLINED = 3

    REGISTRATION_TYPE_CHOICES = (
        (REGISTRATION_TYPE_INVITED, 'Invited'),
        (REGISTRATION_TYPE_REGISTERED, 'Joined'),
        (REGISTRATION_TYPE_DECLINED, 'Declined')
    )

    email = models.EmailField(max_length=200, unique=True)
    name = models.CharField(max_length=200)
    surname = models.CharField(max_length=255, blank=True, default='')
    title = models.CharField(max_length=255, blank=True, default='')

    office_phone = models.CharField(max_length=200, null=True, blank=True, default='')
    mobile_phone = models.CharField(max_length=200, null=True, blank=True, default='')
    assistant_phone = models.CharField(max_length=200, null=True, blank=True, default='')

    shortcut = models.CharField(max_length=255, blank=True, default='receipt')

    role = models.SmallIntegerField(choices=ROLE_CHOICES, default=APP_USER)
    registration_type = models.SmallIntegerField(choices=REGISTRATION_TYPE_CHOICES, default=REGISTRATION_TYPE_REGISTERED)
    is_active = models.BooleanField(default=True)
    date_registered = models.DateTimeField(auto_now_add=True)
    department = models.ForeignKey('Department', null=True, blank=True, related_name='department_users', on_delete=models.SET_NULL)
    company = models.ForeignKey('Company', null=True, blank=True, related_name='company_users', on_delete=models.SET_NULL)
    default_delivery_location = models.ForeignKey('DeliveryLocation', null=True, blank=True, on_delete=models.SET_NULL)
    default_currency = models.ForeignKey('Currency', null=True, blank=True, on_delete=models.SET_NULL)
    default_region = models.ForeignKey('Region', null=True, blank=True, on_delete=models.SET_NULL)
    authorizer = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL, related_name='authorizer_app_users')
    authorization_level = models.ForeignKey('AuthorizationLevel', null=True, blank=True, on_delete=models.SET_NULL)
    buyer_regions = models.ManyToManyField('Region', blank=True, related_name='region_users')
    buyer_companies = models.ManyToManyField('Company', blank=True)
    buyer_categories = models.ManyToManyField('Category', blank=True, related_name='category_buyers')
    buyer_subcategories = models.ManyToManyField('Subcategory', blank=True, related_name='subcategory_buyers')
    # quotes = models.IntegerField(default=0)
    accepted_quotes = models.IntegerField(default=0)

    braintree_customer_id = models.CharField(max_length=255, default='', blank=True)
    stripe_customer_id = models.CharField(max_length=255, default='', blank=True)
    logins_count = models.IntegerField(default=0)
    credit_cards_count = models.IntegerField(default=0)
    hotel_preferences = models.TextField(default='{"max_cost_per_night": "", "min_star_rating": "3"}')
    last_action_date = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.email)

    def has_perms(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.role == User.MANAGER

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.name, self.surname)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.name

    @property
    def all_phones(self):

        phones = []
        if self.office_phone:
            phones.append(self.office_phone)

        if self.mobile_phone:
            phones.append(self.mobile_phone)

        if self.assistant_phone:
            phones.append(self.assistant_phone)

        return ', '.join(phones)

    @property
    def all_regions(self):

        return ', '.join(self.buyer_regions.all().values_list('name', flat=True))

    @property
    def unread_notifications_count(self):

        count = 0
        if UserUnreadActivityNotificationsCount.objects.filter(user=self).exists():
            count = UserUnreadActivityNotificationsCount.objects.filter(user=self).first().count

        return count

    def set_unread_notifications_count(self, count):

        obj, is_created = UserUnreadActivityNotificationsCount.objects.get_or_create(user=self)

        # If string (i.e. '-1' | '+1' | '-2') do the math else set the value
        if isinstance(count, basestring):
            obj.count += + int(count)
        else:
            obj.count = count

        # Avoid negative value
        if obj.count < 0:
            obj.count = 0

        obj.save(update_fields=['count'])

        return obj.count

    def save(self, *args, **kwargs):

        if not self.name:
            self.name = self.get_role_display()

        if not self.default_currency:
            self.default_currency = Currency.objects.all().first()

        if not self.default_region:
            self.default_region = Region.objects.all().order_by('is_default').first()

        super(User, self).save(*args, **kwargs)

    def get_api_report_filters(self):

        expenses_type, is_created = UserAPIAnalyticsType.objects.get_or_create(
            command="expenses", defaults={'label': 'Expenses', 'command': 'expenses'}
        )
        expenses_time, is_created = UserAPIAnalyticsTime.objects.get_or_create(
            command="current_quarter", defaults={'label': 'Current Quarter', 'command': 'current_quarter'}
        )

        user_filter, is_created = UserAPIAnalyticsFilters.objects.get_or_create(user=self, defaults={
            'user': self,
            'type': expenses_type,
            'time': expenses_time,
            'currency': self.default_currency,
            'user_ids': json.dumps([self.id])
        })

        return user_filter

    def get_api_home_filter(self):

        expenses_time, is_created = UserAPIAnalyticsTime.objects.get_or_create(
            command="current_quarter", defaults={'label': 'Current Quarter', 'command': 'current_quarter'}
        )

        user_filter, is_created = UserAPIAnalyticsLocalFilters.objects.get_or_create(user=self, defaults={
            'user': self,
            'time': expenses_time
        })

        return user_filter

    def get_profile_completion_percent(self):

        all_fields_str = [
            'name',
            'surname',
            'email',
            'title',
            'office_phone',
            'mobile_phone',
            'assistant_phone'
        ]

        all_fields_fk = [
            'default_region',
            'default_currency',
            'company'
        ]

        all_fields = all_fields_str + all_fields_fk

        fields_filled_out = 0
        for field in all_fields:

            if field in all_fields_str:
                if getattr(self, field):
                    fields_filled_out += 1

            if field in all_fields_fk:
                if getattr(self, field):
                    if getattr(getattr(self, field), 'name'):
                        fields_filled_out += 1

        return "%0.1f" % (fields_filled_out / float(len(all_fields)) * 100)

    def has_catalog_items(self):
        return CatalogItem.objects.filter(catalog__users=self).exists()


class UserUnreadActivityNotificationsCount(models.Model):

    user = models.OneToOneField('User', related_name='unread_notifications')
    count = models.IntegerField(default=0)

    def __unicode__(self):
        return '%s. Count: %i' % (self.user, self.count)


class UserInvitationToken(models.Model):

    user = models.ForeignKey('User', related_name='user_invitation_tokens')
    user_to = models.ForeignKey('User', related_name='user_to_invitation_tokens')
    hash = models.TextField(unique=True)
    data = models.TextField(default='{}')

    # Set to False if user_to declined the request
    is_active = models.BooleanField(default=True)

    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s.' % (self.id, self.user.name, )

    def save(self, *args, **kwargs):

        from vitesse_prod.apps.general_functions.functions import generate_user_invitation_token
        if not self.hash:
            self.hash = generate_user_invitation_token()

        super(UserInvitationToken, self).save(*args, **kwargs)

    @property
    def is_valid(self):

        duration_in_mins = 60 * 24

        return self.date_created + datetime.timedelta(minutes=duration_in_mins) > datetime.datetime.utcnow().replace(tzinfo=pytz.utc) or not self.is_active


class UserSetupAccountToken(models.Model):

    user_to = models.ForeignKey('User', related_name='user_to_account_setup_tokens')
    hash = models.TextField(unique=True)
    is_active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s.' % (self.id, self.user_to.name, )

    def save(self, *args, **kwargs):
        from vitesse_prod.apps.general_functions.functions import generate_user_account_setup_token
        if not self.hash:
            self.hash = generate_user_account_setup_token()

        super(UserSetupAccountToken, self).save(*args, **kwargs)

    @property
    def is_valid(self):
        duration_in_mins = 60 * 24

        # return self.date_created + datetime.timedelta(minutes=duration_in_mins) > datetime.datetime.utcnow().replace(
        #     tzinfo=pytz.utc) or not self.is_active

        # Ignore token alive time from now due to ticket

        return self.is_active


class Department(models.Model):

    name = models.CharField(max_length=255)
    company = models.ForeignKey('Company')

    class Meta:
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class Company(models.Model):
    from vitesse_prod.apps.general_functions.functions import set_file_name

    name = models.CharField(max_length=255, blank=True, default='')
    is_standalone = models.BooleanField(default=False)

    high_expense_limit_currency = models.ForeignKey('Currency', blank=True, null=True)
    high_expense_limit_value = models.FloatField(default=300)
    # suppliers = models.ManyToManyField('Supplier', blank=True, related_name='supplier_companies')
    terms_n_conditions = models.FileField(upload_to=set_file_name, max_length=255, blank=True, default='')

    class Meta:
        verbose_name = _('company')
        verbose_name_plural = _('companies')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)

    def get_owner(self):

        if self.is_standalone:
            return User.objects.filter(role=User.APP_USER, company=self).first()
        else:
            return User.objects.filter(role=User.SPONSOR, company=self).first()

    def get_terms_n_conditions_file_name(self):
        file_url = ''
        if self.terms_n_conditions:
            file_url = self.terms_n_conditions.name.split('/')[-1]
        return file_url

    def get_custom_email_host(self):

        from vitesse_prod.apps.general_functions.functions import get_object_or_None

        custom_email_host = None
        email_settings = get_object_or_None(CompanyEmailSettings, company=self)

        if email_settings and email_settings.host and email_settings.port and email_settings.host_user and email_settings.password:
            custom_email_host = email_settings

        return custom_email_host

    def get_quote_acceptance_justification_emails(self):

        from vitesse_prod.apps.general_functions.functions import get_object_or_None

        emails = []
        email_settings = get_object_or_None(CompanyEmailSettings, company=self)

        if email_settings:
            for email in email_settings.quote_acceptance_justification_emails.split(';'):

                if email.strip():
                    emails.append(email)

        return emails

    def get_quote_pending_recipients_emails(self):

        from vitesse_prod.apps.general_functions.functions import get_object_or_None

        emails = []
        email_settings = get_object_or_None(CompanyEmailSettings, company=self)

        if email_settings:
            for email in email_settings.quote_pending_recipients_emails.split(';'):

                if email.strip():
                    emails.append(email)

        return emails


class CompanyEmailSettings(models.Model):

    company = models.OneToOneField('Company', related_name='company_email_settings')

    host = models.CharField(max_length=255, default='', blank=True)
    port = models.IntegerField(default=None, blank=True, null=True)
    host_user = models.EmailField(max_length=255, default='', blank=True)
    password = models.CharField(max_length=255, default='', blank=True)
    use_tls = models.BooleanField(default=True, blank=True)

    quote_acceptance_justification_emails = models.TextField(default='', blank=True)
    quote_cancellation_justification_recipients_emails = models.TextField(default='', blank=True)
    quote_declined_justification_recipients_emails = models.TextField(default='', blank=True)

    quote_pending_days_limit_to_end_user = models.PositiveIntegerField(default=3, blank=True, null=True)
    quote_pending_days_limit_to_recipients = models.PositiveIntegerField(default=5, blank=True, null=True)
    quote_pending_recipients_emails = models.TextField(default='', blank=True)

    def __unicode__(self):
        return "%s" % self.company


class CompanyMediaSettings(models.Model):

    from vitesse_prod.apps.general_functions.functions import set_file_name

    company = models.OneToOneField('Company', related_name='media_settings')

    logo = models.FileField(upload_to=set_file_name, max_length=255, blank=True, null=True)

    def __unicode__(self):
        return "%s" % self.company

    def get_logo_file_name(self):
        file_url = ''
        if self.logo:
            file_url = self.logo.name.split('/')[-1]
        return file_url


class CompanyCategorySupplier(models.Model):

    company = models.ForeignKey('Company')
    category = models.ForeignKey('Category', null=True, blank=True)
    subcategory = models.ForeignKey('Subcategory', null=True, blank=True)
    supplier = models.ForeignKey('Supplier', related_name='company_category_suppliers')
    is_in_category_card = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Company Category Supplier')
        verbose_name_plural = _('Company Category Suppliers')
        unique_together = ("company", "category", "subcategory", "supplier")

    def __unicode__(self):

        strv = ''

        if self.category:
            strv = self.category.name

        elif self.subcategory:
            strv = self.subcategory.name

        return '%i. %s. %s. %s' % (self.id, self.company.name, strv, self.supplier.company_name)


class Order(HasCompany, Misc):

    from vitesse_prod.apps.general_functions.functions import set_file_name

    STATUS_NOT_SUBMITTED = 0
    STATUS_NEW = 1
    STATUS_PENDING_AUTHORIZATION = 2
    STATUS_ASSIGNED = 3
    STATUS_RECEIVED = 4
    STATUS_SOURCING = 5
    STATUS_QUOTED = 6
    STATUS_CLOSED_ACCEPTED = 7
    STATUS_CLOSED_CANCELED = 8
    STATUS_CLOSED_AUTHORIZER_DECLINED = 9
    STATUS_CLOSED_QUOTES_DECLINED = 10

    STATUS_CHOICES = (
        (STATUS_NOT_SUBMITTED, 'Buyer Returned'),
        (STATUS_NEW, 'New'),
        (STATUS_PENDING_AUTHORIZATION, 'Pending Authorization'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_SOURCING, 'Sourcing'),
        (STATUS_QUOTED, 'Quoted'),
        (STATUS_CLOSED_ACCEPTED, 'Closed Accepted'),
        (STATUS_CLOSED_CANCELED, 'Closed Canceled'),
        (STATUS_CLOSED_AUTHORIZER_DECLINED, 'Closed Authorizer Declined'),
        (STATUS_CLOSED_QUOTES_DECLINED, 'Closed Quotes Declined')
    )

    ESTIMATED_SOURCE_NONE = 0
    ESTIMATED_SOURCE_PREVIOUS_PO = 1
    ESTIMATED_SOURCE_PREVIOUS_INVOICE = 2
    ESTIMATED_SOURCE_INTERNAL_BUDGET = 3

    ESTIMATED_SOURCE_CHOICES = (
        (ESTIMATED_SOURCE_NONE, 'None'),
        (ESTIMATED_SOURCE_PREVIOUS_PO, 'Previous PO'),
        (ESTIMATED_SOURCE_PREVIOUS_INVOICE, 'Previous Invoice'),
        (ESTIMATED_SOURCE_INTERNAL_BUDGET, 'Internal Budget'),
    )

    make = models.CharField(max_length=255, default='', blank=True)
    model = models.CharField(max_length=255, default='', blank=True)
    description = models.TextField(default='', null=True, blank=True)
    raw_description = models.TextField(default='', null=True, blank=True)
    audio_description = models.FileField(upload_to=set_file_name, max_length=255, blank=True, default='')
    audio_description_duration = models.CharField(max_length=255, default='', blank=True)
    comment = models.TextField(default='', null=True, blank=True)
    date_required = models.DateTimeField(null=True, blank=True)
    tracking_number = models.CharField(max_length=255, unique=True, db_index=True, blank=True)

    app_user = models.ForeignKey('User', related_name='user_orders')
    authorizer = models.ForeignKey('User', related_name='authorizer_orders', blank=True, null=True, on_delete=models.SET_NULL)

    category = models.ForeignKey('Category', related_name='category_orders', null=True, blank=True)
    subcategory = models.ForeignKey('Subcategory', null=True, blank=True, on_delete=models.SET_NULL)
    measurement = models.ForeignKey('Measurement', null=True, blank=True)
    delivery_location = models.ForeignKey('DeliveryLocation')
    currency = models.ForeignKey('Currency')
    purchase = models.ForeignKey('Purchase', blank=True, null=True)

    suppliers = models.ManyToManyField('Supplier', blank=True)
    buyer = models.ForeignKey('User', related_name='buyer_orders', null=True, blank=True, on_delete=models.SET_NULL)

    estimated_value = models.FloatField(default=0)
    quantity = models.FloatField(default=1)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)

    # Predefined by order.description and editable by buyer on rfq
    rfq_item_description = models.TextField(default='', blank=True)

    quotes_decline_comment = models.TextField(default='', blank=True)
    cancelled_by = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)

    payment_date = models.DateTimeField(blank=True, null=True, default=None)
    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)
    date_submitted = models.DateTimeField(blank=True, null=True, default=None)
    date_assigned_to_buyer = models.DateTimeField(null=True, blank=True)
    date_status_changed = models.DateTimeField(null=True, blank=True)
    date_accepted = models.DateTimeField(null=True, blank=True)

    date_submitted_rfq = models.DateTimeField(null=True, blank=True)
    date_rfq_quoted = models.DateTimeField(null=True, blank=True)
    date_submitted_rfq_to_end_user = models.DateTimeField(null=True, blank=True)

    # Buyer creates deadline for suppliers within the order
    buyer_deadline = models.DateTimeField(null=True, blank=True)
    viewed_by_app_user = models.BooleanField(default=False)

    is_emergency_request = models.BooleanField(default=False)
    is_sample_required = models.BooleanField(default=False)
    is_exact_match_required = models.BooleanField(default=False)

    estimated_source = models.SmallIntegerField(choices=ESTIMATED_SOURCE_CHOICES, default=ESTIMATED_SOURCE_NONE, blank=True)

    # App User creates comment for buyer only
    buyer_comment = models.TextField(blank=True, default='')
    on_behalf_user = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL, related_name='on_behalf')

    is_catalog = models.BooleanField(default=False)
    tax_amount = models.FloatField(default=0)

    class Meta:
        verbose_name = _('orders')
        verbose_name_plural = _('orders')
        ordering = ["-date_created"]

    def __unicode__(self):
        return 'ID: %s. Tracking No: %s' % (str(self.id), self.tracking_number, )

    def get_main_image(self):
        return OrderFile.objects.filter(order=self).order_by('id').first()

    def get_estimated_value(self):

        if not self.estimated_value:
            return "Don't know"

        return "%s %s" % (self.currency.sign, intcomma("%.2f" % (float(self.estimated_value) / 1)))

    def get_expected_value(self):

        if not self.estimated_value:
            return "0"

        return "%s %s" % (self.currency.sign, intcomma("%.2f" % float(self.estimated_value * self.quantity)))

    def get_expected_value_clear(self):

        if not self.estimated_value:
            return "0"

        return "%.2f" % float(self.estimated_value * self.quantity)

    def get_quantity_int(self):

        return int(self.quantity)

    @property
    def full_description(self):

        description = ""

        if self.make:
            description += self.make + '. '

        if self.model:
            description += self.model + '. '

        if self.description:
            description += self.description + '.'

        if self.raw_description and self.raw_description.strip():
            description = self.raw_description.strip()

        if len(description) > 50:
            description = description[:50] + ' ...'

        return description

    @property
    def full_description_v2(self):

        description = ""

        if self.make:
            description += self.make + '. '

        if self.model:
            description += self.model + '. '

        if self.description:
            description += self.description + '.'

        return description

    @property
    def ui_status(self):

        ui_status_info = {
            'value': 'not-submitted',
            'label': 'Not Submitted'
        }

        if self.status in [Order.STATUS_NEW, Order.STATUS_PENDING_AUTHORIZATION, Order.STATUS_ASSIGNED, Order.STATUS_RECEIVED, Order.STATUS_SOURCING]:
            ui_status_info['value'] = 'submitted'
            ui_status_info['label'] = 'Submitted'

        elif self.status in [Order.STATUS_QUOTED]:
            ui_status_info['value'] = 'quoted'
            ui_status_info['label'] = 'Quoted'

            if not self.viewed_by_app_user:
                ui_status_info['label'] = 'New'

        elif self.status in [Order.STATUS_CLOSED_ACCEPTED, Order.STATUS_CLOSED_CANCELED, Order.STATUS_CLOSED_AUTHORIZER_DECLINED, Order.STATUS_CLOSED_QUOTES_DECLINED]:
            ui_status_info['value'] = 'closed'
            ui_status_info['label'] = 'Closed'

        return ui_status_info

    @property
    def rfq_count_str(self):

        rfq_count = ''
        if hasattr(self, 'quoted_rfq_count') and hasattr(self, 'total_rfq_count'):
            rfq_count = '%i/%i' % (self.quoted_rfq_count, self.total_rfq_count, )

        return rfq_count

    def get_estimated_source_choices_list(self):

        info_list = []

        for data in self.ESTIMATED_SOURCE_CHOICES:
            info_list.append({
                'id': data[0],
                'name': data[1]
            })

        return info_list

    def get_savings_amount(self):

        # The baseline spend is the amount given in the request and the savings is the difference between lowest quote and the baseline spend

        baseline = self.get_expected_value_clear()
        # lowest_quote = Quote.objects.filter(order=self).order_by('value').first()
        accepted_quote = Quote.objects.filter(order=self, accepted=True).first()
        savings_amount = None

        if accepted_quote:
            savings_amount = round(float(baseline) - accepted_quote.value * self.quantity, 2)

        return savings_amount

    @property
    def attributes(self):
        result = {}

        for attribute in ProductAttribute.objects.filter(is_custom=False):
            result[slugify(attribute.title.lower()).replace('-', '_')] = {
                'is_custom': attribute.is_custom,
                'id': attribute.id,
            }

        for value in self.order_values.all():
            if value.product_attribute.is_custom:
                result[slugify(value.product_attribute.title.lower()).replace('-', '_')] = {
                    'value': value.value,
                    'is_manual': value.is_manual,
                    'is_custom': value.product_attribute.is_custom,
                    'id': value.product_attribute.id if value.product_attribute.title != 'Item name' else -1,
                }
            else:
                result[slugify(value.product_attribute.title.lower()).replace('-', '_')].update({
                    'value': value.value,
                    'is_manual': value.is_manual,
                })
        return json.dumps(result)


class OrderImage(models.Model):

    from vitesse_prod.apps.general_functions.functions import set_file_name

    order = models.ForeignKey('Order', related_name='order_images')

    image = models.FileField(upload_to=set_file_name, max_length=255)
    thumbnail = models.FileField(upload_to=set_file_name, max_length=255, null=True, blank=True, default='')

    width = models.CharField(max_length=50, default='', blank=True)
    height = models.CharField(max_length=50, default='', blank=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.image.name)

    @property
    def file_name(self):

        file_url = ''

        if self.image:
            file_url = self.image.name.split('/')[-1]

        return file_url

    def save(self, *args, **kwargs):

        if self.image:
            from vitesse_prod.apps.general_functions.functions import rotate_image
            rotate_image(self.image)

        super(OrderImage, self).save(*args, **kwargs)

        if self.image:
            OrderImage.objects.filter(id=self.id).update(thumbnail=get_thumbnailer(self.image)['50'])


class OrderFile(models.Model):

    from vitesse_prod.apps.general_functions.functions import set_file_name

    order = models.ForeignKey('Order', related_name='order_files', blank=True, null=True,
                              on_delete=models.SET_NULL)
    order_line = models.ForeignKey('OrderLine', related_name='order_line_files', blank=True, null=True,
                                   on_delete=models.SET_NULL)
    file = models.FileField(upload_to=set_file_name, max_length=255)
    width = models.CharField(max_length=50, default='', blank=True)
    height = models.CharField(max_length=50, default='', blank=True)

    @property
    def file_name(self):

        file_url = ''

        if self.file:
            file_url = self.file.name.split('/')[-1]

        return file_url

    def __unicode__(self):
        return '%i. %s' % (self.id, self.file.name)

    def delete(self, *args, **kwargs):
        self.file.delete()
        super(OrderFile, self).delete(*args, **kwargs)


class OrderEstimatedSourceFile(models.Model):

    from vitesse_prod.apps.general_functions.functions import set_file_name

    order = models.ForeignKey('Order', related_name='order_estimated_source_files', null=True, blank=True,
                              on_delete=models.SET_NULL)
    order_line = models.ForeignKey('OrderLine', related_name='order_line_estimated_source_files', null=True, blank=True,
                                   on_delete=models.SET_NULL)
    file = models.FileField(upload_to=set_file_name, max_length=255)

    @property
    def file_name(self):
        file_url = ''
        if self.file:
            file_url = self.file.name.split('/')[-1]
        return file_url

    def __unicode__(self):
        return '%i. %s' % (self.id, self.file.name)


class OrderReturnComment(models.Model):

    DIRECTION_BUYER_TO_END_USER = 1
    DIRECTION_END_USER_TO_BUYER = 2

    DIRECTION_CHOICES = (
        (DIRECTION_BUYER_TO_END_USER, 'Buyer to End User'),
        (DIRECTION_END_USER_TO_BUYER, 'End User to Buyer'),
    )
    order = models.ForeignKey('Order', related_name='order_return_comment')
    comment = models.TextField()

    direction = models.SmallIntegerField(choices=DIRECTION_CHOICES, default=DIRECTION_BUYER_TO_END_USER)

    date_edited = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('direction', 'order',)

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.order, self.comment[:50])

    # def save(self, *args, **kwargs):
    #
    #     from vitesse_prod.apps.general_functions.functions import get_object_or_None
    #
    #     order_return_comment = get_object_or_None(OrderReturnComment, order=self.order)
    #     if order_return_comment:
    #         order_return_comment.delete()
    #
    #     super(OrderReturnComment, self).save(*args, **kwargs)


class OrderTag(models.Model):

    # VALUE_NONE = 0
    VALUE_LOW = 1
    VALUE_MEDIUM = 2
    VALUE_HIGH = 3

    VALUE_CHOICES = (
        # (VALUE_NONE, 'None'),
        (VALUE_LOW, 'Low'),
        (VALUE_MEDIUM, 'Medium'),
        (VALUE_HIGH, 'High')
    )

    order = models.OneToOneField('Order', related_name='order_tag')
    value = models.SmallIntegerField(choices=VALUE_CHOICES)

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.order, self.get_value_display())


class OrderSavings(models.Model):

    TYPE_BENCHMARK = 1
    TYPE_ESTIMATE = 2
    TYPE_AVG_OF_QUOTES = 3

    TYPE_CHOICES = (
        (TYPE_BENCHMARK, 'Benchmark'),
        (TYPE_ESTIMATE, 'Estimate'),
        (TYPE_AVG_OF_QUOTES, 'Avg. of quotes')
    )

    REALIZATION_TYPE_REALIZED = 1
    REALIZATION_TYPE_UNREALIZED = 2
    REALIZED_TYPE_CHOICES = (
        (REALIZATION_TYPE_REALIZED, 'Realized Savings'),
        (REALIZATION_TYPE_UNREALIZED, 'Unrealized Savings'),
    )

    order = models.OneToOneField('Order', related_name='order_savings')
    type = models.SmallIntegerField(choices=TYPE_CHOICES)
    baseline = models.FloatField()
    savings = models.FloatField()
    levels_applied = models.ManyToManyField('OrderSavingsLevelApplied', blank=True)
    levels_applied_text = models.TextField(default='', blank=True)
    realization_type = models.SmallIntegerField(choices=REALIZED_TYPE_CHOICES, default=REALIZATION_TYPE_REALIZED)

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.order, self.get_type_display())


class OrderSavingsLevelApplied(models.Model):

    TYPE_PRICE_NEGOTIATION = 1
    TYPE_NEW_COMPETITION = 2
    TYPE_SPECIFICATION_OPTIMIZATION = 3
    TYPE_VOLUME_BUNDLING = 4

    TYPE_CHOICES = (
        (TYPE_PRICE_NEGOTIATION, 'Price Negotiation'),
        (TYPE_NEW_COMPETITION, 'New Competition'),
        (TYPE_SPECIFICATION_OPTIMIZATION, 'Specific Optimization'),
        (TYPE_VOLUME_BUNDLING, 'Volume Bundling')
    )

    type = models.SmallIntegerField(choices=TYPE_CHOICES)

    def __unicode__(self):
        return '%s' % self.get_type_display()


class OrderLine(models.Model):

    order = models.ForeignKey('Order', null=True, blank=True)
    session_id = models.TextField(default='', blank=True)

    STATUS_NOT_SUBMITTED = 0
    STATUS_NEW = 1
    STATUS_PENDING_AUTHORIZATION = 2
    STATUS_ASSIGNED = 3
    STATUS_RECEIVED = 4
    STATUS_SOURCING = 5
    STATUS_QUOTED = 6
    STATUS_CLOSED_ACCEPTED = 7
    STATUS_CLOSED_CANCELED = 8
    STATUS_CLOSED_AUTHORIZER_DECLINED = 9
    STATUS_CLOSED_QUOTES_DECLINED = 10

    STATUS_CHOICES = (
        (STATUS_NOT_SUBMITTED, 'Buyer Returned'),
        (STATUS_NEW, 'New'),
        (STATUS_PENDING_AUTHORIZATION, 'Pending Authorization'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_SOURCING, 'Sourcing'),
        (STATUS_QUOTED, 'Quoted'),
        (STATUS_CLOSED_ACCEPTED, 'Closed Accepted'),
        (STATUS_CLOSED_CANCELED, 'Closed Canceled'),
        (STATUS_CLOSED_AUTHORIZER_DECLINED, 'Closed Authorizer Declined'),
        (STATUS_CLOSED_QUOTES_DECLINED, 'Closed Quotes Declined')
    )

    ESTIMATED_SOURCE_NONE = 0
    ESTIMATED_SOURCE_PREVIOUS_PO = 1
    ESTIMATED_SOURCE_PREVIOUS_INVOICE = 2
    ESTIMATED_SOURCE_INTERNAL_BUDGET = 3

    ESTIMATED_SOURCE_CHOICES = (
        (ESTIMATED_SOURCE_NONE, 'None'),
        (ESTIMATED_SOURCE_PREVIOUS_PO, 'Previous PO'),
        (ESTIMATED_SOURCE_PREVIOUS_INVOICE, 'Previous Invoice'),
        (ESTIMATED_SOURCE_INTERNAL_BUDGET, 'Internal Budget'),
    )

    description = models.TextField()
    comment = models.TextField(default='', null=True, blank=True)
    date_required = models.DateTimeField()
    category = models.ForeignKey('Category', related_name='category_order_lines', null=True, blank=True)
    currency = models.ForeignKey('Currency', blank=True, null=True)
    measurement = models.ForeignKey('Measurement')
    purchase = models.ForeignKey('Purchase', blank=True, null=True)
    estimated_value = models.FloatField(default=0)
    quantity = models.FloatField(default=1)
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=STATUS_NOT_SUBMITTED)
    catalog_item = models.ForeignKey('CatalogItem', null=True, blank=True, on_delete=models.SET_NULL)

    quotes_decline_comment = models.TextField(default='', blank=True)
    cancelled_by = models.ForeignKey('User', null=True, blank=True, on_delete=models.SET_NULL)

    payment_date = models.DateTimeField(blank=True, null=True, default=None)

    date_edited = models.DateTimeField(auto_now=True)
    date_submitted = models.DateTimeField(blank=True, null=True, default=None)
    date_assigned_to_buyer = models.DateTimeField(null=True, blank=True)
    date_status_changed = models.DateTimeField(null=True, blank=True)
    date_accepted = models.DateTimeField(null=True, blank=True)

    date_submitted_rfq = models.DateTimeField(null=True, blank=True)
    date_rfq_quoted = models.DateTimeField(null=True, blank=True)
    date_submitted_rfq_to_end_user = models.DateTimeField(null=True, blank=True)

    # Buyer creates deadline for suppliers within the order
    buyer_deadline = models.DateTimeField(null=True, blank=True)
    viewed_by_app_user = models.BooleanField(default=False)

    is_emergency_request = models.BooleanField(default=False)
    is_sample_required = models.BooleanField(default=False)
    is_exact_match_required = models.BooleanField(default=False)

    estimated_source = models.SmallIntegerField(choices=ESTIMATED_SOURCE_CHOICES, default=ESTIMATED_SOURCE_NONE, blank=True)

    raw_description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = _('order lines')
        verbose_name_plural = _('order lines')
        ordering = ["id"]

    def __unicode__(self):
        return 'ID: %s. Order No: %s. Session ID: %s' % (self.id, self.order_id, self.session_id,)

    def get_estimated_value(self):

        if not self.estimated_value:
            return "Don't know"

        return "%s" % (intcomma("%.2f" % (float(self.estimated_value) / 1)),)

    def get_expected_value(self):

        if not self.estimated_value:
            return "0"

        return "%s" % (intcomma("%.2f" % float(self.estimated_value * self.quantity)),)

    def get_expected_value_clear(self):

        if not self.estimated_value:
            return "0"

        total_value = self.estimated_value * self.quantity
        if self.catalog_item:
            total_value = self.estimated_value * self.quantity * (1 + float((self.catalog_item.tax_amount / 100)))

        return "%.2f" % float(total_value)

    def get_quantity_int(self):
        return int(self.quantity)

    def get_main_image(self):
        return OrderFile.objects.filter(order_line=self).order_by('id').first()

    @property
    def cutted_description(self):
        description = self.description
        if len(description) > 120:
            description = "%s ..." % description[:120]
        return description

    @property
    def attributes(self):

        return json.dumps(self.raw_attributes)

    @property
    def raw_attributes(self):
        result = {}
        for attribute in ProductAttribute.objects.filter(is_custom=False):
            result[slugify(attribute.title.lower()).replace('-', '_')] = {
                'is_custom': attribute.is_custom,
                'id': attribute.id,
            }

        for value in self.order_line_values.all():
            if value.product_attribute.is_custom:
                result[slugify(value.product_attribute.title.lower()).replace('-', '_')] = {
                    'value': value.value,
                    'is_manual': value.is_manual,
                    'is_custom': value.product_attribute.is_custom,
                    'id': value.product_attribute.id,
                }
            else:
                result[slugify(value.product_attribute.title.lower()).replace('-', '_')].update({
                    'value': value.value,
                    'is_manual': value.is_manual,
                })
        # return json.dumps(result)
        return result


class Quote(models.Model):

    order = models.ForeignKey('Order', related_name='order_quotes')
    supplier = models.ForeignKey('Supplier', related_name='supplier_quotes', null=True, blank=True)
    supplier_name = models.CharField(max_length=255, default='', blank=True)
    value = models.FloatField(default=0)
    link = models.TextField(default='', null=True, blank=True)
    description = models.TextField(default='', null=True, blank=True)
    justification = models.TextField(default='', null=True, blank=True)

    comment = models.TextField(default='', blank=True)

    exact_match = models.BooleanField(default=False)
    accepted = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)

    rank = models.IntegerField(default=1)

    supplier_quote = models.ForeignKey('SupplierQuote', null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.description[:200])

    @property
    def value_total(self):
        return round(self.value * self.order.quantity, 2)

    @property
    def total_value_gbp(self):
        from vitesse_prod.apps.general_functions.functions import get_currency_rate
        return self.value_total * get_currency_rate(self.order.currency.name)

    @property
    def total_value_gbp_int(self):
        return int(self.total_value_gbp * 100)

    def is_cheapest(self):
        return self.value == Quote.objects.filter(order=self.order).order_by('value')[0].value


class QuoteRecommendation(models.Model):

    quote = models.OneToOneField('Quote', related_name='quote_recommendation')
    comment = models.TextField(default='', blank=True)

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.quote, self.comment)


class QuoteFile(models.Model):
    from vitesse_prod.apps.general_functions.functions import set_file_name

    quote = models.ForeignKey('Quote', related_name='quote_files')
    file = models.FileField(upload_to=set_file_name, max_length=255, default='', blank=True)

    @property
    def file_name(self):
        file_name_str = ''
        if self.file:
            file_name_str = self.file.name.split('/')[-1]
        return file_name_str

    @property
    def file_url(self):
        file_url_str = ''
        if self.file:
            file_url_str = self.file.url
        return file_url_str

    def __unicode__(self):
        return '%s. %s' % (self.quote, self.file)


class QuoteSupportingDocument(models.Model):
    from vitesse_prod.apps.general_functions.functions import set_file_name

    quote = models.ForeignKey('Quote', related_name='quote_supporting_documents')
    file = models.FileField(upload_to=set_file_name, max_length=255, default='', blank=True)

    @property
    def file_name(self):
        file_name_str = ''
        if self.file:
            file_name_str = self.file.name.split('/')[-1]
        return file_name_str

    @property
    def file_url(self):
        file_url_str = ''
        if self.file:
            file_url_str = self.file.url
        return file_url_str

    def __unicode__(self):
        return '%s. %s' % (self.quote, self.file)


class SupplierQuote(models.Model):

    from vitesse_prod.apps.general_functions.functions import set_file_name

    SUPPLIER_PROCESS_STATUS_NOT_SUBMITTED = 0
    SUPPLIER_PROCESS_STATUS_NOT_OPEN = 1
    SUPPLIER_PROCESS_STATUS_OPEN = 2
    SUPPLIER_PROCESS_STATUS_QUOTED = 3
    SUPPLIER_PROCESS_STATUS_ACCEPTED = 4

    SUPPLIER_PROCESS_STATUS_CHOICES = (
        (SUPPLIER_PROCESS_STATUS_NOT_SUBMITTED, 'Not Submitted'),
        (SUPPLIER_PROCESS_STATUS_NOT_OPEN, 'Not Open'),
        (SUPPLIER_PROCESS_STATUS_OPEN, 'Open'),
        (SUPPLIER_PROCESS_STATUS_QUOTED, 'Quoted'),
        (SUPPLIER_PROCESS_STATUS_ACCEPTED, 'Accepted'),
    )

    order = models.ForeignKey('Order', related_name='order_supplier_quotes')
    supplier = models.ForeignKey('Supplier', related_name='supplier_supplier_quotes')

    item_description = models.TextField(default='', blank=True)

    header_info = models.TextField(default='', null=True, blank=True)
    supplier_header_info = models.TextField(default='', null=True, blank=True)
    buyer_description = models.TextField(default='', null=True, blank=True)

    value = models.FloatField(default=0)
    supplier_description = models.TextField(default='', null=True, blank=True)
    supplier_delivery_date = models.DateTimeField(blank=True, null=True)
    attachment = models.FileField(upload_to=set_file_name, max_length=255, blank=True, default='')

    # is_accepted = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)

    supplier_process_status = models.IntegerField(default=SUPPLIER_PROCESS_STATUS_NOT_SUBMITTED, choices=SUPPLIER_PROCESS_STATUS_CHOICES)

    rank = models.IntegerField(default=1)
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    date_received = models.DateTimeField(null=True, blank=True)
    date_quoted = models.DateTimeField(null=True, blank=True)

    is_attachments_processed_by_buyer = models.BooleanField(default=False)
    exact_match_provided = models.BooleanField(default=False)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.order)

    def save(self, *args, **kwargs):

        if not self.date_created:
            self.date_created = datetime.datetime.utcnow()

        if self.header_info:
            templates = {
                '[VENDOR NAME]': self.supplier.company_name,
                '[COMPANY]': self.order.company.name,
                '[BUYER EMAIL]': self.order.buyer.email
            }

            supplier_header_info = self.header_info

            for template, value in templates.items():
                supplier_header_info = supplier_header_info.replace(template, value)

            self.supplier_header_info = supplier_header_info

        super(SupplierQuote, self).save(*args, **kwargs)

    @property
    def value_total(self):
        return round(self.value * self.order.quantity, 2)

    @property
    def total_value_gbp(self):
        from vitesse_prod.apps.general_functions.functions import get_currency_rate
        return self.value_total * get_currency_rate(self.order.currency.name)

    @property
    def total_value_gbp_int(self):
        return int(self.total_value_gbp * 100)

    def get_rfq_token(self):
        token, is_created = SupplierQuoteToken.objects.get_or_create(supplier_quote=self)
        token.is_active = True
        token.save()
        return token

    @property
    def is_requotable(self):
        return self.supplier_process_status == self.SUPPLIER_PROCESS_STATUS_QUOTED
        # return self.value and self.supplier_delivery_date
    #
    # def is_processed_by_supplier(self):
    #     return self.supplier_delivery_date and self.value


class RFQFile(models.Model):
    # Buyer -> suppliers
    from vitesse_prod.apps.general_functions.functions import set_file_name

    order = models.ForeignKey('Order', related_name='rfq_files')
    order_file = models.ForeignKey('OrderFile', related_name='order_file_rfq_files', null=True, blank=True)

    file = models.FileField(upload_to=set_file_name, max_length=255, default='', blank=True)

    @property
    def file_name(self):

        file_name_str = ''
        if self.file:
            file_name_str = self.file.name.split('/')[-1]
        elif self.order_file and self.order_file.file:
            file_name_str = self.order_file.file.name.split('/')[-1]

        return file_name_str

    @property
    def file_url(self):

        file_url_str = ''
        if self.file:
            file_url_str = self.file.url
        elif self.order_file and self.order_file.file:
            file_url_str = self.order_file.file.url

        return file_url_str

    def __unicode__(self):
        return '%s. %s' % (self.order, self.order_file)


class SupplierQuoteFile(models.Model):
    # Supplier -> Buyer
    from vitesse_prod.apps.general_functions.functions import set_file_name

    supplier_quote = models.ForeignKey('SupplierQuote', related_name='supplier_quote_files')
    file = models.FileField(upload_to=set_file_name, max_length=255)

    @property
    def file_name(self):

        file_name_str = ''
        if self.file:
            file_name_str = self.file.name.split('/')[-1]

        return file_name_str

    @property
    def file_url(self):

        file_url_str = ''
        if self.file:
            file_url_str = self.file.url

        return file_url_str

    def __unicode__(self):
        return '%s. %s' % (self.supplier_quote, self.file)


class SupplierQuoteEndFile(models.Model):
    # Buyer -> End user
    from vitesse_prod.apps.general_functions.functions import set_file_name

    supplier_quote = models.ForeignKey('SupplierQuote', related_name='supplier_quote_end_files')

    supplier_quote_file = models.ForeignKey('SupplierQuoteFile', null=True, blank=True)
    file = models.FileField(upload_to=set_file_name, max_length=255, default='', blank=True)

    @property
    def file_name(self):

        file_name_str = ''
        if self.file:
            file_name_str = self.file.name.split('/')[-1]
        elif self.supplier_quote_file and self.supplier_quote_file.file:
            file_name_str = self.supplier_quote_file.file.name.split('/')[-1]

        return file_name_str

    @property
    def file_url(self):

        file_url_str = ''
        if self.file:
            file_url_str = self.file.url
        elif self.supplier_quote_file and self.supplier_quote_file.file:
            file_url_str = self.supplier_quote_file.file.url

        return file_url_str

    def __unicode__(self):
        return '%s. %s' % (self.supplier_quote, self.supplier_quote_file)


class SupplierQuoteToken(models.Model):
    supplier_quote = models.ForeignKey('SupplierQuote')

    token = models.TextField()

    is_active = models.BooleanField(default=True)  # Becomes False once SupplierQuite processed by supplier
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Supplier Quote Token')
        verbose_name_plural = _('Supplier Quote Tokens')

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.supplier_quote, self.token)

    def is_valid(self):
        utc_now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc, hour=0, minute=0, second=0, microsecond=0)
        return self.is_active and self.supplier_quote.order.buyer_deadline >= utc_now
               # and utc_now <= self.date_created + datetime.timedelta(days=3)

    def generate_token(self):
        return hashlib.sha512(str(self.__class__.__name__) + str(self.id) + str(datetime.datetime.utcnow())).hexdigest()

    def save(self, *args, **kwargs):

        if not self.token:

            generated_token = self.generate_token()

            while SupplierQuoteToken.objects.filter(token=generated_token).exists():
                generated_token = self.generate_token()

            self.token = generated_token

        super(SupplierQuoteToken, self).save(*args, **kwargs)


class SupplierQuoteBuyerShortlist(models.Model):

    user = models.ForeignKey('User')
    order = models.ForeignKey('Order')
    supplier_quotes = models.ManyToManyField('SupplierQuote')


class SupplierQuoteRecommendation(models.Model):

    supplier_quote = models.OneToOneField('SupplierQuote', related_name='supplier_quote_recommendation')
    comment = models.TextField(default='', blank=True)

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.supplier_quote, self.comment)


class PriceLookup(models.Model):

    item_description = models.TextField(default='', blank=True)
    manufacturer_name = models.TextField(default='', blank=True)
    unit_of_measure = models.TextField(default='', blank=True)
    vendor_price = models.FloatField(default=0)
    image_url = models.TextField(default='', blank=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.item_description)


class Category(Misc):
    from vitesse_prod.apps.general_functions.functions import set_file_name

    name = models.CharField(max_length=255)
    associative_words = models.ManyToManyField('CategoryAssociativeWords', blank=True)
    web_url = models.CharField(max_length=255, default='http://www.amazon.com/', blank=True)
    is_static = models.BooleanField(default=False)
    image = models.FileField(upload_to=set_file_name, max_length=255, blank=True, default='')

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class Subcategory(Misc):

    name = models.CharField(max_length=255)
    category = models.ForeignKey('Category', related_name='category_subcategories')
    web_url = models.CharField(max_length=255, default='http://www.amazon.com/', blank=True)

    class Meta:
        verbose_name = _('sub category')
        verbose_name_plural = _('sub categories')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class CategoryAssociativeWords(models.Model):

    name = models.CharField(max_length=255)

    class Meta:
        verbose_name = _('category associative word')
        verbose_name_plural = _('category associative words')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class DeliveryLocation(Misc):

    creator = models.ForeignKey('User', default=1)
    company = models.ForeignKey('Company', default=1)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    country = models.ForeignKey('Country', null=True, blank=True, on_delete=models.SET_NULL)
    city = models.ForeignKey('City', null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = _('delivery location')
        verbose_name_plural = _('delivery locations')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class Currency(Misc):

    name = models.CharField(max_length=100)
    sign = models.CharField(max_length=5)

    class Meta:
        verbose_name = _('currency')
        verbose_name_plural = _('currencies')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class AuthorizationLevel(HasCompany):

    level = models.IntegerField()
    single_purchase_value = models.IntegerField()
    monthly_budget = models.IntegerField()

    currency = models.ForeignKey('Currency')

    class Meta:
        verbose_name = _('authorization level')
        verbose_name_plural = _('authorization levels')
        ordering = ["level"]

    def __unicode__(self):
        return '%i. %i' % (self.id, self.level)

    @property
    def label(self):
        return "%i / %i / %i (%s)" % (self.level, self.single_purchase_value, self.monthly_budget, self.currency.sign)


class Region(models.Model):

    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    default_currency = models.ForeignKey('Currency', blank=True, null=True)
    helpdesk_phone = models.CharField(max_length=255, default='', blank=True)
    helpdesk_email = models.EmailField(max_length=255, default='', blank=True)

    class Meta:
        verbose_name = _('region')
        verbose_name_plural = _('regions')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class Measurement(Misc):

    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = _('measurement')
        verbose_name_plural = _('measurements')
        ordering = ["name"]

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class Supplier(models.Model):

    person_name = models.CharField(max_length=255, default='', blank=True)
    company_name = models.CharField(max_length=255, default='', blank=True)
    phone = models.CharField(max_length=255, default='', blank=True)
    web_site = models.CharField(max_length=255, default='', blank=True)
    email = models.EmailField(max_length=255, unique=True)

    category = models.ManyToManyField('Category', blank=True, related_name='category_suppliers')
    subcategory = models.ManyToManyField('Subcategory', blank=True)

    country = models.ForeignKey('Country', blank=True, null=True, on_delete=models.DO_NOTHING)
    city = models.ForeignKey('City', blank=True, null=True, on_delete=models.DO_NOTHING)

    # rank = models.CharField(max_length=50, default='0')

    # all fields are optional but any one is mandatory
    class Meta:
        verbose_name = _('supplier')
        verbose_name_plural = _('suppliers')
        ordering = ["person_name", "company_name", "email"]

    def __unicode__(self):
        return '%i. %s. %s.' % (self.id, self.person_name, self.company_name)

    def get_full_info(self):

        fields = [
            self.person_name,
            self.company_name,
            self.phone,
            self.web_site,
            self.email
        ]

        return ' | '.join(fields)


class OrderPreferredSupplier(models.Model):

    order = models.ForeignKey('Order')
    supplier = models.ForeignKey('Supplier', related_name='preferred_supplier_orders')

    class Meta:
        verbose_name = _('preferred supplier')
        verbose_name_plural = _('preferred suppliers')

    def __unicode__(self):
        return '%i. %s' % (self.id, self.order.app_user.name)


class OrderSuggestedSupplier(models.Model):

    order = models.ForeignKey('Order', related_name='order_suggested_suppliers')
    supplier = models.ForeignKey('Supplier', related_name='suggested_supplier_orders')

    class Meta:
        verbose_name = _('suggested supplier')
        verbose_name_plural = _('suggested suppliers')
        unique_together = ('order', 'supplier',)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.order.app_user.name)


class DeviceToken(models.Model):

    token = models.CharField(max_length=255)
    is_dev = models.BooleanField(default=True)
    is_sra = models.BooleanField(default=False)
    date_registered = models.DateTimeField(auto_now_add=True)

    user = models.ForeignKey(User, related_name="user_device_tokens")

    def __unicode__(self):
        return "%i. %s. %s" % (self.id, self.token[:20], self.user.name)

    class Meta:
        verbose_name = 'Device Token'
        verbose_name_plural = 'Device Tokens'


class UserDidLogin(models.Model):

    user = models.ForeignKey(User, related_name="did_login_users")
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%i. %s." % (self.id, self.user.name)

    class Meta:
        verbose_name = 'Logged In User'
        verbose_name_plural = 'Logged In Users'


class TravelLocation(models.Model):

    user = models.ForeignKey('User')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    max_cost = models.CharField(max_length=255)
    min_star_rating = models.CharField(max_length=255)

    def __unicode__(self):
        return "%i. %s." % (self.id, self.name)

    class Meta:
        ordering = ["name"]


class TravelPreferredHotels(models.Model):

    name = models.CharField(max_length=255)
    travel_location = models.ForeignKey('TravelLocation')

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return "%i. %s." % (self.id, self.name)


class TravelDepartureLocation(Misc):

    user = models.ForeignKey('User')
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    is_selected = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __unicode__(self):
        return "%i. %s." % (self.id, self.name)


class TravelAirline(models.Model):

    user = models.ForeignKey('User')
    airline = models.ForeignKey('Airline')

    is_preferred = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)

    def __unicode__(self):
        return "%i. %s. %s." % (self.id, self.user.email, self.airline.name)

    def save(self, *args, **kwargs):

        if self.is_preferred:
            self.is_rejected = False

        if self.is_rejected:
            self.is_preferred = False

        super(TravelAirline, self).save(*args, **kwargs)


class Airline(models.Model):

    name = models.CharField(max_length=255)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)

    class Meta:
        ordering = ["name"]


class TravelClass(models.Model):

    TRAIN_FIRST = 'First'
    TRAIN_STANDARD = 'Standard'

    TRAIN_CHOICES = (
        (TRAIN_FIRST, TRAIN_FIRST),
        (TRAIN_STANDARD, TRAIN_STANDARD)
    )

    AIRLINE_FIRST = 'First'
    AIRLINE_BUSINESS = 'Business'
    AIRLINE_PREMIUM_ECONOMY = 'Premium Economy'
    AIRLINE_ECONOMY = 'Economy'

    AIRLINE_CHOICES = (
        (AIRLINE_FIRST, AIRLINE_FIRST),
        (AIRLINE_BUSINESS, AIRLINE_BUSINESS),
        (AIRLINE_PREMIUM_ECONOMY, AIRLINE_PREMIUM_ECONOMY),
        (AIRLINE_ECONOMY, AIRLINE_ECONOMY),
    )

    user = models.ForeignKey('User', related_name="user_travelclass")

    train_travel_class = models.CharField(max_length=255, default=TRAIN_STANDARD, choices=TRAIN_CHOICES)
    airline_travel_hours = models.IntegerField(default=1, choices=((x, x) for x in range(1, 11)))
    airline_below_hours_travel_class = models.CharField(max_length=255, default=AIRLINE_ECONOMY, choices=AIRLINE_CHOICES)
    airline_above_hours_travel_class = models.CharField(max_length=255, default=AIRLINE_ECONOMY, choices=AIRLINE_CHOICES)
    airline_overnight_hours_travel_class = models.CharField(max_length=255, default=AIRLINE_ECONOMY, choices=AIRLINE_CHOICES)

    def __unicode__(self):
        return "%i. %s." % (self.id, self.train_travel_class)


class Itinerary(HasCompany, Misc):

    STATUS_RESUBMITTED = -1
    STATUS_NOT_SUBMITTED = 0
    STATUS_NEW = 1
    STATUS_PENDING_AUTHORIZATION = 2
    STATUS_ASSIGNED = 3
    STATUS_RECEIVED = 4
    STATUS_SOURCING = 5
    STATUS_QUOTED = 6
    STATUS_CLOSED_ACCEPTED = 7
    STATUS_CLOSED_CANCELED = 8
    STATUS_CLOSED_AUTHORIZER_DECLINED = 9
    STATUS_CLOSED_QUOTES_DECLINED = 10

    STATUS_CHOICES = (
        (STATUS_RESUBMITTED, 'Resubmitted'),
        (STATUS_NOT_SUBMITTED, 'Not Submitted'),
        (STATUS_NEW, 'New'),
        (STATUS_PENDING_AUTHORIZATION, 'Pending Authorization'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_SOURCING, 'Sourcing'),
        (STATUS_QUOTED, 'Quoted'),
        (STATUS_CLOSED_ACCEPTED, 'Closed Accepted'),
        (STATUS_CLOSED_CANCELED, 'Closed Canceled'),
        (STATUS_CLOSED_AUTHORIZER_DECLINED, 'Closed Authorizer Declined'),
        (STATUS_CLOSED_QUOTES_DECLINED, 'Closed Quotes Declined')
    )

    SUBMITTED = [
        STATUS_NEW,
        STATUS_PENDING_AUTHORIZATION,
        STATUS_ASSIGNED,
        STATUS_RECEIVED,
        STATUS_SOURCING,
        STATUS_QUOTED,
        STATUS_RESUBMITTED
    ]

    ARCHIVED = [
        STATUS_CLOSED_ACCEPTED,
        STATUS_CLOSED_CANCELED,
        STATUS_CLOSED_AUTHORIZER_DECLINED,
        STATUS_CLOSED_QUOTES_DECLINED
    ]

    name = models.CharField(max_length=255)
    departure_location = models.ForeignKey('TravelDepartureLocation', blank=True, null=True)
    text_location = models.TextField(default='', blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    status = models.IntegerField(default=STATUS_NOT_SUBMITTED, choices=STATUS_CHOICES)
    quotes_decline_comment = models.TextField(default='', blank=True)
    currency = models.ForeignKey('Currency')
    tracking_number = models.CharField(max_length=255, unique=True, db_index=True)
    # tracking_number = models.CharField(max_length=255, default='')

    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)
    date_submitted = models.DateTimeField(blank=True, null=True, default=None)
    date_assigned_to_buyer = models.DateTimeField(null=True, blank=True)
    date_status_changed = models.DateTimeField(null=True, blank=True)

    app_user = models.ForeignKey('User', related_name='user_itineraries')
    buyer = models.ForeignKey('User', related_name='buyer_itineraries', blank=True, null=True)

    def __unicode__(self):
        return "%i. %s." % (self.id, self.name)


class Appointment(models.Model):

    itinerary = models.ForeignKey('Itinerary')

    description = models.TextField(default='', blank=True)
    travel_location = models.ForeignKey('TravelLocation', blank=True, null=True)
    travel_location_custom = models.TextField(default='', blank=True)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    is_fixed = models.BooleanField(default=False)

    def __unicode__(self):
        return "%i. %s." % (self.id, self.description)


class AppointmentDay(models.Model):

    appointment = models.ForeignKey('Appointment')

    has_booked_hotel = models.BooleanField(default=False)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __unicode__(self):
        return "%i. %s." % (self.id, self.train_travel_class)


class ItineraryHotelDay(models.Model):

    itinerary = models.ForeignKey('Itinerary')

    has_booked_hotel = models.BooleanField(default=False)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __unicode__(self):
        return "%i. Itinerary: %s." % (self.id, self.itinerary.name)


class ItineraryQuote(models.Model):

    itinerary = models.ForeignKey('Itinerary', related_name='itinerary_quotes')

    value = models.FloatField(default=0)
    description = models.TextField(default='', null=True, blank=True)

    is_submitted = models.BooleanField(default=False)
    is_accepted = models.BooleanField(default=False)

    def __unicode__(self):
        return '%i. %0.2f' % (self.id, self.value)

    @property
    def total_value_gbp(self):
        from vitesse_prod.apps.general_functions.functions import get_currency_rate
        return self.value * get_currency_rate(self.itinerary.currency.name)


class SignupToken(models.Model):

    user = models.ForeignKey('User')
    token = models.CharField(max_length=255)
    is_validated = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Email Validation Token')
        verbose_name_plural = _('Email Validation Tokens')

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user.name)

    def generate_token(self):

        token = hashlib.sha512(str(self.id) + str(datetime.datetime.utcnow())).hexdigest()
        self.token = token
        self.save(update_fields=['token'])

        return token

    def save(self, *args, **kwargs):

        if not self.token:
            self.token = hashlib.sha512(str(self.id) + str(datetime.datetime.utcnow())).hexdigest()

        super(SignupToken, self).save(*args, **kwargs)


class BasicInfoProvided(models.Model):

    user = models.ForeignKey('User')
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user.name)


class OrdersInitialInfoProvided(models.Model):

    user = models.ForeignKey('User')
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user.name)


class TravelInitialInfoProvided(models.Model):

    user = models.ForeignKey('User')
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user.name)


# Expense Claims & Mileage

class ExpenseClaim(models.Model):

    # value_in_base = $$$$ of [self.currency]
    # value = $$$$ self.user.default_currency

    from vitesse_prod.apps.general_functions.functions import set_file_name

    project_text = models.CharField(max_length=255, default='', blank=True)
    project = models.ForeignKey('ExpenseClaimProject', null=True, blank=True)
    description = models.TextField(default='', blank=True)
    date = models.DateTimeField()
    expense_field = models.ForeignKey('ExpenseClaimField')
    value = models.FloatField()
    value_in_base = models.FloatField()
    currency = models.ForeignKey('Currency')
    photo = models.FileField(upload_to=set_file_name, max_length=255, blank=True, default='')
    photo_width = models.CharField(max_length=255, default='', blank=True)
    photo_height = models.CharField(max_length=255, default='', blank=True)

    user = models.ForeignKey('User', related_name='user_claims')
    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.description)

    @property
    def photo_url(self):
        return self.photo.url if self.photo else ''


class ExpenseClaimProject(models.Model):

    # owner = models.ForeignKey('User', related_name='user_own_projects', blank=True, null=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey('Company')

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)

    # def save(self, *args, **kwargs):
    #
    #     if not self.id:
    #         self.company = self.owner.company
    #
    #     super(ExpenseClaimProject, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Expense Project')
        verbose_name_plural = _('Expense Projects')
        ordering = ["name"]


class ExpenseClaimProjectUsage(models.Model):

    user = models.ForeignKey('User')
    project = models.ForeignKey('ExpenseClaimProject', related_name='project_usages')
    count = models.IntegerField(default=1)

    def __unicode__(self):
        return '%i. %s. %i times' % (self.id, self.project.name, self.count)

    class Meta:
        unique_together = ('user', 'project',)


class ExpenseClaimField(models.Model):

    name = models.CharField(max_length=255)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)

    class Meta:
        verbose_name = _('Expense Field')
        verbose_name_plural = _('Expense Fields')
        ordering = ["name"]


class Mileage(models.Model):

    user = models.ForeignKey('User', related_name='user_mileages')
    description = models.TextField(default='', blank=True)
    date = models.DateTimeField()
    miles = models.FloatField()
    cost_per_mile = models.FloatField()
    project = models.ForeignKey('ExpenseClaimProject', null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_edited = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.description)


class ExpenseClaimTeam(models.Model):

    owner = models.ForeignKey('User', related_name='user_own_teams')
    lead = models.ForeignKey('User', related_name='user_lead_teams', null=True, blank=True)
    name = models.CharField(max_length=255)
    members = models.ManyToManyField('User', blank=True, related_name='user_teams')

    def __unicode__(self):
        return '%i. %s' % (self.id, self.name)


class RecoverPasswordToken(models.Model):

    user = models.ForeignKey('User')
    token = models.CharField(max_length=255)
    is_validated = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user.name)

    def generate_token(self):

        token = hashlib.sha512('1' + str(self.id) + str(datetime.datetime.utcnow())).hexdigest()
        self.token = token
        self.save(update_fields=['token'])

        return token


class Rating(models.Model):

    user = models.ForeignKey('User')
    value = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255)

    order = models.ForeignKey('Order', blank=True, null=True)
    itinerary = models.ForeignKey('Itinerary', blank=True, null=True)
    activity = models.ForeignKey('Activity', blank=True, null=True)

    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user.name)


class CurrencyRate(models.Model):

    data = models.TextField(default='{}', blank=True)
    last_date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%i.' % (self.id, )


class Purchase(models.Model):

    user = models.ForeignKey('User', related_name='user_purchases')
    quote = models.ForeignKey('Quote', null=True, blank=True)
    itinerary_quote = models.ForeignKey('ItineraryQuote', null=True, blank=True)
    activity_quote = models.ForeignKey('ActivityQuote', null=True, blank=True)

    sum_paid = models.FloatField()
    braintree_transaction_token = models.CharField(max_length=255, blank=True, default='')

    is_deleted = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i.' % (self.id, )


class UserAPIAnalyticsTime(models.Model):

    index = models.IntegerField(default=1)
    label = models.CharField(max_length=255)
    command = models.CharField(max_length=255)

    def __unicode__(self):
        return '%i. %s. %s.' % (self.id, self.label, self.command)

    def to_data(self, is_selected=False):
        return {
            'id': self.id,
            'name': self.label,
            'is_selected': is_selected
        }


class UserAPIAnalyticsType(models.Model):

    index = models.IntegerField(default=1)
    label = models.CharField(max_length=255)
    command = models.CharField(max_length=255)

    def __unicode__(self):
        return '%i. %s. %s.' % (self.id, self.label, self.command)


class UserAPIAnalyticsFilters(models.Model):

    user = models.OneToOneField('User')

    type = models.ForeignKey('UserAPIAnalyticsType')
    time = models.ForeignKey('UserAPIAnalyticsTime')
    currency = models.ForeignKey('Currency')

    user_ids = models.TextField(default='[]', blank=True)
    purchase_category_ids = models.TextField(default='[]', blank=True)
    travel_category_ids = models.TextField(default='[]', blank=True)
    expense_field_ids = models.TextField(default='[]', blank=True)
    project_ids = models.TextField(default='[]', blank=True)

    def __unicode__(self):
        return '%i.' % (self.id,)

    def reset_to_defaults(self):

        from vitesse_prod.apps.general_functions.functions import get_object_or_None

        new_values = {
            'user_ids': '[]',
            'purchase_category_ids': '[]',
            'travel_category_ids': '[]',
            'expense_field_ids': '[]',
            'project_ids': '[]',
            'type': get_object_or_None(UserAPIAnalyticsType, command='expenses'),
            'time': get_object_or_None(UserAPIAnalyticsTime, command='current_quarter'),
            'currency': self.user.default_currency
        }

        for attr_name, value in new_values.items():
            setattr(self, attr_name, value)
        self.save(update_fields=new_values.keys())

        return self

    def update_filters(self, data):

        basic_data = {}
        if 'type_id' in data and data['type_id'] != str(self.type_id):
            basic_data['purchase_category_ids'] = [u'[]']
            basic_data['travel_category_ids'] = [u'[]']
            basic_data['expense_field_ids'] = [u'[]']
            basic_data['project_ids'] = [u'[]']

        basic_data.update(data)

        for attr_name, value in basic_data.items():
            setattr(self, attr_name, value[0])
        self.save(update_fields=basic_data.keys())

        return self


class UserAPIAnalyticsLocalFilters(models.Model):

    user = models.OneToOneField('User')
    time = models.ForeignKey('UserAPIAnalyticsTime')

    def __unicode__(self):
        return '%i.' % (self.id,)

    def reset(self):

        from vitesse_prod.apps.general_functions.functions import get_object_or_None

        default_values = {
            'time_id': get_object_or_None(UserAPIAnalyticsTime, command='current_quarter').id
        }

        return self.update(default_values)

    def update(self, data):

        keys_to_update = []
        for attr_name, value in data.items():
            if hasattr(self, attr_name):
                setattr(self, attr_name, value)
                keys_to_update = [attr_name]
        self.save(update_fields=keys_to_update)

        return self

    def get_list(self):

        filters = []
        analytics_times = UserAPIAnalyticsTime.objects.all()
        for time in analytics_times:
            filters.append(time.to_data(time.id == self.user.get_api_home_filter().time_id))

        return filters


# New Booking Section called "Activities"

class Activity(HasCompany, Misc):

    STATUS_NOT_SUBMITTED = 0
    STATUS_NEW = 1
    STATUS_ASSIGNED = 2
    STATUS_RECEIVED = 3
    STATUS_SOURCING = 4
    STATUS_QUOTED = 5
    STATUS_QUOTE_ACCEPTED = 6
    STATUS_QUOTES_DECLINED = 7

    STATUS_CHOICES = (
        (STATUS_NOT_SUBMITTED, 'Not Submitted'),
        (STATUS_NEW, 'New'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_SOURCING, 'Sourcing'),
        (STATUS_QUOTED, 'Quoted'),
        (STATUS_QUOTE_ACCEPTED, 'Quote Accepted'),
        (STATUS_QUOTES_DECLINED, 'Quotes Declined'),
    )

    TYPE_FLIGHT = 'flight'
    TYPE_TRAIN = 'train'
    TYPE_HOTEL = 'hotel'
    TYPE_TAXI = 'taxi'
    TYPE_CAR_RENTAL = 'car_rent'
    TYPE_MEALS = 'meal'
    TYPE_APPOINTMENTS = 'appointment'

    TYPE_CHOICES = (
        (TYPE_FLIGHT, 'Flight'),
        (TYPE_TRAIN, 'Train'),
        (TYPE_HOTEL, 'Hotel'),
        (TYPE_TAXI, 'Taxi'),
        (TYPE_CAR_RENTAL, 'Car Rental'),
        (TYPE_MEALS, 'Meal'),
        (TYPE_APPOINTMENTS, 'Appointment'),
    )

    ANALYTICS_TYPE_CHOICES = (
        (TYPE_FLIGHT, 'Flight'),
        (TYPE_TRAIN, 'Train'),
        (TYPE_HOTEL, 'Hotel'),
        (TYPE_TAXI, 'Taxi'),
        (TYPE_CAR_RENTAL, 'Car Rental'),
    )

    user = models.ForeignKey('User')
    buyer = models.ForeignKey('User', null=True, blank=True, related_name='buyer_activities')
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)
    type = models.CharField(max_length=100, choices=TYPE_CHOICES)
    currency = models.ForeignKey('Currency', blank=True, null=True)
    purchase = models.ForeignKey('Purchase', blank=True, null=True)
    project = models.ForeignKey('ExpenseClaimProject', blank=True, null=True)

    from_departure_location = models.ForeignKey('TravelDepartureLocation', null=True, blank=True)
    from_text = models.TextField(default='', blank=True)

    to_travel_location = models.ForeignKey('TravelLocation', null=True, blank=True)
    to_text = models.TextField(default='', blank=True)

    estimated_start_date = models.DateTimeField(null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    return_start_date = models.DateTimeField(null=True, blank=True)
    return_end_date = models.DateTimeField(null=True, blank=True)
    # event_time = models.TimeField(null=True, blank=True)

    num_of_people = models.IntegerField(default=1, blank=True)

    travel_preferences = models.TextField(default='{}', blank=True)
    airlines = models.TextField(default='{}', blank=True)

    should_source = models.BooleanField(default=False)
    additional_information = models.TextField(default='', blank=True)

    location_name = models.CharField(max_length=255, default='', blank=True)
    address = models.CharField(max_length=255, default='', blank=True)
    city = models.CharField(max_length=255, default='', blank=True)
    near_locality = models.CharField(max_length=255, default='', blank=True)

    max_cost_per_night = models.CharField(max_length=20, default='', blank=True)
    min_star_rating = models.IntegerField(default=3, blank=True)
    tracking_number = models.CharField(max_length=255, unique=True, db_index=True, blank=True)

    quotes_decline_comment = models.TextField(default='', blank=True)
    date_assigned_to_buyer = models.DateTimeField(null=True, blank=True)

    payment_date = models.DateTimeField(blank=True, null=True, default=None)
    date_created = models.DateTimeField(auto_now_add=True)
    is_fixed = models.BooleanField(default=False)
    is_two_way = models.BooleanField(default=False)

    def __unicode__(self):
        return '%i.' % (self.id, )

    @property
    def icon_url(self):

        from django.conf import settings

        url = settings.STATIC_URL + 'img/activity/'

        if self.type == self.TYPE_FLIGHT:
            url += 'airplane.png'

        elif self.type == self.TYPE_TRAIN:
            url += 'train.png'

        elif self.type == self.TYPE_HOTEL:
            url += 'hotel.png'

        elif self.type == self.TYPE_TAXI:
            url += 'taxi.png'

        elif self.type == self.TYPE_CAR_RENTAL:
            url += 'car.png'

        elif self.type == self.TYPE_MEALS:
            url += 'meal.png'

        elif self.type == self.TYPE_APPOINTMENTS:
            url += 'appointment.png'

        return url

    @property
    def display_name(self):

        name = ''
        if self.type == self.TYPE_FLIGHT:
            name = 'Flight to '

            if self.to_travel_location:
                name += self.to_travel_location.name

            elif self.to_text:
                name += self.to_text

        elif self.type == self.TYPE_TRAIN:
            name = 'Train to '

            if self.to_travel_location:
                name += self.to_travel_location.name

            elif self.to_text:
                name += self.to_text

        elif self.type == self.TYPE_HOTEL:
            name = 'Hotel check-in'

        elif self.type == self.TYPE_TAXI:
            name = 'Taxi ride to %s' % self.to_text

        elif self.type == self.TYPE_CAR_RENTAL:
            name = 'Car rental'

        elif self.type == self.TYPE_MEALS:
            name = 'Meal at %s' % self.location_name

        elif self.type == self.TYPE_APPOINTMENTS:
            name = self.location_name

        return name

    def get_type_ids_by_type_names(self, type_names=()):

        type_ids = []
        for choice in self.TYPE_CHOICES:

            if choice[0] in type_names:
                type_ids.append(choice[1])

        return type_ids


class ActivityQuote(models.Model):

    activity = models.ForeignKey('Activity', related_name='activity_quotes')

    value = models.FloatField(default=0.00)
    airline = models.TextField(default='', null=True, blank=True)
    address = models.TextField(default='', null=True, blank=True)
    description = models.TextField(default='', null=True, blank=True)
    inner_comment = models.TextField(default='', blank=True)

    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    return_start_date = models.DateTimeField(null=True, blank=True)
    return_end_date = models.DateTimeField(null=True, blank=True)

    is_accepted = models.BooleanField(default=False)

    def __unicode__(self):
        return '%i. %0.2f' % (self.id, self.value)

    @property
    def total_value_gbp(self):
        from vitesse_prod.apps.general_functions.functions import get_currency_rate
        return self.value * get_currency_rate(self.activity.currency.name)

    @property
    def total_value_gbp_int(self):
        return int(self.total_value_gbp * 100)


class FirstExpenseClaimCreated(models.Model):

    user = models.ForeignKey('User')

    def __unicode__(self):
        return '%i. %s' % (self.id, self.user)


class ReportSharing(models.Model):

    # STATUS_NOT_SHARING = 0
    STATUS_REQUESTED = 'requested'
    STATUS_SHARING = 'sharing'

    STATUS_CHOICES = (
        # (STATUS_NOT_SHARING, 'Not Sharing'),
        (STATUS_REQUESTED, 'Requested'),
        (STATUS_SHARING, 'Sharing')
    )

    user_from = models.ForeignKey('User', related_name='report_sharing_from')
    user_to = models.ForeignKey('User', related_name='report_sharing_to')
    status = models.CharField(max_length=200, default=STATUS_REQUESTED, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('user_from', 'user_to',)

    def __unicode__(self):
        return '%i. From: %s. To: %s. %s.' % (self.id, self.user_from, self.user_to, self.get_status_display())


class PowerBICredentials(models.Model):

    data = models.TextField(default='{}')

    def __unicode__(self):
        return '%i. %s' % (self.id, self.data)


class ActivityNotification(models.Model):

    TYPE_ORDER_DECLINED = 'order_declined'
    TYPE_ORDER_RECEIVED_QUOTES = 'order_received_quotes'
    TYPE_ORDER_APPROVAL_REQUEST = 'order_approval_request'
    TYPE_ORDER_BUYER_RETURNED = 'order_buyer_returned'
    TYPE_ACTIVITY_RECEIVED_QUOTES = 'activity_received_quotes'
    TYPE_SHARE_REPORT_WITH_YOU = 'share_with_you'
    # TYPE_SHARE_REPORT_BY_YOU = 'share_by_you'

    TYPE_CHOICES = (
        (TYPE_ORDER_DECLINED, TYPE_ORDER_DECLINED),
        (TYPE_ORDER_RECEIVED_QUOTES, TYPE_ORDER_RECEIVED_QUOTES),
        (TYPE_ORDER_APPROVAL_REQUEST, TYPE_ORDER_APPROVAL_REQUEST),
        (TYPE_ORDER_BUYER_RETURNED, TYPE_ORDER_BUYER_RETURNED),
        (TYPE_ACTIVITY_RECEIVED_QUOTES, TYPE_ACTIVITY_RECEIVED_QUOTES),
        (TYPE_SHARE_REPORT_WITH_YOU, TYPE_SHARE_REPORT_WITH_YOU),
        # (TYPE_SHARE_REPORT_BY_YOU, TYPE_SHARE_REPORT_BY_YOU),
    )

    user_from = models.ForeignKey('User', related_name='user_from_activity_notifications')
    user_to = models.ForeignKey('User', related_name='user_to_activity_notifications')

    type = models.CharField(max_length=200, choices=TYPE_CHOICES)

    order = models.ForeignKey('Order', null=True, blank=True)
    activity = models.ForeignKey('Activity', null=True, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return '%i.' % (self.id,)

    @property
    def message(self):
        message_str = ''

        if self.type == self.TYPE_ORDER_DECLINED:
            message_str = "Purchase #%s has been declined by %s %s" % (
                self.order.tracking_number,
                self.user_from.name,
                self.user_from.surname
            )

        elif self.type == self.TYPE_ORDER_RECEIVED_QUOTES:
            message_str = "Purchase #%s has been quoted" % self.order.tracking_number

        elif self.type == self.TYPE_ORDER_APPROVAL_REQUEST:
            message_str = "Purchase #%s requires authorization" % self.order.tracking_number

        elif self.type == self.TYPE_ACTIVITY_RECEIVED_QUOTES:

            activity_type_str = 'Travel Activity'
            if self.activity.type == self.activity.TYPE_FLIGHT:
                activity_type_str = 'flight'

            elif self.activity.type == self.activity.TYPE_TRAIN:
                activity_type_str = 'train ride'

            elif self.activity.type == self.activity.TYPE_CAR_RENTAL:
                activity_type_str = 'car rent'

            elif self.activity.type == self.activity.TYPE_HOTEL:
                activity_type_str = 'hotel booking'

            message_str = "Your %s #%s has been quoted" % (activity_type_str, self.activity.tracking_number)

        elif self.type == self.TYPE_SHARE_REPORT_WITH_YOU:
            message_str = "%s would like to see your reports" % self.user_from.get_full_name()

        elif self.type == self.TYPE_ORDER_BUYER_RETURNED:
            message_str = 'Order has been returned by buyer. Tracking number: #%s.\nBuyer comment: %s' % (str(self.order.tracking_number), self.order.order_return_comment.get().comment)

        return message_str

    @property
    def action_center_message(self):
        message_str = ''

        if self.type == self.TYPE_ORDER_DECLINED:
            message_str = "Request #%s has been declined by %s %s" % (
                self.order.tracking_number,
                self.user_from.name,
                self.user_from.surname
            )

        elif self.type == self.TYPE_ORDER_RECEIVED_QUOTES:
            message_str = "Request #%s has been quoted" % self.order.tracking_number

        elif self.type == self.TYPE_ORDER_APPROVAL_REQUEST:
            message_str = "Request #%s requires authorization" % self.order.tracking_number

        elif self.type == self.TYPE_ACTIVITY_RECEIVED_QUOTES:

            activity_type_str = 'Travel Activity'
            if self.activity.type == self.activity.TYPE_FLIGHT:
                activity_type_str = 'flight'

            elif self.activity.type == self.activity.TYPE_TRAIN:
                activity_type_str = 'train ride'

            elif self.activity.type == self.activity.TYPE_CAR_RENTAL:
                activity_type_str = 'car rent'

            elif self.activity.type == self.activity.TYPE_HOTEL:
                activity_type_str = 'hotel booking'

            message_str = "Your %s #%s has been quoted" % (activity_type_str, self.activity.tracking_number)

        elif self.type == self.TYPE_SHARE_REPORT_WITH_YOU:
            message_str = "%s would like to see your reports" % self.user_from.get_full_name()

        elif self.type == self.TYPE_ORDER_BUYER_RETURNED:
            message_str = 'Request has been returned by buyer. Tracking number: #%s.' % self.order.tracking_number

        return message_str


class UserExpensesReminderLog(models.Model):

    user = models.ForeignKey('User', related_name='user_reminder_logs')
    date_updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%i. %s. %s' % (self.id, self.user.name, self.date_updated)


class Country(models.Model):

    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = _('country')
        verbose_name_plural = _('countries')
        ordering = ['name']

    def __unicode__(self):
        return self.name


class City(models.Model):

    name = models.CharField(max_length=255)
    country = models.ForeignKey('Country', related_name='cities', on_delete=models.CASCADE)

    def validate_unique(self, exclude=None):
        city = City.objects.filter(country=self.country, name=self.name)
        if len(city) > 0:
            raise ValidationError(
                _('%s already exists in %s' % (self.name, self.country.name)),
                code='invalid',
                params={'city': self.name, 'country': self.country.name}
            )

    class Meta:
        verbose_name = _('city')
        verbose_name_plural = _('cities')
        ordering = ['name']

    def __unicode__(self):
        return self.name


class BestDeal(models.Model):
    from vitesse_prod.apps.general_functions.functions import set_file_name

    image = models.FileField(upload_to=set_file_name, max_length=255, blank=True, default='')
    short_description = models.TextField()
    long_description = models.TextField()
    companies = models.ManyToManyField('Company', related_name='best_deals', blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('best deal')
        verbose_name_plural = _('best deals')
        ordering = ['date_created']

    def __unicode__(self):
        return self.short_description


class Catalog(models.Model):

    file_name = models.TextField()
    file = models.FileField(upload_to='/catalogs/', blank=True, null=True)
    companies = models.ManyToManyField('Company', blank=True)
    users = models.ManyToManyField('User', blank=True, related_name='user_catalogs')
    date_created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s. %s." % (self.file_name, self.date_created)


class CatalogItem(models.Model):

    supplier_name = models.TextField()
    title = models.TextField()
    short_description = models.TextField()
    long_description = models.TextField(default='')
    manufacturer = models.TextField(default='')
    brand = models.TextField(default='')
    image_url = models.TextField()

    price = models.FloatField()
    tax_amount = models.FloatField(default=0)
    days_to_deliver = models.SmallIntegerField(default=3)

    currency = models.ForeignKey('Currency')
    measurement = models.ForeignKey('Measurement')
    category = models.ForeignKey('Category')
    category_level_2 = models.ForeignKey('Category', blank=True, null=True, related_name='categories_level_2')
    category_level_3 = models.ForeignKey('Category', blank=True, null=True, related_name='categories_level_3')
    category_level_4 = models.ForeignKey('Category', blank=True, null=True, related_name='categories_level_4')
    catalog = models.ForeignKey('Catalog', related_name='catalog_items')

    vendor = models.TextField('Vendor', default="")
    synonym = models.TextField('Synonym', default="")

    # companies = models.ManyToManyField('Company', related_name='catalog_items', blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _('catalog item')
        verbose_name_plural = _('catalog items')

    def __unicode__(self):
        return self.title

    @property
    def description(self):
        return '.'.join([self.short_description, self.long_description])

    def has_valid_image_url(self):

        is_image = False
        image_formats = ("image/png", "image/jpeg", "image/gif")
        try:
            site = requests.get(self.image_url)
        except:
            pass
        else:
            if site.headers['content-type'] in image_formats:  # check if the content-type is a image
                is_image = True
        return is_image


@python_2_unicode_compatible
class Product(models.Model):
    title = models.CharField(max_length=255, unique=True)
    attributes = models.ManyToManyField("ProductAttribute")
    category = models.ForeignKey('Category', related_name='category_product', null=True, blank=True)

    def __str__(self):
        return self.title

    @property
    def values(self):
        result = {}

        for attribute in self.attributes.all():
            result[attribute.title] = {
                'id': attribute.id,
                'slug': slugify(attribute.title).replace('-', '_').lower(),
                'values': ProductAttributeValue.objects.filter(
                    products__product=self, products__attribute=attribute).uniq_values(),
                'measurements': attribute.measurements_list
            }

        return result


@python_2_unicode_compatible
class NLPProductAttribute(models.Model):
    product = models.ForeignKey('Product')
    attribute = models.ForeignKey('ProductAttribute')

    matchers = JSONField(null=True)

    def __str__(self):
        return "{}. {} - {}".format(self.id, self.product.title, self.attribute.title)

    @property
    def values(self):
        return ProductAttributeValue.objects.filter(
                    products__product=self.product, products__attribute=self.attribute).uniq_values()

    def nlp_rules(self):

        values = []
        if self.attribute.measurements.all().exists():
            for measurement in self.attribute.measurements.all():
                values.extend(list(measurement.items.all().values_list('title', flat=True)))
        else:
            values = list(self.values.values_list('value_lower', flat=True))

        if self.attribute.nlp_pattern is None:

            patterns = [[{'LOWER': t.lower()} for t in value.split()] for value in filter(None, values)]

        else:
            patterns = []

            for pattern in self.attribute.nlp_pattern:

                for value in filter(None, values):
                    attr_pattern = pattern[:]
                    attr_pattern.append({"LOWER": t.lower() for t in value.split()})
                    patterns.append(attr_pattern)
        self.matchers = patterns
        self.save()


class ProductAttributeValueQueryset(models.QuerySet):
    def uniq_values(self, **kwargs):
        return self.annotate(
            value_lower=Lower('value')).distinct('value_lower').order_by('value_lower')


class ProductAttributeValueManager(models.Manager):
    # use_for_related_fields = True

    def get_queryset(self):
        return ProductAttributeValueQueryset(self.model, using=self._db)


@python_2_unicode_compatible
class ProductAttribute(models.Model):
    title = models.CharField(max_length=255, unique=True)
    is_custom = models.BooleanField(default=False)
    nlp_pattern = JSONField(null=True)
    matchers = JSONField(null=True)

    measurements = models.ManyToManyField('ProductMeasurementGroup')
    measurements_items = models.ManyToManyField('ProductMeasurement')

    # order

    class Meta:
        # ordering = []
        pass

    def __str__(self):
        return "{} {}".format(self.title, "[custom]" if self.is_custom else "")

    @property
    def slug(self):
        return slugify(self.title).replace('-', '_')

    def nlp_rules(self):

        values = []
        if self.measurements.all().exists():
            for measurement in self.measurements.all():
                values.extend(list(measurement.items.all().values_list('title', flat=True)))
        else:
            values = list(self.values.all().distinct().values_list('value', flat=True))

        if self.nlp_pattern is None:

            patterns = [[{'LOWER': t.lower()} for t in value.split()] for value in filter(None, values)]

        else:
            patterns = []

            for pattern in self.nlp_pattern:

                for value in filter(None, values):
                    attr_pattern = pattern[:]
                    attr_pattern.append({"LOWER": t.lower() for t in value.split()})
                    patterns.append(attr_pattern)
        self.matchers = patterns
        self.save()

    @property
    def raw_values(self):
        return json.dumps([v.value for v in self.values.all()])

    @property
    def raw_measurements(self):
        return json.dumps(self.measurements_list)

    @property
    def measurements_list(self):
        m = [v.title for m in self.measurements.all().distinct() for v in m.items.all().distinct()]
        m.extend([i.title for i in self.measurements_items.all().distinct()])
        return sorted(list(set(m)))


@python_2_unicode_compatible
class ProductAttributeValue(models.Model):
    value = models.TextField()
    is_manual = models.BooleanField(default=False)
    product_attribute = models.ForeignKey('ProductAttribute', related_name="values", related_query_name='values',
                                          on_delete=models.CASCADE)

    order = models.ForeignKey('Order', related_name='order_values', related_query_name='order_values', blank=True,
                              null=True, on_delete=models.SET_NULL)
    order_line = models.ForeignKey('OrderLine', related_name='order_line_values', blank=True, null=True,
                                   on_delete=models.SET_NULL)

    objects = ProductAttributeValueManager()

    def __str__(self):
        return "{}: {}".format(self.product_attribute, self.value)


@python_2_unicode_compatible
class ProductMeasurementGroup(models.Model):
    title = models.CharField(max_length=255)

    def __str__(self):
        return "{}: {} items".format(self.title, self.items.all().count())


@python_2_unicode_compatible
class ProductMeasurement(models.Model):
    title = models.CharField(max_length=255)
    group = models.ForeignKey(
        'ProductMeasurementGroup',
        on_delete=models.CASCADE,
        related_name='items',
        related_query_name='items',
        null=True,
        blank=True
    )

    def __str__(self):
        return "{}: {}".format(self.group.title, self.title)


@python_2_unicode_compatible
class ProductAttributeValueThrough(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='product_values', related_query_name='product_values')
    attribute = models.ForeignKey('ProductAttribute', on_delete=models.CASCADE, related_name='product_values')
    value = models.ForeignKey('ProductAttributeValue', on_delete=models.CASCADE, related_name='products',
                              related_query_name='products')

    def __str__(self):
        return "{} [{}] - {}".format(self.product.title, self.attribute.title, self.value.value)


# SIGNALS


def create_company(sender, instance, created, **kwargs):

    from vitesse_prod.apps.api.functions import get_default_currency, get_default_region, create_default_auth_level, create_default_auth_level_standalone

    if created:

        # If Sponsor created, it means the company created at this time as well
        # if instance.role == User.SPONSOR:
            # Create Company's default auth level
            # create_default_auth_level(instance.company)

        if instance.role == User.APP_USER:

            if instance.company:
                company = Company.objects.get(id=instance.company_id)

                if company.is_standalone:
                    instance.authorization_level = create_default_auth_level_standalone(company)

                    #FIXME
                    # instance.authorizer =

    if instance.default_currency and instance.company and not instance.company.high_expense_limit_currency:
        instance.company.high_expense_limit_currency = instance.default_currency
        instance.company.save(update_fields=['high_expense_limit_currency'])

        # Add default currency and region to a newly created user
        # try:
        #     instance.default_currency = get_default_currency()
        #
        #     if not instance.default_region:
        #         instance.default_region = get_default_region()
        # except:
        #     pass

        # instance.save(update_fields=['default_currency', 'authorization_level'])


def create_default_travel_class(sender, instance, created, **kwargs):

    if created:
        TravelClass.objects.create(
            user=instance,
            train_travel_class=TravelClass.TRAIN_STANDARD,
            airline_travel_hours=5,
            airline_below_hours_travel_class=TravelClass.AIRLINE_ECONOMY,
            airline_above_hours_travel_class=TravelClass.AIRLINE_ECONOMY,
            airline_overnight_hours_travel_class=TravelClass.AIRLINE_ECONOMY
        )


def set_order_status_changed_date(sender, instance, **kwargs):

    import datetime, pytz

    if not instance.id:
        instance.date_status_changed = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)

    else:
        old_order = Order.objects.get(id=instance.id)

        if old_order.status != instance.status:
            instance.date_status_changed = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)


def inherit_region_currency(sender, instance, **kwargs):

    if instance.id:

        old_region = User.objects.get(id=instance.id).default_region
        if instance.default_region != old_region:
            instance.default_currency = instance.default_region.default_currency

    else:

        if not instance.default_currency and instance.default_region:
            instance.default_currency = instance.default_region.default_currency


def process_currency_change(sender, instance, **kwargs):

    if instance.id and User.objects.get(id=instance.id).default_currency:

        old_currency = User.objects.get(id=instance.id).default_currency
        new_currency = instance.default_currency

        if new_currency != old_currency and old_currency and new_currency:

            from vitesse_prod.apps.general_functions.functions import convert_sum

            # Recalc Claims and Mileages
            ExpenseClaim.objects.filter(user=instance).update(
                value=convert_sum(F('value'), old_currency.name, new_currency.name)
            )

            Mileage.objects.filter(user=instance).update(
                cost_per_mile=convert_sum(F('cost_per_mile'), old_currency.name, new_currency.name)
            )


def remove_old_notifications(sender, instance, **kwargs):

    if instance.id:

        old_user_role = User.objects.get(id=instance.id).role
        new_user_role = instance.role

        if old_user_role != new_user_role and new_user_role == User.SPONSOR:

            ActivityNotification.objects.filter(
                user_from=instance,
                type=ActivityNotification.TYPE_SHARE_REPORT_WITH_YOU
            ).delete()


def set_order_tracking_number(sender, instance, **kwargs):

    from vitesse_prod.apps.general_functions.functions import generate_order_tracking_number

    if not instance.tracking_number:
        instance.tracking_number = generate_order_tracking_number()


def set_activity_tracking_number(sender, instance, **kwargs):

    from vitesse_prod.apps.general_functions.functions import generate_activity_tracking_number

    if not instance.tracking_number:
        instance.tracking_number = generate_activity_tracking_number()


def set_activity_status(sender, instance, **kwargs):

    if not instance.should_source:
        instance.status = Activity.STATUS_NOT_SUBMITTED

    if instance.id:
        old_activity = Activity.objects.get(id=instance.id)
        if instance.should_source and old_activity.should_source != instance.should_source and old_activity.status == Activity.STATUS_NOT_SUBMITTED:
            instance.status = Activity.STATUS_NEW


def company_initial_data_create(sender, instance, created, **kwargs):

    if created:

        obj_list = []
        initial_project_names = [
            'Internal',
            'Sales Activity',
            'Client Work'
        ]

        for project_name in initial_project_names:
            obj_list.append(
                ExpenseClaimProject(
                    name=project_name, company=instance
                )
            )

        ExpenseClaimProject.objects.bulk_create(obj_list)

        if not instance.is_standalone:
            from vitesse_prod.apps.api.functions import create_default_auth_level
            create_default_auth_level(instance)


def sponsor_report_sharing(sender, instance, created, **kwargs):

    if instance.role == User.BUYER:
        return {}

    report_sharing_objs = []

    sponsors_ids = User.objects.filter(role=User.SPONSOR, company=instance.company)
    if not created:

        from vitesse_prod.apps.api.functions import get_shared_reports_users

        already_connected_users_ids = get_shared_reports_users(instance)['users_involved_ids']
        sponsors_ids = sponsors_ids.exclude(id=instance.id).exclude(id__in=already_connected_users_ids)

    sponsors_ids = sponsors_ids.values_list('id', flat=True)

    for sponsors_id in sponsors_ids:
        report_sharing_objs.append(ReportSharing(user_from=instance, user_to_id=sponsors_id, status=ReportSharing.STATUS_SHARING))

    ReportSharing.objects.bulk_create(report_sharing_objs)


def increase_user_unread_notifs_count(sender, instance, created, **kwargs):

    if created:
        instance.user_to.set_unread_notifications_count('+1')


def reduce_user_unread_notifs_count(sender, instance, **kwargs):
    instance.user_to.set_unread_notifications_count('-1')


def clear_text(sender, instance, **kwargs):

    from vitesse_prod.apps.general_functions.functions import clear_text

    if sender == ExpenseClaim:
        instance.project_text = clear_text(instance.project_text)
        instance.description = clear_text(instance.description)

    elif sender == ExpenseClaimProject:
        instance.name = clear_text(instance.name)

    elif sender == Mileage:
        instance.description = clear_text(instance.description)

    elif sender == Order:
        instance.make = clear_text(instance.make)
        instance.model = clear_text(instance.model)
        instance.description = clear_text(instance.description)
        instance.quotes_decline_comment = clear_text(instance.quotes_decline_comment)

    elif sender == Activity:
        instance.from_text = clear_text(instance.from_text)
        instance.to_text = clear_text(instance.to_text)

    elif sender == User:
        instance.name = clear_text(instance.name)
        instance.surname = clear_text(instance.surname)
        instance.title = clear_text(instance.title)


models.signals.post_save.connect(create_company, sender=User)
models.signals.post_save.connect(create_default_travel_class, sender=User)
models.signals.post_save.connect(sponsor_report_sharing, sender=User)
models.signals.pre_save.connect(remove_old_notifications, sender=User)
models.signals.pre_save.connect(inherit_region_currency, sender=User)
models.signals.pre_save.connect(process_currency_change, sender=User)
models.signals.pre_save.connect(set_order_status_changed_date, sender=Order)
models.signals.pre_save.connect(set_order_tracking_number, sender=Order)
models.signals.pre_save.connect(set_activity_tracking_number, sender=Activity)
models.signals.pre_save.connect(set_activity_status, sender=Activity)
models.signals.post_save.connect(company_initial_data_create, sender=Company)
models.signals.post_save.connect(increase_user_unread_notifs_count, sender=ActivityNotification)
models.signals.post_delete.connect(reduce_user_unread_notifs_count, sender=ActivityNotification)

models.signals.pre_save.connect(clear_text, sender=ExpenseClaim)
models.signals.pre_save.connect(clear_text, sender=ExpenseClaimProject)
models.signals.pre_save.connect(clear_text, sender=Mileage)
models.signals.pre_save.connect(clear_text, sender=Order)
models.signals.pre_save.connect(clear_text, sender=Activity)
models.signals.pre_save.connect(clear_text, sender=User)

