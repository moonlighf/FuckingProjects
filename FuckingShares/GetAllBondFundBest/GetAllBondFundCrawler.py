# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         GetAllBondFundCrawler
# Description:  抓取东方财富的所有债券型基金
# Author:       skymoon9406@gmail.com
# Date:         2020/5/3
# -------------------------------------------------------------------------------
# --------------------------------设置工作路径------------------------------------#
import os
import sys
abspath = os.path.split(os.path.realpath(__file__))[0]
sys.path.append(abspath)
# --------------------------------导入模块和包------------------------------------#
import re
import json
import time
import random
import requests
import traceback
from retrying import retry
from utils.loggers import Logger
from json.decoder import JSONDecodeError
from utils.MySQLConnect import MysqlConnect


"""
http://fund.eastmoney.com/daogou/#dt0;ftzq;rs;sd;ed;pr;cp;rt;tp;rk;se;nx;scz;stdesc;pi3;pn20;zfdiy;shlist

http://fund.eastmoney.com/data/FundGuideapi.aspx?dt=0&ft=zq&sd=&ed=&sc=z&st=desc&pi=1&pn=20&zf=diy&sh=list

ft：zs-指数 zq-债券 gp-股票 hh-混合
pi：页码
pn：每页基金数
sc：z-近一周 1y-近一月 3y-近三月 1n-近一年
st：排序方式 desc和asc
"""


# noinspection PyBroadException
class SaveDataToMysql:
    def __init__(self):
        self.db_client = MysqlConnect("online")

    def insert_into_db(self, params):
        insert_sql = """
        INSERT INTO fund_profit (fund_name, fund_num, fund_type, new_value, new_value_day, 
        profit_near_week, profit_near_month, profit_near_three_month, profit_near_six_month, profit_near_year, 
        profit_near_two_year, profit_near_three_year, profit_this_year, detail_url, fetch_time) 
        VALUES("%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s") 
        ON DUPLICATE KEY UPDATE new_value="%s", new_value_day="%s", fetch_time="%s"
        """
        fetch_day = time.strftime("%Y-%m-%d", time.localtime())
        sql = insert_sql % (
            params["fund_name"], params["fund_num"], params["fund_type"], params["new_value"], params["new_value_day"],
            params["profit_from_near_week"], params["profit_from_near_month"], params["profit_from_near_3month"],
            params["profit_from_near_6month"], params["profit_from_near_year"],
            params["profit_from_near_2year"], params["profit_from_near_3year"], params["profit_from_this_year"],
            params["detail_url"], fetch_day,

            params["new_value"], params["new_value_day"], fetch_day
        )
        try:
            self.db_client.insert_to_table_way2(sql=sql)
            log.logger.info("Insert In Database Success: "
                            + params["fund_name"] + "--" + str(params["new_value"]) + "--" + params["new_value_day"])
        except Exception:
            log.logger.error("INSERT IN DATABASE ERROR AND ERROR SQL: " + sql
                             + "\n ERROR MESSAGE: " + traceback.format_exc())

    def close(self):
        self.db_client.close()


