# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name         :  MySQLConnect
# Description  :  Mysql操作
# Author       :  skymoon9406@gmail.com/fuzheng3@xiaomi.com
# Date         :  2020/05/03
# -------------------------------------------------------------------------------
import pymysql


class MysqlConnect:
    # 正式库
    online = {"host": "", "user": "n",
              "password": "", "port": 3306,
              "db": "", "charset": ""}
    # 数据库关系映射
    db_list = {
        "online": online,
    }

    def __init__(self, db_level):
        """Connection to a MySQL"""
        db_params = self.db_list[db_level]
        try:
            self._conn = pymysql.connect(host=db_params["host"], user=db_params["user"], password=db_params["password"],
                                         charset=db_params["charset"], database=db_params["db"], port=db_params["port"])
            self.__cursor = self._conn.cursor()
        except Exception as err:
            print('mysql连接错误：', err)

    def insert_to_table(self, sql, params):
        """
        :param sql:
        :param params:  元组类型，和该表中的参数一一对应
        :return:
        """
        self.__cursor.execute(sql, params)
        self._conn.commit()

    def insert_to_table_way2(self, sql):
        self.__cursor.execute(sql)
        self._conn.commit()

    def commit_with_sql(self, sql, find_type="all"):
        if find_type == "all":
            self.__cursor.execute(sql)
            result_list = self.__cursor.fetchall()
            return result_list
        elif find_type == "single":
            self.__cursor.execute(sql)
            result = self.__cursor.fetchone()
            return result

    def close(self):
        self.__cursor.close()
        self._conn.close()
