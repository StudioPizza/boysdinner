from django.contrib import admin
from .models import Boy, Dinner, Attendance


# Register your models here.
class AttendanceInline(admin.TabularInline):
    model = Attendance
    extra = 1
    autocomplete_fields = ("boy",)
    # fields shown per row in the inline
    fields = ("boy", "status")



@admin.register(Boy)
class BoyAdmin(admin.ModelAdmin):
    list_display = ("name", "nickname", "birthday", "reliability", "last_hosted")
    search_fields = ("name", "nickname")

@admin.register(Dinner)
class DinnerAdmin(admin.ModelAdmin):
    list_display = ("date", "restaurant", "host")
    search_fields = ("restaurant", "host__name")
    list_select_related = ("host",)
    inlines = [AttendanceInline]

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("dinner", "boy", "status")
    list_filter = ("status",)      # ← tuple, not string
    autocomplete_fields = ("dinner", "boy")