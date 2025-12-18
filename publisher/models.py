from django.db import models
from cloudinary.models import CloudinaryField

# Create your models here.


class Publisher(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    founded_year = models.IntegerField(blank=True, null=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    logo = CloudinaryField('image', default='placeholder')
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        from django.utils.text import slugify
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def games_count(self):
        """Return the number of reviews (games) associated with this
        publisher"""
        return self.reviews.count()

    @property
    def country(self):
        """Placeholder for country field - can be added later if needed"""
        return "-"

    @property
    def founded(self):
        """Return founded year for template compatibility"""
        return self.founded_year
