import re
import numpy as np
import pandas as pd
import requests   #웹통신
import json
from pmdarima.arima import ndiffs
import pmdarima as pm
from pykrx import stock
from bs4 import BeautifulSoup
import html5lib


#                   ==============
#                      업종 분류
#                   ==============
# -------- 동일 업종 기업 출력
# TODO(미완성) 동일 업종 선택
def select_same_industry(corp_name):
    indus=com_df[com_df['nm']==corp_name]['industry'].values[0] # TODO(df 확인)

    # print(com_df.groupby(by='industry')['nm'].nunique().max()) # 동종업계 최대 151개 -> 151개 재무제표 크롤링?

    list_com=com_df[com_df['industry']==indus]['corp_name'].values.tolist()
    return list_com



#  -------- 네이버증권 연관기업 코드(hjh)
def relate_code_crawl(co):
    #연관 종목코드 있는 페이지 불러오기
    url='https://finance.naver.com/item/main.naver?code='+str(co)
    page=pd.read_html(url,encoding='CP949')
    #연관 종목명과 종목코드 뽑아내기(code_list[0]은 '종목명'이어서 제외)
    code_list=page[4].columns.tolist()
    code_list=code_list[1:]
    #종목코드 리스트 반환
    codes=[]
    for word in (code_list):
        codes.append(word[-6:])
    #print(codes)
    return codes

#relate_code_crawl('000660')



#                   ==============
#                  기업 이름 코드 변환
#                   ==============

# -------- 네이버 재무제표 크롤링 용 gicode로 변환
def nm_to_bs_gicode(corp_name):
    gi=com_df[com_df['nm']==corp_name]['cd']
    gi=gi.values[0]
    return gi



def stc_code_to_bs_gicode(stock_code):
    gi = com_df[com_df['stock_code'] == stock_code]['cd']
    gi = gi.values[0]
    return gi



def yh_code_to_bs_gicode(yh_code):
    gi = com_df[com_df['yh_code'] == yhcode]['cd']
    gi = gi.values[0]
    return gi



# -------- 네이버 금융 크롤링 용 gicode로 변환
def nm_to_fn_gicode(corp_name):
    gi=com_df[com_df['nm']==corp_name]['stock_code']
    gi=gi.values[0]
    return gi



def yh_code_to_fn_gicode(yh_code):
    gi=com_df[com_df['yh_code']==yh_code]['stock_code']
    gi=gi.values[0]
    return gi



# -------- 코드를 기업이름으로 변환
def stc_code_to_nm(stock_code):
    gi = com_df[com_df['stock_code'] == stock_code]['nm']
    gi = gi.values[0]
    return gi



def yh_code_to_nm(yh_code):
    gi = com_df[com_df['yh_code'] == yh_code]['nm']
    gi = gi.values[0]
    return gi



#                   ==============
#                     데이터 수집
#                   ==============


# -------- Balance Sheets API call
# def bs_api(corp_name=None, yh_code=None, stock_code=None):
#     print('haha')




# -------- Balance Sheets Crawling(재무제표 크롤링)
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) kind로 특정 테이블 지정하는 대신 데이터프레임 리스트 전체 반환
# 3) '~계산에 참여한 계정 펼치기' 제거는 선택사항으로 둠

def bs_craw(stock_code, clear_name=False):  # ------- 검색과 연동해서 입력 변수 설정
    """
    # kind
        : 0 (연간 포괄손익계산서),  1 (분기별 포괄손익계산서)
          2 (연간 재무상태표),     3 (분기별 재무상태표)
          4 (연간 현금흐름표),     5 (분기별 현금프름표)
    """

    # ------- 검색과 연동해서 입력되는 변수 따라 gicode(네이버에서 분류하는 기업 코드)로 변환
    gcode = stc_code_to_bs_gicode(stock_code)

    url = f"http://comp.fnguide.com/SVO2/ASP/SVD_Finance.asp?NewMenuID=103&gicode={gcode}"

    table_list = pd.read_html(url, encoding='UTF-8')

    # 항목에서 불필요한 부분 제거('계산에 참여한 계정 펼치기')
    if clear_name == False:
        return table_list

    else:
        new_table_list = []
        for tbl in table_list:
            for i, idx in enumerate(tbl.iloc[:, 0]):
                m = idx.replace('계산에 참여한 계정 펼치기', '')
                tbl.iloc[i, 0] = m
            new_table_list.append(tbl)
        return new_table_list


