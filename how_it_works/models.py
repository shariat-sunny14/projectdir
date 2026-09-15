from django.core.exceptions import ValidationError
from django.db import models


class ProcessSection(models.Model):
    """
    Singleton model — শুধু ১টা row থাকবে।
    এইখানে section এর kicker ("How it works") আর heading
    ("From first message to final gallery") রাখা হয়।
    """
    kicker = models.CharField(
        max_length=100,
        default="How it works",
        help_text="ছোট লেবেল, যেমন: How it works",
    )
    heading = models.CharField(
        max_length=200,
        default="From first message to final gallery",
        help_text="মূল H2 heading",
    )
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Process Section (Heading)"
        verbose_name_plural = "Process Section (Heading)"

    def __str__(self):
        return self.heading

    def save(self, *args, **kwargs):
        # সবসময় ১টাই instance থাকবে (singleton pattern)
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # ডিলিট হবে না

    @classmethod
    def load(cls):
        obj, _created = cls.objects.get_or_create(pk=1)
        return obj


class ProcessStep(models.Model):
    """
    একেকটা step card (01, 02, 03, 04 ...)
    """
    step_number = models.PositiveIntegerField(
        help_text="ধাপের নাম্বার, যেমন: 1, 2, 3 (অটো 01, 02 আকারে দেখাবে)"
    )
    title = models.CharField(max_length=150)
    description = models.TextField()
    order = models.PositiveIntegerField(
        default=0,
        help_text="সিরিয়াল অনুযায়ী সাজানোর জন্য (ছোট নাম্বার আগে দেখাবে)",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "step_number"]
        verbose_name = "Process Step"
        verbose_name_plural = "Process Steps"

    def __str__(self):
        return f"{self.formatted_step_number} - {self.title}"

    @property
    def formatted_step_number(self):
        """01, 02, 03 ... আকারে দেখানোর জন্য"""
        return f"{self.step_number:02d}"

    def clean(self):
        # একই step_number দুইবার active অবস্থায় থাকতে পারবে না (optional validation)
        qs = ProcessStep.objects.filter(
            step_number=self.step_number, is_active=True
        ).exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                {"step_number": "এই step number দিয়ে ইতিমধ্যে একটা active step আছে।"}
            )
