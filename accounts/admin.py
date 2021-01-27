from django.contrib import admin

from .models import BotSetting


@admin.register(BotSetting)
class BotSettingAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'started')