# Copyright (c) 2024 Carbonyl LLC & Carbonyl R&D
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import base64
import hmac
import json
import time

import requests


def initLoginParams(useServerTime: bool, apiKey, passphrase, secretKey):
    timestamp = getLocalTime()
    if useServerTime:
        timestamp = getServerTime()
    message = str(timestamp) + 'GET' + '/users/self/verify'
    mac = hmac.new(bytes(secretKey, encoding='utf8'), bytes(message, encoding='utf-8'), digestmod='sha256')
    d = mac.digest()
    sign = base64.b64encode(d)
    arg = {"apiKey": apiKey, "passphrase": passphrase, "timestamp": timestamp, "sign": sign.decode("utf-8")}
    payload = {"op": "login", "args": [arg]}
    return json.dumps(payload)


def isNotBlankStr(param: str) -> bool:
    return param is not None and isinstance(param, str) and (~param.isspace())


def getParamKey(arg: dict) -> str:
    s = ""
    for k in arg:
        if k == 'channel':
            continue
        s = s + "@" + arg.get(k)
    return s


def initSubscribeSet(arg: dict) -> set:
    paramsSet = set()
    if arg is None:
        return paramsSet
    elif isinstance(arg, dict):
        paramsSet.add(getParamKey(arg))
        return paramsSet
    else:
        raise ValueError("arg must dict")


def checkSocketParams(args: list, channelArgs, channelParamMap):
    for arg in args:
        channel = arg['channel'].strip()
        if ~isNotBlankStr(channel):
            raise ValueError("channel must not none")
        argSet = channelParamMap.get(channel, set())
        argKey = getParamKey(arg)
        if argKey in argSet:
            continue
        else:
            validParams = initSubscribeSet(arg)
        if len(validParams) < 1:
            continue
        p = {}
        for k in arg:
            p[k.strip()] = arg.get(k).strip()
        channelParamMap[channel] = channelParamMap.get(channel, set()) | validParams
        if channel not in channelArgs:
            channelArgs[channel] = []
        channelArgs[channel].append(p)


def getServerTime():
    url = "https://www.okx.com/api/v5/public/time"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['data'][0]['ts']
    else:
        return ""


def getLocalTime():
    return int(time.time())
