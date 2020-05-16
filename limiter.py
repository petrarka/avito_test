import ipaddress, time
from flask import Response, request
from functools import wraps
import toml

cfg = toml.load('./app.toml')
MASK =  int(ipaddress.IPv4Address(cfg["ip"]["mask"])) 
GSTORAGE = {} # роут: {подсеть: [разы, время первого обращения за dt]}
GBANNED = {} # словарь забаненых подсетей


def limit(times, sec, bantime):
    def decorator_limit(func):
        @wraps(func)
        def wrapper_limit(*args, **kwargs):
            rule = func.__name__
            storage = GSTORAGE.setdefault(rule, {})
            banned = GBANNED.setdefault(rule, {}) #лучше заменить 
            ip = parse_ip()
            if not ip: 
                return Response('{"err":"header error"}', status=401, mimetype='application/json')
            subnet = ip & MASK 
            if ban_check(subnet, banned): 
                return Response('{"err":"Too many requests"}', status=429, mimetype='application/json')
            if limit_check(times, sec, subnet, bantime, banned, storage):
                value = func(*args, **kwargs) #вызываем хендлер
            else: #возвращаем ответ для фласка, с кодом 429
                value = Response('{"err":"Too many requests"}', status=429, mimetype='application/json')
            return value
        return wrapper_limit
    return decorator_limit


def limit_check(times, sec, subnet, bantime, banned, storage):
    curr_time =  time.time()
    if subnet in storage:
        if curr_time - storage[subnet][1] < sec:
            if storage[subnet][0] < times:
                storage[subnet][0] += 1
                return True #всё ок
            else:
                banned[subnet] = curr_time + bantime
                return False #много запросов, баним
        else:
            storage[subnet][1] = curr_time
            storage[subnet][0] = 1
            return True #dt закончился
    else:
            storage[subnet] = [1, curr_time] #регистрация подсети 
            return True


def ban_check(subnet, banned):
    if subnet in banned:
        if time.time()< banned[subnet]:
            return True
        else:
            banned.pop(subnet)
            return False
    else:
        return False


def limit_reset():
    ip = parse_ip()
    if not ip:
        return False
    subnet = ip & MASK 
    curr_time =  time.time()
    for rule in GSTORAGE:
        storage = GSTORAGE.setdefault(rule, {})
        banned = GBANNED.setdefault(rule, {}) 
        if subnet in banned:
            banned.pop(subnet)
        if subnet in storage:
                storage[subnet][1] = curr_time
                storage[subnet][0] = 0
        else:
            storage[subnet] = [0, curr_time]
        return True

def parse_ip():
    raw_ip = request.headers.get('X-Forwarded-For')
    if not raw_ip: #хедера нет
        return False
    try:
        ip = int(ipaddress.IPv4Address(raw_ip))
    except ipaddress.AddressValueError:
        return False
    return ip