# noinspection PyBroadException
class GetAllBondFundCrawler:
    def __init__(self):
        # 初始化数据库存储
        self.db_client = SaveDataToMysql()

    @retry(stop_max_attempt_number=3, wait_random_min=3000, wait_random_max=5000)
    def connect_to_url(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/76.0.3809.87 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Host": "fund.eastmoney.com",
            "Referer": "http://fund.eastmoney.com/daogou/"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and len(response.content) > 500:
            return response.text
        else:
            raise ConnectionError

    def parse(self, text):
        try:
            data_json_str = re.search("var rankData =([\\s\\S]*)", text).group(1).strip()
        except AttributeError:
            log.logger.error("PARSE PAGE RE ERROR: " + text + '\nAND ERROR MESSAGE: ' + traceback.format_exc())
            raise AttributeError
        try:
            data_json = json.loads(data_json_str)
        except JSONDecodeError:
            log.logger.error("PARSE PAGE JSON ERROR:" + data_json_str + '\nAND ERROR MESSAGE:' + traceback.format_exc())
            raise JSONDecodeError
        try:
            # 最大页码和基金个数
            max_page = data_json["allPages"]
            current_page = data_json["pageIndex"]
            if int(current_page) <= int(max_page):
                log.logger.info("Start Parse Page %s And Max Page %s" % (str(current_page), str(max_page)))
                page_flag = True
                data = data_json["datas"]
                for bond_info in data:
                    bond_info_list = bond_info.split(",")
                    fund_num = bond_info_list[0]
                    fund_name = bond_info_list[1]
                    fund_type = bond_info_list[3]
                    # 今年来收益率
                    profit_from_this_year = bond_info_list[4]
                    # 近一周收益率
                    profit_from_near_week = bond_info_list[5]
                    # 近一月收益率
                    profit_from_near_month = bond_info_list[6]
                    # 近三月收益率
                    profit_from_near_3month = bond_info_list[7]
                    # 近六月收益率
                    profit_from_near_6month = bond_info_list[8]
                    # 近一年收益率
                    profit_from_near_year = bond_info_list[9]
                    # 近两年收益率
                    profit_from_near_2year = bond_info_list[10]
                    # 近三年收益率
                    profit_from_near_3year = bond_info_list[10]
                    # 最新净值和最新净值时间(2020-04-20)
                    new_value_day = bond_info_list[15]
                    new_value = bond_info_list[16]
                    # 对于没有最新净值的，直接跳过，不入库
                    if new_value_day == "":
                        continue
                    # 基金详情的网页
                    detail_url = "http://fund.eastmoney.com/{}.html".format(str(fund_num))
                    # 基金详情存入数据库
                    params = {
                        "fund_num": str(fund_num),
                        "fund_name": str(fund_name),
                        "fund_type": str(fund_type),
                        "profit_from_this_year": profit_from_this_year,
                        "profit_from_near_week": profit_from_near_week,
                        "profit_from_near_month": profit_from_near_month,
                        "profit_from_near_3month": profit_from_near_3month,
                        "profit_from_near_6month": profit_from_near_6month,
                        "profit_from_near_year": profit_from_near_year,
                        "profit_from_near_2year": profit_from_near_2year,
                        "profit_from_near_3year": profit_from_near_3year,
                        "new_value_day": str(new_value_day),
                        "new_value": str(new_value),
                        "detail_url": detail_url
                    }
                    self.db_client.insert_into_db(params=params)
            else:
                page_flag = False
            return page_flag
        except Exception:
            log.logger.error("PARSE THE PAGE ERROR AND ERROR MESSAGE: " + traceback.format_exc())

    def start(self):
        base_url = 'http://fund.eastmoney.com/data/FundGuideapi.aspx?dt=0&ft={}&sd=&ed=&sc=z&st=desc' \
                   '&pi={}&pn=20&zf=diy&sh=list'
        fund_type_list = ["zq", "zs", "gp", "hh"]
        for fund_type in fund_type_list:
            current_page = 1
            while True:
                try:
                    text = self.connect_to_url(base_url.format(fund_type, current_page))
                except ConnectionError:
                    log.logger.error("CONNECT TO URL ERROR AND URL: " + base_url.format(fund_type, current_page))
                    break
                try:
                    page_flag = self.parse(text)
                    if page_flag is False:
                        break
                    else:
                        current_page += 1
                        time.sleep(random.uniform(4, 6))
                except:
                    break
            time.sleep(random.uniform(5, 8))


if __name__ == '__main__':
    log_day = time.strftime("%Y-%m-%d", time.localtime())
    log = Logger(abspath + '/logs/GetFundInfo_' + log_day + '.log', level='info')
    GetAllBondFundCrawler().start()
