from django.contrib import admin
from .models import Fred, card_sales, card_members, franchise_data
from .models import travel_caution, tour_intrst, currency_rate
from .models import wooricard

admin.site.register(Fred)
admin.site.register(card_sales)
admin.site.register(card_members)
admin.site.register(franchise_data)

admin.site.register(travel_caution)
admin.site.register(tour_intrst)
admin.site.register(currency_rate)


admin.site.register(wooricard)