# ------- 네이버 금융
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) kind로 특정 테이블 지정하는 대신 데이터프레임 리스트 전체 반환
def fn_craw(stock_code):
    """
       # kind
           : 0 (전일&당일 상한가, 하한가, 거래량 등) #TODO 가공 필요
             1 (증권사 별 매도 매수 정보) #TODO 가공 필요(컬럼이름)
             2 (외국인, 기관 거래 정보) #TODO 가공 필요
             3 (기업실적분석(연도별 분기별 주요재무 정보)) #TODO 가공 필요?
             4 (동일업종비교) #TODO 가공 필요?
             5 (시가총액, 주식수, 액면가 정보) #TODO 가공 필요
             6 (외국인 주식 한도, 보유 정보)
             7 (목표주가 정보) #TODO 가공 필요
             8 (PER, PBR 배당수익률 정보) (주가 따라 변동) #TODO 가공 필요
             9 (동일업종 PER, 등락률 정보) #TODO 가공 필요
             10 (호가 10단계)
             11 (인기 검색 종목: 코스피) #TODO 가공 필요
             12 (인기 검색 종목: 코스닥) #TODO 가공 필요
       """

    gcode = str(stock_code)

    url = f"https://finance.naver.com/item/main.naver?code={gcode}"
    table_list = pd.read_html(url, encoding='euc-kr')

    return table_list

#                   ==============
#                      지표 선정
#                   ==============

# 220222 날씨 수정 시작 ---------------------------------------------

