# -*- coding: utf-8 -*-#
# -------------------------------------------------------------------------------
# Name:         SendMessage
# Description:  利用twilio模块发送短信
# Author:       skymoon9406@gmail.com
# Date:         2020/4/23
# -------------------------------------------------------------------------------
import time
from twilio.rest import Client


class SendMessage:
    def __init__(self):
        # twilio.com 注册获取的参数
        self.auth_token = ''
        self.account_sid = ''

    def send_message(self, phone_number, message):
        client = Client(self.account_sid, self.auth_token)
        mes = client.messages.create(
            # 填写在active number处获得的号码
            from_='',
            body=message,
            to=phone_number
        )
        print("Send Message Success")


if __name__ == "__main__":
    SendMessage().send_message(
        phone_number="",
        message=""
    )
