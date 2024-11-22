from .views_fred import *
from .views_card_sales import *
from .views_hoseop import *
from .views_law import *
from .veiws_cautions_map import *
from .views_tour import *
# from .views_eunchae import *


def dashboard_view(request):
    # 우리카드 데이터 분석 - 호섭
    top10_level_html = top10_level_view()
    lifestage_distribution_html = lifestage_distribution_view()
    age_dist_html, lifestage_dist_html = age_and_life_stage_distribution_view()
    male_chart_html, female_chart_html = gender_expense_distribution_view()
    age_payment_html = age_payment_distribution_view()
    age_category_html = age_category_top5_view()
    # 거시경제 지표 - 지연
    gdp_rates_html = gdp_and_rates_view()
    price_indicators_html = price_indicators_view()
    consumer_trends_html = consumer_trends_view()
    employment_trends_html = employment_trends_view()
    economic_table_html = economic_indicators_table_view()
    # 카드사 매출 정보 - 지연
    card_total_sales_ladar_html =  card_total_sales_ladar_view()
    create_card_heatmap_html = create_card_heatmap_view()
    wooricard_sales_treemap_html = wooricard_sales_treemap_view()
    # 법 - 은지
    korean_law_html = korean_law_view()

    # 템플릿에 전달
    return render(request, "main.html", {
        # 우리카드 데이터 분석 - 호섭
        "top10_level_html" : top10_level_html,
        "lifestage_distribution_html" : lifestage_distribution_html,
        "age_dist_html" : age_dist_html,
        "lifestage_dist_html" : lifestage_dist_html,
        "male_chart_html" : male_chart_html,
        "female_chart_html" : female_chart_html,
        "age_payment_html" : age_payment_html,
        "age_category_html" : age_category_html,
        # 거시경제 지표 - 지연
        "gdp_rates_html": gdp_rates_html,
        "price_indicators_html": price_indicators_html,
        "consumer_trends_html": consumer_trends_html,
        "employment_trends_html": employment_trends_html,
        "economic_table_html": economic_table_html,
        "korean_law_html" : korean_law_html,
                # 카드사 매출 정보 - 지연
        "card_total_sales_ladar_html" : card_total_sales_ladar_html,
        "create_card_heatmap_html" : create_card_heatmap_html,
        "wooricard_sales_treemap_html" : wooricard_sales_treemap_html,
 
        })


def dashboard_view_practice(request):
    # 카드 소비 카테고리 - 호섭
    gender_html = gender_view()
    # 카드사 매출 정보 - 지연
    card_total_sales_ladar_html =  card_total_sales_ladar_view()
    create_card_heatmap_html = create_card_heatmap_view()
    wooricard_sales_treemap_html = wooricard_sales_treemap_view()
    # 법 - 은지
    korean_law_html = korean_law_view()
    # 여행
    tour_servey_html = tour_servey()
    visualize_travel_advice_html = visualize_travel_advice(),

    # 템플릿에 전달
    return render(request, "tmp.html", {
        "gender_html": gender_html,
        # 카드사 매출 정보 - 지연
        "card_total_sales_ladar_html" : card_total_sales_ladar_html,
        "create_card_heatmap_html" : create_card_heatmap_html,
        "wooricard_sales_treemap_html" : wooricard_sales_treemap_html,
        # 법 - 은지
        "korean_law_html": korean_law_html,
        "tour_servey_html":tour_servey_html,
        "visualize_travel_advice_html" : visualize_travel_advice_html,
    })
