
from django.template.response import TemplateResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django import template
from accounts.models import BotSetting

from threading import Thread
from datetime import datetime
import time

from main.ftx.api import FtxClient
from .config import MASTER_API, MASTER_SECRET, SLAVE_API, SLAVE_SECRET

client1 = FtxClient(api_key=MASTER_API, api_secret=MASTER_SECRET)
client2 = FtxClient(api_key=SLAVE_API, api_secret=SLAVE_SECRET, subaccount_name="Trader")


def index(request, template_name="main/index.html"):
    botSettings = BotSetting.objects.all()
    for botSetting in botSettings:
        if botSetting.user == request.user:
            break

    isStarted = 0
    if botSetting.started == "YES":
        isStarted = 1
    else:
        isStarted = 0

    return TemplateResponse(request, template_name, {"isStarted": isStarted})


def check_bot_setting(user):
    botSettings = BotSetting.objects.all()
    for botSetting in botSettings:
        if botSetting.user == user:
            break

    if botSetting.started == "YES":
        return True
    else:
        return False


def place_order(order):
    print(order)
    try:
        market = order["market"]
        price = order["price"]
        side = order["side"]
        size = order["size"]
        _type = order["type"]
    except Exception as e:
        print(e)
        return None

    try:
        res = client2.place_order(market, side, None, size, _type)
    except Exception as e:
        print(e)
        res = {"success":False}

    return res


def run_bot(user):
    loop = check_bot_setting(user)
    try:
        last_orders = client1.get_order_history()
    except Exception as e:
        print(e)
        last_orders = []
    last_orders = [order for order in last_orders if order["avgFillPrice"] or order["status"]!="closed"]
    print(last_orders)

    while loop:
        print(datetime.now(), " ========")
        try:
            new_orders = client1.get_order_history()
        except Exception as e:
            new_orders = []
        new_orders = [order for order in new_orders if order["avgFillPrice"] or order["status"]!="closed"]

        orders = [order for order in new_orders if order not in last_orders]
        last_orders = new_orders
        print(orders)

        for order in orders:
            res = place_order(order)
            print("order success")
            print(res)

        time.sleep(10)
        loop = check_bot_setting(user)


def start_bot(request):
    botSettings = BotSetting.objects.all()
    for botSetting in botSettings:
        if botSetting.user == request.user:
            break

    botSetting.started = "YES"
    botSetting.save()

    thr = Thread(target=run_bot, args=(request.user,))
    thr.start()
    return redirect("/")


def stop_bot(request):
    botSettings = BotSetting.objects.all()
    for botSetting in botSettings:
        if botSetting.user == request.user:
            break

    botSetting.started = "NO"
    botSetting.save()
    return redirect("/")