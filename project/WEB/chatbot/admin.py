from django.contrib import admin
from .models import FredData, CardSales, ChatbotCardMembers, FranchiseData, TravelCaution, TourIntrst, CurrencyRate

admin.site.register(FredData)
admin.site.register(CardSales)
admin.site.register(ChatbotCardMembers)
admin.site.register(FranchiseData)

admin.site.register(TravelCaution)
admin.site.register(TourIntrst)
admin.site.register(CurrencyRate)
