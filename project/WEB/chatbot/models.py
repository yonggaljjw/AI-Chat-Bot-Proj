from django.db import models

# Create your models here.

class Fred(models.Model) :
    date = models.DateField()
    FFTR = models.FloatField()
    GDP = models.FloatField()
    GDP_Growth_Rate = models.FloatField()
    PCE = models.FloatField()
    CPI = models.FloatField()
    Core_CPI = models.FloatField()
    Personal_Income = models.FloatField()
    Unemployment = models.FloatField()
    ISM_Manufacturing = models.FloatField()
    Durable_Goods_Orders = models.FloatField()
    Building_Permits = models.FloatField()
    Retail_Sales = models.FloatField()
    Consumer_Sentiment = models.FloatField()
    Nonfarm_Payrolls = models.FloatField()
    JOLTS_Hires = models.FloatField()
    
    class Meta :
        managed = False
        db_table = "fred_data"


class card_sales(models.Model) :
    대분류 = models.TextField()
    카드_종류 = models.TextField()
    사용구분 = models.TextField()
    결제_방법 = models.TextField()
    롯데카드 = models.FloatField()
    비씨카드 = models.FloatField()
    삼성카드 = models.FloatField()
    신한카드 = models.FloatField()
    우리카드 = models.FloatField()
    하나카드 = models.FloatField()
    현대카드 = models.FloatField()
    KB국민카드 = models.FloatField()
    합계 = models.FloatField()
    date = models.DateField()

    class Meta :
        managed = False
        db_table = "card_sales"

class card_members(models.Model) :
    대분류 = models.TextField()
    카드_종류 = models.TextField()
    사용구분 = models.TextField()
    결제_방법 = models.TextField()
    롯데카드 = models.FloatField()
    비씨카드 = models.FloatField()
    삼성카드 = models.FloatField()
    신한카드 = models.FloatField()
    우리카드 = models.FloatField()
    하나카드 = models.FloatField()
    현대카드 = models.FloatField()
    KB국민카드 = models.FloatField()
    date = models.DateField()

    class Meta :
        managed = False
        db_table = "card_members"


class wooricard(models.Model) :
    고객번호 = models.TextField()
    연령대 = models.FloatField()
    성별 = models.TextField()
    회원등급 = models.TextField()
    라이프스테이지 = models.TextField()
    총이용금액 = models.FloatField()
    신용카드이용금액 = models.FloatField()
    체크카드이용금액 = models.FloatField()
    가전_가구_주방용품 = models.FloatField()
    보험_병원 = models.FloatField()
    사무통신_서적_학원 = models.FloatField()
    여행_레져_문화 = models.FloatField()
    요식업 = models.FloatField()
    용역_수리_건축자재 = models.FloatField()
    유통 = models.FloatField()
    보건위생 = models.FloatField()
    의류_신변잡화 = models.FloatField()
    자동차_연료_정비 = models.FloatField()
    가구 = models.FloatField()
    가전제품 = models.FloatField()
    건물및시설관리 = models.FloatField()
    건축_자재 = models.FloatField()
    광학제품 = models.FloatField()
    농업 = models.FloatField()
    레져업소 = models.FloatField()
    레져용품 = models.FloatField()
    문화_취미 = models.FloatField()
    보건_위생 = models.FloatField()
    보험 = models.FloatField()
    사무_통신기기 = models.FloatField()
    서적_문구 = models.FloatField()
    수리서비스 = models.FloatField()
    숙박업 = models.FloatField()
    신변잡화 = models.FloatField()
    여행업 = models.FloatField()
    연료판매 = models.FloatField()
    용역서비스 = models.FloatField()
    유통업비영리 = models.FloatField()
    유통업영리 = models.FloatField()
    음식료품 = models.FloatField()
    의료기관 = models.FloatField()
    의료기관 = models.FloatField()
    의류 = models.FloatField()
    일반_휴게음식 = models.FloatField()
    자동차정비_유지 = models.FloatField()
    자동차판매 = models.FloatField()
    주방용품 = models.FloatField()
    직물 = models.FloatField()
    학원 = models.FloatField()
    회원제형태업소 = models.FloatField()

    class Meta :
        managed = False
        db_table = "wooricard"


class franchise_data(models.Model) :
    yr = models.TextField()
    indutyLclasNm = models.TextField()
    indutyMlsfcNm = models.TextField()
    corpNm = models.TextField()
    brandNm = models.TextField()
    frcsCnt = models.FloatField()
    newFrcsRgsCnt = models.FloatField()
    ctrtEndCnt = models.FloatField()
    ctrtCncltnCnt = models.FloatField()
    nmChgCnt = models.FloatField()
    avrgSlsAmt = models.FloatField()
    arUnitAvrgSlsAmt = models.FloatField()
    date = models.DateField()

    class Meta :
        managed = False
        db_table = "franchise_data"


class tour_intrst(models.Model) :
    RESPOND_ID = models.TextField()
    EXAMIN_BEGIN_DE = models.DateField()
    SEXDSTN_FLAG_CD = models.TextField()
    AGRDE_FLAG_NM = models.TextField()
    ANSWRR_OC_AREA_NM = models.TextField()
    HSHLD_INCOME_DGREE_NM = models.TextField()
    CHINA_TOUR_INTRST_VALUE = models.TextField()
    JP_TOUR_INTRST_VALUE = models.TextField()
    HONGKONG_MACAU_TOUR_INTRST_VALUE = models.TextField()
    SEASIA_TOUR_INTRST_VALUE = models.TextField()
    MDLEST_SWASIA_TOUR_INTRST_VALUE = models.TextField()
    USA_CANADA_TOUR_INTRST_VALUE = models.TextField()
    SAMRC_LAMRC_TOUR_INTRST_VALUE = models.TextField()
    WEURP_NEURP_TOUR_INTRST_VALUE = models.TextField()
    EEURP_TOUR_INTRST_VALUE = models.TextField()
    SEURP_TOUR_INTRST_VALUE = models.TextField()
    SPCPC_TOUR_INTRST_VALUE = models.TextField()
    AFRICA_TOUR_INTRST_VALUE = models.TextField()

    class Meta :
        managed = False
        db_table = "tour_intrst"


class travel_caution(models.Model) :
    Country = models.TextField()
    Travel_Caution = models.BinaryField()
    Travel_Restriction = models.BinaryField()
    Departure_Advisory = models.BinaryField()
    Travel_Ban = models.BinaryField()
    Special_Travel_Advisory = models.BinaryField()

    class Meta : 
        managed = False
        db_table = 'travel_caution'


class currency_rate(models.Model) :
    cur_unit = models.TextField()
    ttb = models.FloatField()
    tts = models.FloatField()
    deal_bas_r = models.FloatField()
    bkpr = models.FloatField()
    yy_efee_r = models.FloatField()
    ten_dd_efee_r = models.FloatField()
    kftc_bkpr = models.FloatField()
    kftc_deal_bas_r = models.FloatField()
    cur_nm = models.TextField()
    date = models.DateField()

    class Meta : 
        managed = False
        db_table = "currency_rate"