from django.db import models
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model

from slugify import UniqueSlugify

from chronowiz.core.models import TextDescriptionMixin, TimestampsMixin
from chronowiz.watches.utils import slugify_wrapper
from .watch import Watch, SLUG_HELP_TEXT

User = get_user_model()

ORDER_STATUS_CHOICES = (('DRAFT', 'draft'), ('IN_PROCESS', 'in process'),
                        ('SUCCESS', 'success'), ('FAILURE', 'failure'))


class WatchInTray(models.Model, TimestampsMixin):
    watch = models.OneToOneField(
        Watch, related_name='watch_in_tray', on_delete=models.CASCADE)
    added_times = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('-added_times', )

    def __str__(self):
        return self.watch.model

    def increment_added_times(self):
        self.added_times += 1
        self.save()


class OrderItem(models.Model, TimestampsMixin):
    watch = models.ForeignKey(
        Watch, related_name='order_item', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ('-quantity', )

    def __str__(self):
        return f'{self.watch.model} - {self.quantity}'


class Order(models.Model, TimestampsMixin):
    order_items = models.ManyToManyField(OrderItem, related_name='orders')
    customer = models.ForeignKey(
        User,
        related_name='orders',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)
    status = models.CharField(
        max_length=10, choices=ORDER_STATUS_CHOICES, default='DRAFT')
    stripe = models.CharField(max_length=255, blank=True, null=True)
    escrow = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ('status', )

    def __str__(self):
        return str(self.id)


class Brand(models.Model):
    name = models.CharField(max_length=30, unique=True)
    logo = models.ImageField(upload_to='brands_logos', blank=True, null=True)
    banner = models.ImageField(
        upload_to='brands_banners', blank=True, null=True)
    slug = models.SlugField(
        max_length=50, unique=True, blank=True, help_text=SLUG_HELP_TEXT)

    class Meta:
        ordering = ('name', )

    def __str__(self):
        return self.name


class Family(models.Model):
    name = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name_plural = 'Families'

    def __str__(self):
        return self.name


class WatchBanner(models.Model):
    image = models.ImageField(upload_to='watch_banners')
    watch = models.ForeignKey(
        'Watch', related_name='watch_banners', on_delete=models.CASCADE)

    class Meta:
        ordering = ('id', )

    def __str__(self):
        return self.watch.model


class Discount(models.Model):
    value = models.IntegerField()
    is_active = models.BooleanField(default=False)
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, related_name='discounts')

    class Meta:
        unique_together = ('value', 'brand')

    def __str__(self):
        return f'{self.brand.name}-{self.value}'


class RetailerWatchInfo(models.Model):
    watch = models.ForeignKey('Watch', on_delete=models.CASCADE)
    retailer = models.ForeignKey(User, on_delete=models.CASCADE)
    availability = models.BooleanField(default=False)
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        related_name='discounts')

    class Meta:
        unique_together = ('watch', 'retailer', 'discount')

    def __str__(self):
        return self.watch.model


class WatchDescription(TextDescriptionMixin):
    watch = models.ForeignKey(
        'Watch', related_name='watch_description', on_delete=models.CASCADE)
    image = models.ImageField(
        blank=True, null=True, upload_to='watch_descriptions')
    is_carousel_item = models.BooleanField(
        help_text=(
            'If checked then the item will be shown only in a carousel. '
            'In this case if an image is uploaded text fields '
            'will be ommited. Otherwise all fields will be displayed '
            'as a row in a static description section'))

    class Meta:
        ordering = (
            'id',
            'is_carousel_item',
        )


class MovementDetail(models.Model):
    detail = models.CharField(max_length=255)
    watch = models.ForeignKey(
        'Watch', related_name='movement_details', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('detail', 'watch')

    def __str__(self):
        return self.detail


class WatchFunctionName(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class WatchFunction(models.Model):
    watch_function_name = models.ForeignKey(
        WatchFunctionName,
        related_name='watch_functions',
        on_delete=models.CASCADE)
    watch = models.ForeignKey(
        'Watch', related_name='functions', on_delete=models.CASCADE)

    class Meta:
        unique_together = (
            'watch_function_name',
            'watch',
        )

    def __str__(self):
        return self.watch_function_name.name


def pre_save_gen_slug_receiver(sender, instance, **kwargs):
    slugify_unique = UniqueSlugify(
        unique_check=slugify_wrapper(sender), to_lower=True)
    slug_source_field = 'model' if isinstance(instance, Watch) else 'name'
    if not instance.slug:
        instance.slug = slugify_unique(getattr(instance, slug_source_field))


pre_save.connect(pre_save_gen_slug_receiver, sender=Family)
pre_save.connect(pre_save_gen_slug_receiver, sender=Brand)
pre_save.connect(pre_save_gen_slug_receiver, sender=Watch)
