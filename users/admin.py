from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'manager_de')
    list_filter = ('manager_de',)
    search_fields = ('user__username',)

