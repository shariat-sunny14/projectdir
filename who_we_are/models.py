# models.py
from django.db import models


class WhoWeAreQuerySet(models.QuerySet):
    def delete(self, *args, **kwargs):
        # Bulk delete (queryset.delete()) o block kore dilam,
        # shudhu instance.delete() na, .all().delete() theke o protect thakbe
        return 0, {}


class WhoWeAreManager(models.Manager):
    def get_queryset(self):
        return WhoWeAreQuerySet(self.model, using=self._db)


class WhoWeAre(models.Model):
    """
    Singleton model.
    Ekhane shudhu EKTA row/data thakbe (pk=1 always).
    Multiple entry create kora jabe na — save() overridden.
    """

    # ---- LEFT SIDE (about-copy) ----
    kicker_text = models.CharField(
        max_length=100, default="Who we are"
    )
    subtitle = models.CharField(
        max_length=150, default="Bridal Harmony", help_text="H3 text"
    )
    title_main = models.CharField(
        max_length=200,
        default="Premium Class Photography",
        help_text="H2 er age er part",
    )
    title_highlight = models.CharField(
        max_length=50, default="&", help_text="<em> tag er bhitorer text"
    )
    title_after = models.CharField(
        max_length=200,
        default="Cinematography Services",
        help_text="H2 er pore er part",
    )
    description = models.TextField(
        default="Bridal Harmony is a team of experienced professional photographers, "
        "cinematographers and photo-book experts dedicated to creating stunning, "
        "authentic stories of people's lives."
    )
    note = models.TextField(
        default="From intimate family moments to grand celebrations, we capture "
        "every frame with intention, emotion and cinematic detail."
    )

    # ---- RIGHT SIDE (stats-section intro) ----
    stats_intro_label = models.CharField(max_length=100, default="Our journey")
    stats_intro_text = models.TextField(
        default="More than a decade of capturing moments across Bangladesh."
    )

    updated_at = models.DateTimeField(auto_now=True)

    objects = WhoWeAreManager()

    class Meta:
        verbose_name = "Who We Are"
        verbose_name_plural = "Who We Are"

    def save(self, *args, **kwargs):
        # Forcefully lock pk to 1 -> shob shomoy ekta e row thakbe
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete disable kore dilam, singleton row thake jate accidentally
        # delete na hoye jay
        pass

    @classmethod
    def load(cls):
        """View theke ei method diye object load korben.
        Kono data na thakle nijei ekta default row create kore dibe.
        """
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "Who We Are Content"


class StatCard(models.Model):
    """
    stats-grid er protita card (Since / Events / Photos / Happy Clients).
    WhoWeAre er sathe ForeignKey diye jukto — jate koyta card lagbe
    seta admin theke add/remove kora jay, kintu WhoWeAre nijei singleton.
    """

    about = models.ForeignKey(
        WhoWeAre, related_name="stats", on_delete=models.CASCADE
    )
    label = models.CharField(
        max_length=50, help_text="e.g. Since, Events, Photos, Happy Clients"
    )
    target_number = models.PositiveIntegerField(
        help_text="Counter animation er target value, e.g. 2013, 6000, 800, 40"
    )
    suffix = models.CharField(
        max_length=10,
        blank=True,
        help_text="e.g. +  or  k+ (khali rakhle kichu dekhabe na)",
    )
    is_featured = models.BooleanField(
        default=False, help_text="stat-featured class add hobe kina"
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Stat Card"
        verbose_name_plural = "Stat Cards"

    def __str__(self):
        return f"{self.label} - {self.target_number}{self.suffix or ''}"