# -------- 지표 선정
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) 데이터프레임 하나가 아닌 리스트로 받아오기때문에 kind 제거하고 직접 선택해줌
# 3) sli_df_y, sil_df_q 에서 '-' 가공 시 if 조건에 따라 처리하는 대신 lambda와 re.sub 이용
# 4) dict 대신 array로 반환, 기업 이름(nm도 반환)
def idv_radar_weather_data(stock_code):
    """
    # <지표 설명>
    # 1. 배당 분석                      -> 배당성향(배당 커버리지의 역수.)
    # 2. 유동성 분석(단기채무지급능력)    -> 당좌비율(당좌자산 / 유동부채)
    # 3. 재무건전성 분석(레버리지 비율)   -> 부채비율(총부채 / 자기자본)의 역수
    # 4. 수익성분석                      -> 매출수익성(당기순이익/매출액))
    # 5. 성장성분석                      -> 순이익성장률
    """

    gcode = stock_code
    nm = stc_code_to_nm(stock_code)

    sil_df = fn_craw(gcode)[3]  # 3: 기업실적정보 재무제표 (220220 수정)
    foreign_ms = fn_craw(gcode)[2].loc[1, '외국인']  # 2 : 외국인, 기관 거래 정보
    giguan_ms = fn_craw(gcode)[2].loc[1, '기관']  # 2 : 외국인, 기관 거래 정보

    if (sil_df.iloc[0:8, 3].isna().sum()) > 0:  # 표 안 가르고 계산하는 건 신규 상장 기업은 정보가 아예 없기 때문
        pass
    elif (sil_df.iloc[0:8, 9].isna().sum()) > 0:  # 표 안 가르고 계산하는 건 신규 상장 기업은 정보가 아예 없기 때문
        pass


    else:
        # 0. 재무정보는 최신 분기 실공시 기준
        # 0. 단, 배당은 1년에 한 번 이루어지기 때문에 최신 년도 공시 기준임
        sil_df_y = sil_df['최근 연간 실적'].iloc[:, 2]  # 느리지만 .iloc으로 하는 이유는 공시 날짜가 다른 기업이 있기 때문
        sil_df_q = sil_df['최근 분기 실적'].iloc[:, 4]

        sil_df_y = sil_df_y.fillna(0)
        sil_df_q = sil_df_q.fillna(0)

        if sil_df_y.dtype == 'O':
            sil_df_y = sil_df_y.apply(lambda x: re.sub('^-$', '0', '{}'.format(x)))
            sil_df_y = sil_df_y.astype('float')

        if sil_df_q.dtype == 'O':
            sil_df_q = sil_df_q.apply(lambda x: re.sub('^-$', '0', '{}'.format(x)))
            sil_df_q = sil_df_q.astype('float')

        # 1. 배당성향(bd_tend)
        bd_tend = sil_df_y[15]  # 실제 배당 성향

        # 2. 유동성 분석 - 당좌비율(당좌자산/유동부채)
        #                       당좌자산 = (유동자산 - 재고자산)
        dj_rate = sil_df_q[7]  # 당좌비율

        # 3. 재무건전성 분석 - 부채비율(총부채/자기자본)의 역수
        bch_rate = sil_df_q[6] / 100  # 부채비율
        bch_rate = round((1 / bch_rate) * 100, 2)

        # 4. 수익성 분석 - 매출수익성(당기순이익/매출액) # TODO 매출액 0인 애들은?

        dg_bene = sil_df_q[2]
        mch = sil_df_q[0]

        suyk = round((dg_bene / mch) * 100, 2)

        # 5. 성장성 분석 - 순이익성장률(지속성장 가능률)
        # (1-배당성향)*자기자본순이익률(ROE)
        #    유보율

        roe = sil_df_y[5] / 100
        ubo = (100 - bd_tend) / 100
        grth = round(roe * ubo * 100, 2)

        data_arr = np.array([bd_tend, dj_rate, bch_rate, suyk, grth])

        # weather part----------------
        # PER?
        weather_per = sil_df_y[10]

        # PBR
        weather_pbr = sil_df_y[12]

        # ROE
        weather_roe = sil_df_y[5]

        # EPS
        weather_eps = sil_df_y[9]

        # BPS
        weather_bps = sil_df_y[11]

        # array
        weather_arr = np.array([weather_per, weather_pbr, weather_roe, weather_eps, weather_bps])

        return data_arr, weather_arr, nm, foreign_ms, giguan_ms

# 수정수정수정

# -------- 관련 기업 지표 선정(상대적 비율 기준)
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) dict 대신 array로 반환, 기업 이름(nm도 반환)

# 220222 날씨

def relate_radar_weather_data(stock_code):
    label_list = ['배당성향', '유동성', '건전성', '수익성', '성장성']
    arr_list = []

    # 주식 코드,이름으로 변환

    gcode = stock_code

    relate_corp = relate_code_crawl(co=gcode)

    # 다섯 개 회사가 안에 있다
    arr_list = [idv_radar_weather_data(stock_code=stcd) for stcd in relate_corp]

    # arr_list에서 데이터 분리
    radar_list = [x[0] for x in arr_list if x is not None]
    weather_list = [x[1] for x in arr_list if x is not None]
    nm_list = [x[2] for x in arr_list if x is not None]

    # 외인 매수, 기관 매수
    try:
        foreign_ms = arr_list[0][3]
    except TypeError:
        foreign_ms=0.01

    try:
        giguan_ms = arr_list[0][4]
    except TypeError:
        giguan_ms=0.01

    # radar_chart_data
    radar_list = np.array(radar_list)

    radar_list[:, 0] = (radar_list[:, 0] / radar_list[:, 0].mean()) * 100
    radar_list[:, 1] = (radar_list[:, 1] / radar_list[:, 1].mean()) * 100
    radar_list[:, 2] = (radar_list[:, 2] / radar_list[:, 2].mean()) * 100
    radar_list[:, 3] = (radar_list[:, 3] / radar_list[:, 3].mean()) * 100
    radar_list[:, 4] = (radar_list[:, 4] / radar_list[:, 4].mean()) * 100

    # radar_chart_dict
    radar_dict_list = []

    for i, nm in enumerate(nm_list):
        dic = {}
        dic[nm] = radar_list[i, :].tolist()
        radar_dict_list.append(dic)

    # weather_chart_data
    weather_list = np.array(weather_list)

    weather_list[:, 0] = (weather_list[:, 0] / weather_list[:, 0].mean())  # 각 기업의 평균 대비 PER
    weather_list[:, 1] = (weather_list[:, 1] / weather_list[:, 1].mean())  # 각 기업의 평균 대비 PBR
    weather_list[:, 2] = (weather_list[:, 2] / weather_list[:, 2].mean())  # 각 기업의 평균 대비 ROE
    weather_list[:, 3] = (weather_list[:, 3] / weather_list[:, 3].mean())  # 각 기업의 평균 대비 EPS
    weather_list[:, 4] = (weather_list[:, 4] / weather_list[:, 4].mean())  # 각 기업의 평균 대비 BPS
    weather_list=np.round(weather_list, 2)

    return label_list, radar_dict_list, weather_list[0], foreign_ms, giguan_ms


