from django.contrib import admin
from .models import Answer, Question

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['name']
