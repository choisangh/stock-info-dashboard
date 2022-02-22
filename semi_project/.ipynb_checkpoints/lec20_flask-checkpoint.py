import json
import numpy as np
import pandas as pd
from flask import Flask, make_response, jsonify, request, render_template
from datetime import  datetime, date,timedelta
import requests
import yfinance as yf



app = Flask(__name__, template_folder="production", static_folder="build")

@app.route('/')
def index():

    return render_template("index.html")

#---------------- 업체이름을 타이핑할때마다 실시간 비동기로 업체 명단을 가져와서 리턴 -----------
@app.route('/com_search_ajax', methods=['post'])
def com_search_ajax():

    str = request.form.get('search_input')
    print(str)

    com_df = pd.read_csv("y_finance_stockcode.csv")

    #-----------웹에서 입력한 검색어와 관련된 업체만 가져오기 -----------------
    temp = com_df[(com_df['nm'].str.contains(str))|(com_df['nm'].str.contains(str.upper()))][['cd', 'nm']].head()
    print(temp.values.tolist())
    return json.dumps(  temp.values.tolist()  )




#=============================================== form get
@app.route('/form_submit_get', methods=["post"])
def form_submit_get():

    # input = request.args.get("search_input")  # name="userid"
    # corpname= request.args.get("lec20_flask.py0_name")


    hidden_stock_code = request.form.get("hidden_stock_code")

    my = chart_data(hidden_stock_code)
    print("form_submit_get.....--------------------------------....실행",hidden_stock_code)
    return render_template("res.html", res_obj=my)     #render_template("index.html", MY_MSG="ok")
















# chart_data : KMS 2022.02.16
# 목적
# return val : 원하는 날짜기간의 기업의 종가정보(Close)와 날짜(Date).
# return type: DataFrame(columns = 'Date'타입:Timestamp 형식:yyyy-mm-dd','Close'타입:float)
#
# 변수설명
# ent: yfinance에서 필요한 기업Code
# select_date[list] : yfinance에서 검색시에 필요한 list[0] > start_date / list[1] > end_date
# ent_df : yfinance에서 가져온 기업정보를 담아 놓는 DataFrame
# e_date : 현재날짜
# s_date : 현재날짜 - 7 (일주일전)
#
# 기능설명
# 1. 검색버튼으로 기업명을 검색시 Default Chart Date : 7일
# 2. 사용자 기간 설정시 해당하는 날짜의 주가정보를 가져오는 기능.

# TODO
# 거래량(Volumn)도 같이 보여주는게 의미가 있는지? 질문해보기.
def chart_data(ent, select_date = None):
    if (select_date != None):
        ent_df = yf.download(ent, start=select_date[0], end=select_date[1])

    # 처음 기업명 검색하고 들어온 경우 차트 기간을 얼마나 설정할지? : 일주일 - 상현님
    else:
        e_date = datetime.now()
        s_date = e_date - timedelta(days=30)
        ent_df = yf.download(ent, start=s_date, end=e_date)
    ent_df = ent_df.reset_index()
    ent_df = ent_df.drop(['Open', 'High', 'Low', 'Adj Close', 'Volume'], axis=1)
    ent_df['Date'] = ent_df['Date'].astype('str')
    print(ent_df["Close"].value_counts())
    ent_dict = ent_df.to_dict()
    my = {'ent':ent, 'ent_dict':ent_dict}
    return my


# calendar_ajax_handle : KMS 2022.02.16
# 목적
# 1. index.html에 있는 차트에서 해당 날짜를 선택하였을 경우 값을 받아내기.
# 2. chart_data()로 해당날짜 type casting > [start_date,end_date] 넘겨주는 기능.
#
# 변수설명                           start   :   end
# 1. data : index.html에서 날아오는 mm/dd/yyyy:mm/dd/yyyy를 담아내는 변수.
# 2. splt_data : start:end로 구분되어있는 Data를 ":"로 Split한 정보를 담아내는 변수.
# 3. se_list : mm/dd/yyyy 형태를 yyyy-mm-dd로 변경하여 [start_date,end_date]로 담아놓기위한 변수.
#
# 기능설명
# 1. request값을 받는다
# 2. 해당 데이터를 yfinance에서 요구하는 형태('yyyy-mm-dd')로 변경한다.
# 3. 변경한값을 [start_date/end_date]형식으로 담는다.
# 4. chart_data(종목명, [start_date/end_date]) 전송하여 DataFrame을 받는다.
# 5. 해당 DataFrame을 return한다.
@app.route('/calendar_ajax_handle', methods=["post"])
def calendar_ajax_handle():
    # TODO: 해당 종목데이터도 하나 받아오기.
        # 종목데이터 = request.form.get("종목데이터")
    data = request.form.get("prm")
    ent_name = request.form.get("fuck")
    print(ent_name)
    splt_data = data.split(":")
    se_list = []
    for my_day in splt_data:
        # ymd = my_day.split("/")
        # se_list.append(ymd[2]+'-'+ymd[0]+'-'+ymd[1])

        se_list.append(str(datetime.strptime(my_day, "%m/%d/%Y").date()))

    print(f'0 번째 : {se_list[0]}')
    print(f'1 번째 : {se_list[1]}')
    my = chart_data(ent_name, se_list)
    # test_res = pd.DataFrame([['2021-01-03',1400.0],
    #             ['2021-01-04',2000.0],
    #             ['2021-01-05',900.0]], columns=['Date','Close'])
    # test_res = test_res.to_dict()
    # print(test_res)

    return my

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8088)