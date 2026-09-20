# what_we_do/models.py
from django.db import models
from django.core.validators import MinLengthValidator


class Service(models.Model):
    number = models.PositiveSmallIntegerField(
        unique=True,
        help_text="Card এ 01, 02 এভাবে দেখানোর জন্য ক্রম (order)"
    )
    title = models.CharField(max_length=150)
    description = models.TextField(validators=[MinLengthValidator(10)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['number']
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return f"{self.number:02d} - {self.title}"

    @property
    def display_number(self):
        return f"{self.number:02d}"


class ServiceSection(models.Model):
    kicker_text = models.CharField(max_length=100, default="What we do")
    heading = models.CharField(
        max_length=255,
        default="Services built around how Bangladeshi celebrations actually unfold"
    )
    sub_text = models.TextField(
        default="Pick a single day of coverage or hand us the whole calendar — holud through walima."
    )

    class Meta:
        verbose_name = "Service Section (Heading)"
        verbose_name_plural = "Service Section (Heading)"

    def __str__(self):
        return "Services Section Content"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj