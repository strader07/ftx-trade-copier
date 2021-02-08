
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

main_client = FtxClient(api_key=MASTER_API, api_secret=MASTER_SECRET, subaccount_name=MASTER_SUBACC_NAME)
sub_clients = []
for i in range(NUM_SLAVES):
    client = FtxClient(api_key=SLAVE_APIS[i], api_secret=SLAVE_SECRETS[i], subaccount_name=SLAVE_NAMES[i])
    sub_clients.append(client)
sub_clients = [sub_clients[3]]

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


def check_bot_setting():
    botSettings = BotSetting.objects.all()
    botSetting = botSettings[0]

    if botSetting.started == "YES":
        return True
    else:
        return False


def place_order(order, mBalance, mLeverage):
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
    for client, i in zip(sub_clients, range(len(sub_clients))):
        acc_info = client.get_account_info()
        sBalance = acc_info["freeCollateral"]
        sLeverage = SLAVE_LEVERAGES[i]
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


def run_bot():
    try:
        last_orders = main_client.get_order_history()
    except Exception as e:
        print(e)
        last_orders = []
    last_orders = [order for order in last_orders if order["avgFillPrice"] or order["status"]!="closed"]
    print(len(last_orders))

    main_accinfo = main_client.get_account_info()
    mBalance = main_accinfo["freeCollateral"]
    mLeverage = MASTER_LEVERAGE

    while True:
        loop = check_bot_setting()
        if not loop:
            print(datetime.now(), " ========")
            print("Bot status: ", loop)
            try:
                last_orders = main_client.get_order_history()
            except Exception as e:
                print(e)
                last_orders = []
            last_orders = [order for order in last_orders if order["avgFillPrice"] or order["status"]!="closed"]
            print(len(last_orders))

            main_accinfo = main_client.get_account_info()
            mBalance = main_accinfo["freeCollateral"]
            mLeverage = MASTER_LEVERAGE
            time.sleep(2)
            continue

        print(datetime.now(), " ========")
        print("Bot status: ", loop)
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
            results = place_order(order, mBalance, mLeverage)
            print("order status!")
            for res, i in zip(results, range(len(results))):
                print(f"{i+1}-th account: \n", res)

        time.sleep(10)
        bal1 = main_client.get_account_info()["freeCollateral"]
        loop = check_bot_setting()


thr = Thread(name="run_bot", target=run_bot)
thr.start()
print("Bot thread started.\n")


def start_bot(request):
    botSettings = BotSetting.objects.all()
    try:
        botSetting = botSettings[0]
    except Exception as e:
        print("Bot setting is not set")
        return redirect("/")

    botSetting.started = "YES"
    botSetting.save()

    return redirect("/")


def stop_bot(request):
    botSettings = BotSetting.objects.all()
    try:
        botSetting = botSettings[0]
    except Exception as e:
        print("Bot setting is not set")
        return redirect("/")

    botSetting.started = "NO"
    botSetting.save()
    return redirect("/")