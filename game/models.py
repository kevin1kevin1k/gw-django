from django.db import models
from django.core.urlresolvers import reverse

class Answer(models.Model):
    name = models.CharField(max_length=20)
    name_en = models.CharField(max_length=20, default='NULL')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('answer_detail', kwargs={'pk': self.pk})

class Game(models.Model):
    '''record each game'''
    user_id = models.IntegerField(default=0)
    created_time = models.DateTimeField(auto_now_add=True)
    answer = models.ForeignKey('Answer', related_name='games')
    is_finished = models.BooleanField(default=False)
    hint_used = models.CharField(max_length=20, default='None')
    original_questions = models.ManyToManyField('Original_Question')

class Question(models.Model):
    game = models.ForeignKey('Game', related_name='questions', null=True)
    content =  models.CharField(max_length=100, blank=True) # question content
    label = models.CharField(max_length=5, blank=True) # yes or no
    source = models.CharField(max_length=10, blank=True) # the result is given by which component
    confidence_score = models.FloatField(default=0)
    created_time = models.DateTimeField(auto_now_add=True)
    
    def __unicode__(self):
        return self.content

class Original_Question(models.Model):
    content = models.CharField(default=' ', max_length=100, primary_key=True)
    parsed_result = models.CharField(max_length=200, blank=True)
    
