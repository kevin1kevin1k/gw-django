from django.db import models
from django.core.urlresolvers import reverse

# Create your models here.

class Answer(models.Model):
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('answer_detail', kwargs={'pk': self.pk})

class Question(models.Model):
    answer = models.ForeignKey('Answer', related_name='questions')
    name = models.CharField(max_length=20)
    
    def __str__(self):
        return self.name
    