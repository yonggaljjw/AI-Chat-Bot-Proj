from .views_fred import *
from .views_card_sales import *
from .views_hoseop import *
from .views_law import *
from .veiws_cautions_map import *
from .views_tour import *
from .views_travel_trend import *
from .views_currency import *
from .views_indicator import *
from .views_fred import *
from django.views.decorators.cache import cache_page
import secrets
from django.contrib.auth.decorators import login_required


# 캐시 데코레이터 추가 (60*60*24 = 24시간)
@cache_page(60 * 60)
@login_required
def dashboard_view(request):
    """tmp와 연동 + /tmp에서 확인"""
    nonce = secrets.token_hex(16)
    context = {
        'nonce': nonce,
        # 카드 소비 카테고리 - 호섭
        "gender_json": gender_view(),
        # 카드사 매출 정보 - 지연
        "card_total_sales_ladar_json" :  card_total_sales_ladar_view(),
        "create_card_heatmap_json" : create_card_heatmap_view(),
        "wooricard_sales_treemap_json" : wooricard_sales_treemap_view(),
        # 법 - 은지
        "korean_law_html": korean_law_view(),
        # 여행
        "tour_servey_json": tour_servey(),
        "visualize_travel_advice_json" : visualize_travel_advice(),
        "travel_trend_line_json" : travel_trend_line(),
        # 환율
        "currency_rates_json" : create_currency_view(),
        # indicator
        "bankrate_indicator_json" : bankrate_indicator(),
        "K_GDP_indicator_json" : K_GDP_indicator(),
        "K_cpi_indicator_json" : K_cpi_indicator(),
        "K_pce_indicator_json" : K_pce_indicator(),
        "K_USD_indicator_json" : K_USD_indicator(),
        "K_growth_indicator_json" : K_growth_indicator(),
        #
        "cpi_card_predict_json" : cpi_card_predict_view(),
        # 거시경제 지표 - 지연
        "gdp_rates_json": gdp_and_rates_view(),
        "price_indicators_json": price_indicators_view(),
        "consumer_trends_json": consumer_trends_view(),
        "employment_trends_json": employment_trends_view(),
        "economic_indicators_table_json" : economic_indicators_table_view(),
    }
    response = render(request, "main.html", context)
    response['Content-Security-Policy'] = f"script-src 'self' 'unsafe-eval' 'nonce-{nonce}' https://cdn.tailwindcss.com https://cdn.plot.ly;"
    return response
