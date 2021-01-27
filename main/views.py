
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
client2 = FtxClient(api_key=SLAVE_API, api_secret=SLAVE_SECRET)


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


def place_order(position):
    print(position)
    try:
        market = position["future"]
        price = position["entryPrice"]
        side = position["side"]
        size = position["size"]
    except Exception as e:
        print(e)
        return None

    try:
        res = client.place_order(market, side, None, size, "market")
    except Exception as e:
        print(e)
        res = {"success":False}

    return res


def run_bot(user):
    loop = check_bot_setting(user)
    try:
        last_positions = client1.get_account_info()["positions"]
    except Exception as e:
        print(e)
        last_positions = []
    print(last_positions)

    while loop:
        print(datetime.now(), " ========")
        try:
            new_positions = client1.get_account_info()["positions"]
        except Exception as e:
            new_positions = []

        if len(new_positions) > len(last_positions):
            positions = [pos for pos in new_positions if pos not in last_positions]
        else:
            positions = []
        last_positions = new_positions

        for position in positions:
            res = place_order(position)
            if not res["success"]:
                print("order not placed")
            else:
                print("order success, here is the details: ", res["result"])

        time.sleep(10)
        loop = check_bot_setting(user)


def start_bot(request):
    botSettings = BotSetting.objects.all()
    for botSetting in botSettings:
        if botSetting.user == request.user:
            break

    botSetting.started = "YES"
    botSetting.save()

    # start the bot thread
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