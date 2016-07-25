from django.db import models
from django.core.urlresolvers import reverse

# Create your models here.

class Store(models.Model):
    name = models.CharField(max_length=20)
    notes = models.TextField(blank=True, default='')

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store_detail', kwargs={'pk': self.pk})

class MenuItem(models.Model):
    store = models.ForeignKey('Store', related_name='menu_items')
    name = models.CharField(max_length=20)
    price = models.IntegerField()

    def __str__(self):
        return self.name
