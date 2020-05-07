# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name         :  FreeIPProxiesPool
# Description  :  每日获取免费代理IP网上前几页的代理IP并更新到Mysql中
# Author       :  skymoon9406@gmail.com<
# Date         :  2020/5/7
# -------------------------------------------------------------------------------
# --------------------------------设置工作路径------------------------------------#
import sys
import os
abspath = os.path.split(os.path.realpath(__file__))[0]
father_path = os.path.dirname(abspath)
sys.path.append(abspath)
sys.path.append(father_path)
# --------------------------------导入模块和包------------------------------------#
import time
import random
import requests
import telnetlib
import traceback
from retrying import retry
from utils.loggers import Logger
from lxml import etree
from utils.MySQLConnect import MysqlConnect


# noinspection PyBroadException
class SaveDataToMysql:
    def __init__(self):
        self.db_client = MysqlConnect("online")

    def insert_into_db(self, params):
        insert_sql = """
        INSERT INTO ip_proxies (ip_address, port, http_type, speed_connect, time_connect, fetch_time) 
        VALUES ("%s", "%s", "%s", "%s", "%s", "%s") ON DUPLICATE KEY UPDATE 
        speed_connect="%s", time_connect="%s", fetch_time="%s"
        """
        fetch_day = time.strftime("%Y-%m-%d", time.localtime())
        sql = insert_sql % (
            params["ip_address"], params["ip_port"], params["http_type"], params["speed_content"],
            params["time_connect"], fetch_day,

            params["speed_content"], params["time_connect"], fetch_day
        )
        try:
            self.db_client.insert_to_table_way2(sql=sql)
            log.logger.info("Insert into success " + params["ip_address"] + ":" + params["ip_port"])
        except Exception:
            log.logger.error("INSERT IN DATABASE ERROR AND ERROR SQL: " + sql
                             + "\n ERROR MESSAGE: " + traceback.format_exc())

    def select_ip(self):
        select_sql = """
        select ip_address, port, http_type from ip_proxies
        """
        results = self.db_client.commit_with_sql(sql=select_sql)
        return results

    def delete_ip(self, ip_address, port):
        delete_sql = """
        delete from ip_address where ip_address="%s" and port="%s" 
        """
        sql = delete_sql % (ip_address, port)
        self.db_client.insert_to_table_way2(sql=sql)

    def close(self):
        self.db_client.close()


# noinspection PyBroadException
class GetIPProxies:
    def __init__(self):
        # 初始化数据库存储
        self.db_client = SaveDataToMysql()
        pass

    @staticmethod
    def test_ip_useful(ip_address, ip_port):
        try:
            telnetlib.Telnet(str(ip_address), port=str(ip_port), timeout=5)
            return True
        except Exception:
            return False

    @retry(stop_max_attempt_number=3, wait_random_min=3000, wait_random_max=5000)
    def connect_to_url(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/76.0.3809.87 Safari/537.36",
            "Accept-Encoding": "gzip, deflate",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200 and len(response.content) > 500:
            return response.text
        else:
            raise ConnectionError

    def parse_xc(self, text):
        # 这里的解析很简单，直接找到table中的tr标签下的内容
        doc = etree.HTML(text)
        data = doc.xpath('//table[@id="ip_list"]/tr')
        # 第一个是表头,直接从第二个后面的开始
        for item in data[1:]:
            try:
                tds = item.xpath('td')
                # 地址
                ip_address = tds[1].text
                # 端口
                ip_port = tds[2].text
                # 类型,http还是https
                http_type = tds[5].text
                # 速度和耗时
                speed_content = str(tds[6].xpath('div/@title')[0]).replace("秒", "")
                time_connect = str(tds[7].xpath('div/@title')[0]).replace("秒", "")

                # 检测该代理ip是否有用
                ip_status = self.test_ip_useful(ip_address, ip_port)
                if ip_status is True:
                    # 存入数据库
                    params = {
                        "ip_address": str(ip_address),
                        "ip_port": str(ip_port),
                        "http_type": str(http_type),
                        "speed_content": speed_content,
                        "time_connect": time_connect
                    }
                    self.db_client.insert_into_db(params=params)

            except IndexError:
                log.logger.error("Parse xici Error and Error text: \n " + text
                                 + "\nError Message: " + traceback.format_exc())

    def parse_kd(self, text):
        doc = etree.HTML(text)
        data = doc.xpath("//table/tbody/tr")
        for item in data:
            try:
                tds = item.xpath('td')
                # 地址
                ip_address = tds[0].text
                # 端口
                ip_port = tds[1].text
                # 类型,http还是https
                http_type = tds[3].text
                time_connect = tds[5].text.replace("秒", "")

                # 检测该代理ip是否有用
                ip_status = self.test_ip_useful(ip_address, ip_port)
                if ip_status is True:
                    # 存入数据库
                    params = {
                        "ip_address": str(ip_address),
                        "ip_port": str(ip_port),
                        "http_type": str(http_type),
                        "speed_content": time_connect,
                        "time_connect": time_connect
                    }
                    self.db_client.insert_into_db(params=params)

            except IndexError:
                log.logger.error("Parse xici Error and Error text: \n " + text
                                 + "\nError Message: " + traceback.format_exc())

    def start(self):
        base_url_map = {
            "xici": "http://www.xicidaili.com/nn/",
            "kuaidaili": "https://www.kuaidaili.com/free/inha/"
        }
        for name, base_url in base_url_map.items():
            # 只获取两个网页的前五页的ip，一般就是近几天的IP
            for current_page in range(1, 6):
                url = base_url + str(current_page)
                log.logger.info("Start with " + name + " And Url is " + url)
                try:
                    text = self.connect_to_url(url)
                except ConnectionError:
                    log.logger.error("Connect to url Error: " + url)
                    continue
                if name == "xici":
                    self.parse_xc(text)
                else:
                    self.parse_kd(text)
                time.sleep(random.uniform(3, 4))

        self.db_client.close()

    def delete_error_ip(self):
        """每天首先删除库中没用的ip地址"""
        select_result = self.db_client.select_ip()
        num_count, all_count = 0, 0
        for temp in select_result:
            all_count += 1
            ip_status = self.test_ip_useful(temp[0], temp[1])
            if ip_status is False:
                self.db_client.delete_ip(temp[0], temp[1])
                num_count += 1
        log.logger.info("Delete Form table Success nums: " + str(num_count) + " And All IP nums: " + str(all_count))


if __name__ == '__main__':
    log_day = time.strftime("%Y-%m-%d", time.localtime())
    log = Logger(abspath + '/logs/GetIPProxies' + log_day + '.log', level='info')
    # 先删除库中没用的IP地址
    GetIPProxies().delete_error_ip()
    # 再往库中增加有用的IP地址
    GetIPProxies().start()
