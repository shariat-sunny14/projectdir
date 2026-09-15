from django.db import models


class Testimonial(models.Model):
    """
    Ekta testimonial entry — client er nam (couple name), message, ebong
    tader avatar/image. is_approved False thakle website a show korbe na,
    admin approve korle tarpor show korbe.
    """
    couple_name = models.CharField(
        max_length=150,
        help_text="Example: Morsheda & Saquib"
    )
    message = models.TextField(
        help_text="Client er testimonial text"
    )
    image = models.ImageField(
        upload_to="testimonials/",
        blank=True,
        null=True,
        help_text="Client er round avatar image (optional)"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Approved na hoile website a show hobe na"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Testimonial"
        verbose_name_plural = "Testimonials"

    def __str__(self):
        return self.couple_name