# 220222 날씨 수정 끝 ---------------------------------------------

#                   ==============
#                      지표 선정
#                   ==============

# -------- 지표 선정
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) 데이터프레임 하나가 아닌 리스트로 받아오기때문에 kind 제거하고 직접 선택해줌
# 3) sli_df_y, sil_df_q 에서 '-' 가공 시 if 조건에 따라 처리하는 대신 lambda와 re.sub 이용
# 4) dict 대신 array로 반환, 기업 이름(nm도 반환)
def idv_radar_data(stock_code):
    """
    # <지표 설명>
    # 1. 배당 분석                      -> 배당성향(배당 커버리지의 역수.)
    # 2. 유동성 분석(단기채무지급능력)    -> 당좌비율(당좌자산 / 유동부채)
    # 3. 재무건전성 분석(레버리지 비율)   -> 부채비율(총부채 / 자기자본)의 역수
    # 4. 수익성분석                      -> 매출수익성(당기순이익/매출액))
    # 5. 성장성분석                      -> 순이익성장률
    """

    gcode = stock_code
    nm = stc_code_to_nm(stock_code)

    sil_df = fn_craw(gcode)[3]  # 3: 기업실적정보 재무제표 (220220 수정)

    if (sil_df.iloc[0:8, 3].isna().sum()) > 0:  # 표 안 가르고 계산하는 건 신규 상장 기업은 정보가 아예 없기 때문
        pass
    elif (sil_df.iloc[0:8, 9].isna().sum()) > 0:  # 표 안 가르고 계산하는 건 신규 상장 기업은 정보가 아예 없기 때문
        pass


    else:
        # 0. 재무정보는 최신 분기 실공시 기준
        # 0. 단, 배당은 1년에 한 번 이루어지기 때문에 최신 년도 공시 기준임
        sil_df_y = sil_df['최근 연간 실적'].iloc[:, 2]  # 느리지만 .iloc으로 하는 이유는 공시 날짜가 다른 기업이 있기 때문
        sil_df_q = sil_df['최근 분기 실적'].iloc[:, 4]

        sil_df_y = sil_df_y.fillna(0)
        sil_df_q = sil_df_q.fillna(0)

        if sil_df_y.dtype == 'O':
            sil_df_y = sil_df_y.apply(lambda x: re.sub('^-$', '0', '{}'.format(x)))
            sil_df_y = sil_df_y.astype('float')

        if sil_df_q.dtype == 'O':
            sil_df_q = sil_df_q.apply(lambda x: re.sub('^-$', '0', '{}'.format(x)))
            sil_df_q = sil_df_q.astype('float')

        # 1. 배당성향(bd_tend)
        bd_tend = sil_df_y[15]  # 실제 배당 성향

        # 2. 유동성 분석 - 당좌비율(당좌자산/유동부채)
        #                       당좌자산 = (유동자산 - 재고자산)
        dj_rate = sil_df_q[7]  # 당좌비율

        # 3. 재무건전성 분석 - 부채비율(총부채/자기자본)의 역수
        bch_rate = sil_df_q[6] / 100  # 부채비율
        bch_rate = round((1 / bch_rate) * 100, 2)

        # 4. 수익성 분석 - 매출수익성(당기순이익/매출액) # TODO 매출액 0인 애들은?

        dg_bene = sil_df_q[2]
        mch = sil_df_q[0]

        suyk = round((dg_bene / mch) * 100, 2)

        # 5. 성장성 분석 - 순이익성장률(지속성장 가능률)
        # (1-배당성향)*자기자본순이익률(ROE)
        #    유보율

        roe = sil_df_y[5] / 100
        ubo = (100 - bd_tend) / 100
        grth = round(roe * ubo * 100, 2)

        data_arr = np.array([bd_tend, dj_rate, bch_rate, suyk, grth])

        return data_arr, nm


