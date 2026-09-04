from django.db import models

class AboutUs(models.Model):
    header = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"AboutUs {self.id}"

class TeamMember(models.Model):
    name = models.CharField(max_length=200)
    designation = models.CharField(max_length=200)
    image = models.ImageField(upload_to='team/')
    
    facebook = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Award(models.Model):
    image = models.ImageField(upload_to='awards/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Award {self.id}"


class Certificate(models.Model):
    image = models.ImageField(upload_to='certificates/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate {self.id}"
    
    
class LifeAtOur(models.Model):
    header = models.CharField(max_length=200)
    description = models.TextField()
    iframe_code = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"LifeAtOur {self.id}"