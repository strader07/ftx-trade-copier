
from django.template.response import TemplateResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django import template
from accounts.models import BotSetting

from threading import Thread
from datetime import datetime
import time
import os

from main.ftx.api import FtxClient
from .config import *

main_client = FtxClient(api_key=MASTER_API, api_secret=MASTER_SECRET)
sub_clients = []
for i in range(NUM_SLAVES):
    client = FtxClient(api_key=SLAVE_APIS[i], api_secret=SLAVE_SECRETS[i], subaccount_name=SLAVE_NAMES[i])
    sub_clients.append(client)
mLeverage = MASTER_LEVERAGE
sLeverage = SLAVE_LEVERAGE


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


def place_order(order, mBalance):
    print(order)
    try:
        market = order["market"]
        price = order["price"]
        side = order["side"]
        _size = order["size"]
        _type = order["type"]
    except Exception as e:
        print(e)
        return None

    order_results = []
    for client in sub_clients:
        sBalance = client.get_account_info()["freeCollateral"]
        size = round(_size * (sBalance / mBalance) * (sLeverage / mLeverage), 4)
        if size == 0:
            size = _size

        try:
            res = client.place_order(market, side, price, size, _type)
            order_results.append({"success":True, "result": res})
        except Exception as e:
            print(e)
            res = {"success":False, "result": e}
            order_results.append(res)

    return order_results


def run_bot(user):
    loop = check_bot_setting(user)
    try:
        last_orders = main_client.get_order_history()
    except Exception as e:
        print(e)
        last_orders = []
    last_orders = [order for order in last_orders if order["avgFillPrice"] or order["status"]!="closed"]
    print(len(last_orders))

    mBalance = main_client.get_account_info()["freeCollateral"]

    while loop:
        print(datetime.now(), " ========")
        try:
            new_orders = main_client.get_order_history()
        except Exception as e:
            new_orders = []
        new_orders = [order for order in new_orders if order["avgFillPrice"] or order["status"]!="closed"]
        print(len(new_orders))
        orders = [order for order in new_orders if order not in last_orders]
        last_orders = new_orders
        print(orders)

        for order in orders:
            results = place_order(order, mBalance)
            print("order status!")
            for res, i in zip(results, range(len(results))):
                print(f"{i+1}-th account: \n", res)

        time.sleep(10)
        bal1 = main_client.get_account_info()["freeCollateral"]
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