# -------- 관련 기업 지표 선정(상대적 비율 기준)
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) dict 대신 array로 반환, 기업 이름(nm도 반환)
def relate_radar_data(stock_code):
    label_list = ['배당성향', '유동성', '건전성', '수익성', '성장성']
    arr_list = []

    # 주식 코드,이름으로 변환

    gcode = stock_code

    relate_corp = relate_code_crawl(co=gcode)

    arr_list = [idv_radar_data(stock_code=stcd) for stcd in relate_corp]
    nm_list = [x[1] for x in arr_list if x is not None]
    arr_list = [x[0] for x in arr_list if x is not None]

    arr_list = np.array(arr_list)

    arr_list[:, 0] = (arr_list[:, 0] / arr_list[:, 0].mean()) * 100
    arr_list[:, 1] = (arr_list[:, 1] / arr_list[:, 1].mean()) * 100
    arr_list[:, 2] = (arr_list[:, 2] / arr_list[:, 2].mean()) * 100
    arr_list[:, 3] = (arr_list[:, 3] / arr_list[:, 3].mean()) * 100
    arr_list[:, 4] = (arr_list[:, 4] / arr_list[:, 4].mean()) * 100

    dict_list = []

    for i, nm in enumerate(nm_list):
        dic = {}
        dic[nm] = arr_list[i, :].tolist()
        dict_list.append(dic)

    return label_list, dict_list


# -------- 관련 기업 지표 선정(원본)

# def relate_radar_data(yh_code=None, corp_name=None, stock_code=None):
#     label_list=['배당성향', '유동성', '건전성', '수익성', '성장성']
#     dict_list = []
#
#     # 주식 코드로 변환
#     gcode = 0
#     if yh_code != None:
#         gcode = yh_code_to_fn_gicode(yh_code)
#     elif corp_name != None:
#         gcode = nm_to_fn_gicode(corp_name)
#     elif stock_code != None:
#         gcode = stock_code
#
#     relate_corp = relate_code_crawl(co=gcode)
#
#     dict_list = [idv_radar_data(stock_code=stcd) for stcd in relate_corp]
#
#     dict_list = [x for x in dict_list if x is not None]
#
#
#     return label_list, dict_list


#                   ==============
#                       시각화
#                   ==============

# -------- 매출, 당기순이익 추이 그래프
# 220220 수정
# 1) 매개변수 stock_code로 축약
# 2) 크롤링한 데이터는 list로 받아오므로 kind 없애고 직접 인덱스 처리

def mch_dg(stock_code):
    gcode = stock_code
    nm = stc_code_to_nm(stock_code)

    bs_df = bs_craw(stock_code=gcode)[0]
    label_list = bs_df.columns[1:6].tolist()  # 네 분기 + 전년동기
    mch_list = bs_df.loc[0, label_list].tolist()  # 매출액
    dg_list = bs_df.loc[15, label_list].tolist()  # 당기순이익

    return label_list, mch_list, dg_list


def icon_selection(index_array):
    res=[]
    for idx in index_array:
        if 3<idx :
            res.append("RAIN")
        elif ( 1.2<idx and idx<=3 ):
            res.append("CLOUDY")
        elif ( 0.8<idx and idx<=1.2 ):
            res.append("PARTLY_CLOUDY_DAY")
        elif ( 0<idx and idx<=0.8 ):
            res.append("CLEAR_DAY")
        else:
            res.append("SNOW")

    return res

