from django.contrib import admin
from running_app.models import UserProfile

# class CountryAdmin(admin.ModelAdmin):
#     prepopulated_fields = {'slug':('name',)}
#     exclude = ('demonym', 'population', 'capital')
#     list_display = ('name', 'partyInPower', 'startDate', 'titleOfHead', 'headOfState', 'description')
#
# class PolicyAdmin(admin.ModelAdmin):
#     list_display = ('id', 'subject', 'country', 'status', 'category')
#
#
# admin.site.register(Country, CountryAdmin)
# admin.site.register(Policy, PolicyAdmin)
# admin.site.register(Category)
admin.site.register(UserProfile)
