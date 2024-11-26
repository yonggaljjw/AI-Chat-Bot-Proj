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


def dashboard_view(request):
    """main.html과 연동 + /index에서 확인"""
    # 우리카드 데이터 분석 - 호섭
    top10_level_json = top10_level_view()
    lifestage_distribution_json = lifestage_distribution_view()
    age_dist_json, lifestage_dist_json = age_and_life_stage_distribution_view()
    male_chart_json, female_chart_json = gender_expense_distribution_view()
    age_payment_json = age_payment_distribution_view()
    age_category_json = age_category_top5_view()
    # 거시경제 지표 - 지연
    gdp_rates_json = gdp_and_rates_view()
    price_indicators_json = price_indicators_view()
    consumer_trends_json = consumer_trends_view()
    employment_trends_json = employment_trends_view()
    economic_table_json = economic_indicators_table_view()
    # 카드사 매출 정보 - 지연
    card_total_sales_ladar_json =  card_total_sales_ladar_view()
    create_card_heatmap_json = create_card_heatmap_view()
    wooricard_sales_treemap_json = wooricard_sales_treemap_view()
    # 법 - 은지
    korean_law_html = korean_law_view()

    # 템플릿에 전달
    return render(request, "main.html", {
        # 우리카드 데이터 분석 - 호섭
        "top10_level_json" : top10_level_json,
        "lifestage_distribution_json" : lifestage_distribution_json,
        "age_dist_json" : age_dist_json,
        "lifestage_dist_json" : lifestage_dist_json,
        "male_chart_json" : male_chart_json,
        "female_chart_json" : female_chart_json,
        "age_payment_json" : age_payment_json,
        "age_category_json" : age_category_json,
        # 거시경제 지표 - 지연
        "gdp_rates_json": gdp_rates_json,
        "price_indicators_json": price_indicators_json,
        "consumer_trends_json": consumer_trends_json,
        "employment_trends_json": employment_trends_json,
        "economic_table_json": economic_table_json,
        # 법 - 은지
        "korean_law_html" : korean_law_html,
        # 카드사 매출 정보 - 지연
        "card_total_sales_ladar_json" : card_total_sales_ladar_json,
        "create_card_heatmap_json" : create_card_heatmap_json,
        "wooricard_sales_treemap_json" : wooricard_sales_treemap_json,
        })


# 캐시 데코레이터 추가 (60*60*24 = 24시간)
@cache_page(60 * 60)  
def dashboard_view_practice(request):
    """tmp와 연동 + /tmp에서 확인"""
    # 카드 소비 카테고리 - 호섭
    gender_json = gender_view()
    # 카드사 매출 정보 - 지연
    card_total_sales_ladar_json =  card_total_sales_ladar_view()
    create_card_heatmap_json = create_card_heatmap_view()
    wooricard_sales_treemap_json = wooricard_sales_treemap_view()
    # 법 - 은지
    korean_law_html = korean_law_view()
    # 여행
    tour_servey_json = tour_servey()
    visualize_travel_advice_html = visualize_travel_advice()
    travel_trend_line_json = travel_trend_line()
    # 환율
    currency_rates_json = create_currency_view()
    # indicator
    bankrate_indicator_json = bankrate_indicator()
    K_GDP_indicator_json = K_GDP_indicator()
    K_cpi_indicator_json = K_cpi_indicator()
    K_pce_indicator_json = K_pce_indicator()
    K_USD_indicator_json = K_USD_indicator()
    K_growth_indicator_json = K_growth_indicator()
    #
    cpi_card_predict_json = cpi_card_predict_view()
    # 거시경제 지표 - 지연
    economic_indicators_table_json = economic_indicators_table_view()
    gdp_rates_json = gdp_and_rates_view()
    price_indicators_json = price_indicators_view()
    consumer_trends_json = consumer_trends_view()
    employment_trends_json = employment_trends_view()

    # 템플릿에 전달
    return render(request, "tmp.html", {
        "gender_json": gender_json,
        # 카드사 매출 정보 - 지연
        "card_total_sales_ladar_json" : card_total_sales_ladar_json,
        "create_card_heatmap_json" : create_card_heatmap_json,
        "wooricard_sales_treemap_json" : wooricard_sales_treemap_json,
        # 법 - 은지
        "korean_law_html": korean_law_html,
        "tour_servey_json":tour_servey_json,
        "visualize_travel_advice_html" : visualize_travel_advice_html,
        "travel_trend_line_json" : travel_trend_line_json,
        # 환율
        "currency_rates_json" : currency_rates_json,
        # indicator
        "bankrate_indicator_json" : bankrate_indicator_json,
        "K_GDP_indicator_json" : K_GDP_indicator_json,
        "K_cpi_indicator_json" : K_cpi_indicator_json,
        "K_pce_indicator_json" : K_pce_indicator_json,
        "K_USD_indicator_json" : K_USD_indicator_json,
        "K_growth_indicator_json" : K_growth_indicator_json,
        #
        "cpi_card_predict_json" : cpi_card_predict_json,
        # 거시경제 지표 - 지연
        "gdp_rates_json": gdp_rates_json,
        "price_indicators_json": price_indicators_json,
        "consumer_trends_json": consumer_trends_json,
        "employment_trends_json": employment_trends_json,
        "economic_indicators_table_json" : economic_indicators_table_json,
    })

def dashboard_view_practice2(request):
    """tmp_origin과 연동 + /tmp_origin에서 확인"""
    '''거시경제 대시보드 차트 구현 시각화 함수 넣어주세요'''
    cpi_card_predict_html = cpi_card_predict_view()
    K_cpi_indicator_html = K_cpi_indicator()
    K_pce_indicator_html = K_pce_indicator()
    bankrate_indicator_html = bankrate_indicator()
    K_GDP_indicator_html = K_GDP_indicator()
    K_growth_indicator_html = K_growth_indicator()
    K_USD_indicator_html = K_USD_indicator()
    economic_indicators_table_html = economic_indicators_table_view()

    # 템플릿에 전달
    return render(request, "tmp_origin.html", {
        "cpi_card_predict_html" : cpi_card_predict_html,
        "K_cpi_indicator_html" : K_cpi_indicator_html,
        "K_pce_indicator_html" : K_pce_indicator_html
    })