def foreign_giguan(index_array):
    res = []
    for idx in index_array:
        if idx >0:
            res.append("CLEAR_DAY")
        elif idx==0:
            res.append("CLOUDY")
        else:
            res.append("RAIN")

    return res





# ====================================================
#                      데이터
# ====================================================

# -------- 병합 파일 불러오기
com_df=pd.read_csv('com_df.csv',
                   dtype={'stock_code': 'str', '표준코드': 'str', '단축코드': 'str', 'stock_code_ori':'str'},
                   parse_dates=['listed_date', '상장일'])



# -------- 뉴스 크롤링
def news_crawl(gi):


    tot_list = []

    for p in range(1):
        # 뉴스 기사 모인 페이지
        url = 'https://m.stock.naver.com/domestic/stock/' + str(gi) + '/news/title'  # https://m.stock.naver.com/domestic/stock/003550/total
        #F12누르면 나오는 네트워크상에서 찾아온 경로
        #https://m.stock.naver.com/api/news/stock/005930?pageSize=20&page=1&searchMethod=title_entity_id.basic
        url = "https://m.stock.naver.com/api/news/stock/"+str(gi)+"?pageSize=5&searchMethod=title_entity_id.basic&page=1"
        res = requests.get(url)

        news_list = json.loads(res.text)
        #페이지에서 가져온 전체 뉴스기사를 for문으로 분리
        #print(news_list[0])
        for i, news in enumerate(news_list) :
            #신문사 id
            a=news['items'][0]['officeId']
            #기사 id
            b=news['items'][0]['articleId']
            list = []
            list.append(news['items'][0]['officeName']) #신문사
            list.append(news['items'][0]['datetime'][:8]) #날짜
            list.append(news['items'][0]['title'].replace('&quot;','\"')) #제목
            list.append(news['items'][0]['imageOriginLink']) #이미지
            list.append(news['items'][0]['body'].replace('&quot;','\"')) # 기사 내용
            list.append('https://m.stock.naver.com/domestic/stock/005930/news/view/'+str(a)+'/'+str(b)) #기사 url
            tot_list.append(list)

    news_df = pd.DataFrame(data=tot_list, columns=['offname','rdate','title','imgsrc','content','url'])
    news_df['title'] = news_df['title'].str.replace('&amp;', '&')
    news_df['content'] = news_df['content'].str.replace('&amp;', '&')

    #news_df['title'] = [re.sub('[^A-Za-z0-9가-힣]', '' ,s) for s in news_df['title']]


    #news_df.to_csv('css.csv',index=False)
    return news_df

#co-종목코드
def relate_code_crawl(co):
    #연관 종목코드 있는 페이지 불러오기
    url='https://finance.naver.com/item/main.naver?code='+str(co)
    page=pd.read_html(url,encoding='CP949')
    #연관 종목명과 종목코드 뽑아내기(code_list[0]은 '종목명'이어서 제외)
    code_list=page[4].columns.tolist()
    code_list=code_list[1:]
    #종목코드 리스트 반환
    codes=[]
    for word in (code_list):
        codes.append(word[-6:])
    #print(codes)
    return codes


# def before_1w_kospi(date):
#     before1w=date-timedelta(days=7)
#     return fdr.DataReader('KS11',before1w)[['Close']]#, fdr.DataReader('KQ11',before1w)

def invest_opinion(gcode):
    url='https://finance.naver.com/item/coinfo.naver?code='+str(gcode)
    page=pd.read_html(url,encoding='CP949')
    try:
        a,b=page[3][1].tolist()[0][:4].split('.')
        return ((int(a)+int(b)/100)/5)*100 #의견 점수 구한 후 백분율로 다시 변환
    except ValueError:
        return 0.1
