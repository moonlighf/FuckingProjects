# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         GetConvertibleBondInfo
# Description:  抓取东方财富可转债页面最近申购和上市的可转债，发送到手机
# Author:       skymoon9406@gmail.com
# Date:         2020/4/20
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
import requests
import traceback
from retrying import retry
from datetime import datetime
from utils.loggers import Logger
from json.decoder import JSONDecodeError
from utils.SendEMail import SendEmailByGoogleMail


class GetConvertibleBondInfo:
    def __init__(self):
        pass

    @retry(stop_max_attempt_number=3, wait_random_min=3000, wait_random_max=5000)
    def connect_url(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/76.0.3809.87 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.eastmoney.com",
            "Upgrade-Insecure-Requests": "1"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and len(response.content) > 500:
            return response.text
        else:
            raise ConnectionError

    @staticmethod
    def parse(text):
        try:
            data_json_str = re.search("defjson:([\\s\\S]*)afterdisplay: function \\(_t\\)", text).group(1) \
                .strip().replace("\n", "")
            data_json_str = re.sub("( )+", " ", data_json_str)[:-1]
            data_json_str = data_json_str.replace("pages", "\"pages\"") \
                .replace("data:", "\"data\":").replace("font:", "\"font\":")
        except AttributeError:
            raise AttributeError
        try:
            data_json = json.loads(data_json_str)
        except JSONDecodeError:
            raise JSONDecodeError
        try:
            data = data_json["data"]
            today = time.strftime("%Y-%m-%d", time.localtime())
            applied_bond_map, market_bond_map = {}, {}
            for bond_data in data:
                bond_name = bond_data["SNAME"]
                # 申购时间
                start_time = bond_data["STARTDATE"].replace("T00:00:00", "")
                # 申购时间是今天的可转债进行存储
                if start_time == today:
                    applied_bond_map[bond_name] = start_time
                # 上市时间
                list_time = bond_data["LISTDATE"].replace("T00:00:00", "")
                if list_time == "-":
                    continue
                days = (datetime.strptime(list_time, "%Y-%m-%d") - datetime.strptime(today, "%Y-%m-%d")).days
                # 上市时间是明天的可转债进行存储
                if 0 <= days <= 1:
                    market_bond_map[bond_name] = list_time
            return {
                "applied_bond_map": applied_bond_map,
                "market_bond_map": market_bond_map
            }
        except KeyError:
            raise KeyError

    @staticmethod
    def get_html_content(bond_map):
        """
        构建发送邮件的html
        """
        # 表头
        html_header = """
         <table border="1" width="70%" bgcolor="#e9faff" cellpadding="2">
         <caption><strong>可转债申购表</strong></caption>
         <tr align="center">
             <td><strong>序号</strong></td>
             <td><strong>可转债名称</strong></td>
             <td><strong>申购/上市日期</strong></td>
         </tr>
         """
        if len(bond_map["applied_bond_map"].keys()) != 0:
            html_applied_content,  index = "", 0
            for bond_name in bond_map["applied_bond_map"].keys():
                index += 1
                html_applied_content = html_applied_content + ("""<tr align="center"><td>""" + str(index)
                                                               + "</td><td>" + str(bond_name)
                                                               + "</td><td>"
                                                               + str(bond_map["applied_bond_map"][bond_name])
                                                               + "</td></tr>")
        else:
            html_applied_content = """<tr align="center"><td>99</td><td>今日没有可以申购可转债</td><td>--</td></tr>"""

        if len(bond_map["market_bond_map"].keys()) != 0:
            html_market_content, index = "", 0
            for bond_name in bond_map["market_bond_map"].keys():
                index += 1
                html_market_content = html_market_content + ("""<tr align="center"><td>""" + str(index)
                                                             + "</td><td>" + str(bond_name)
                                                             + "</td><td>" + str(bond_map["market_bond_map"][bond_name])
                                                             + "</td></tr>")
        else:
            html_market_content = """<tr align="center"><td>99</td><td>今日没有等待上市可转债</td><td>--</td></tr>"""

        # 组合成html
        html_content = html_header + html_applied_content + html_market_content
        return html_content

    @staticmethod
    def get_text_content(bond_map):
        if len(bond_map["applied_bond_map"].keys()) != 0:
            applied_content, index = "今日可申购可转债：\n", 0
            for bond_name in bond_map["applied_bond_map"].keys():
                index += 1
                applied_content = applied_content + "  " + (str(index) + '. '
                                                            + str(bond_name) + "    "
                                                            + str(bond_map["applied_bond_map"][bond_name]))
                if index != len(bond_map["applied_bond_map"].keys()):
                    applied_content = applied_content + "\n"
        else:
            applied_content = """  今日没有可以申购可转债"""

        if len(bond_map["market_bond_map"].keys()) != 0:
            market_content, index = "今日可出售可转债：\n", 0
            for bond_name in bond_map["market_bond_map"].keys():
                index += 1
                market_content = market_content + "  " + (str(index) + '. '
                                                          + str(bond_name) + "    "
                                                          + str(bond_map["market_bond_map"][bond_name]))
                if index != len(bond_map["market_bond_map"].keys()):
                    market_content = market_content + "\n"
        else:
            market_content = """  今日没有等待上市可转债"""
        content = applied_content + "\n\n" + market_content
        return content

    def start(self):
        base_url = 'http://data.eastmoney.com/kzz/default.html'
        try:
            text = self.connect_url(base_url)
            try:
                useful_bond_map = self.parse(text)
                content = self.get_text_content(useful_bond_map)
            except KeyError or AttributeError or JSONDecodeError:
                log.logger.error("There is a error:\n" + text
                                 + "\n and Error Message: " + traceback.extract_stack())
                content = "Maybe There Are Some Mistakes Here"
        except ConnectionError:
            content = "Maybe There Are Some Mistakes Here"

        SendEmailByGoogleMail(
            subject="今日可转债申购/上市情况",
            username="skymoon9406@gmail.com",
            password="ycinrjvpjrrpzmcq",
            receivers=['trigger@applet.ifttt.com'],
        ).send_mail(
            way='common',
            content=content,
            files=None
        )


if __name__ == '__main__':
    fetch_day = time.strftime("%Y-%m-%d", time.localtime())
    log = Logger(abspath + '/logs/Monitor' + fetch_day + '.log', level='info')
    requests.packages.urllib3.disable_warnings()
    GetConvertibleBondInfo().start()