#최상현 함수
def crawl_ifrs(gcode):
    url = "http://comp.fnguide.com/SVO2/ASP/SVD_Main.asp?pGB=1&gicode=A"+gcode+"&cID=&MenuYn=Y&ReportGB=&NewMenuID=11&stkGb=701"
    table_list = pd.read_html(url, encoding='UTF-8')

    ifrs = table_list[10]

    ifrs = ifrs.fillna('9999999999')
    for i in range(1, 5):
        if ifrs.iloc[:, i].dtype == 'O':
            ifrs.iloc[:, i] = ifrs.iloc[:, i].apply(lambda x: '9999999999' if type(x) == str else x)
            print(ifrs.iloc[:, i])
            ifrs.iloc[:, i] = ifrs.iloc[:, i].astype('float')
        ifrs.iloc[:, i] = ifrs.iloc[:, i].apply(lambda x: format(float(x), ','))

    ifrs = pd.concat([ifrs.iloc[:, 0], ifrs['Annual']], axis=1)
    ifrs = ifrs.astype(str)

    for i in range(1, 5):
        ifrs.iloc[:12, i] = ifrs.iloc[:12, i].apply(lambda x: x[:-2])
        ifrs.iloc[18:21, i] = ifrs.iloc[18:21, i].apply(lambda x: x[:-2])
        ifrs.iloc[23:24, i] = ifrs.iloc[23:24, i].apply(lambda x: x[:-2])
    ifrs = ifrs.replace(['9,999,999,999', '9,999,999,999.0'], ['-', '-'])

    ifrs.rename(columns={'IFRS(연결)': ''}, inplace=True)
    ifrs = ifrs.to_html(justify="right", index=False, classes="table")
    ifrs = ifrs.replace('border="1"', 'border="0"')
    pd.options.display.float_format = '{:,.0f}'.format
    ifrs = ifrs.replace('<td>', '<td align="right">')
    ifrs = ifrs.replace('<th>', '<th style="text-align: right;">')
    ifrs = ifrs.replace('halign="left"', 'style="text-align: center;"')
    ifrs = ifrs.replace('class ="dataframe table"',
                        'class ="dataframe table" style = "table-layout:fixed;word-break:break-all;"')

    return (ifrs)


def ori_code(yh_code):
    origin_stock=com_df[com_df['yh_code']==yh_code]['stock_code_ori'].values[0]
    return origin_stock



# 아리마 모델
def stock_predict(code,ptype):
    data = stock.get_market_ohlcv_by_date(fromdate="20220101", todate="20220222", ticker=str(code))
    print(data.head())
    data=data[[ptype]]
    y_train=data
    y_test=data
    kpss_diffs = ndiffs(y_train, alpha=0.05, test='kpss', max_d=6)
    adf_diffs = ndiffs(y_train, alpha=0.05, test='adf', max_d=6)
    n_diffs = max(adf_diffs, kpss_diffs)

    print(f"추정된 차수 d = {n_diffs}")
    model=pm.auto_arima(y_train,d=n_diffs,seasonal=False,trace=True)
    model.fit(y_train)
    print(model.summary())
    def forecast_one_step():
        fc, conf_int = model.predict(n_periods=1 # 한 스텝씩!
            , return_conf_int=True)              # 신뢰구간 출력
        return (
            fc.tolist()[0],
            np.asarray(conf_int).tolist()[0]
        )
    forecasts = []
    y_pred = []
    pred_upper = []
    pred_lower = []

    for new_ob in y_test[ptype]:

        fc, conf = forecast_one_step()
        y_pred.append(int(fc))
        pred_upper.append(conf[1])
        pred_lower.append(conf[0])

        ## 모형 업데이트 !!
        model.update(new_ob)
    fc_last = model.predict(n_periods=1 # 한 스텝씩!
            )
    df=pd.DataFrame({"test": y_test[ptype], "pred": y_pred})
    print(df.tail())
    def MAE(y_test, y_pred):
        return np.mean(np.abs((df['test']-df['pred'])/df['test']))*100
    mae=np.round(MAE(y_test, y_pred).astype('float'),4)
    print(f"MAE: {MAE(y_test, y_pred):.3f}")
    price_list=[]
    return int(fc_last),mae





