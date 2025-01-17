import time

import requests
import json
import math

from requests import ReadTimeout


# Python program to print
# colored text and background


# Method to get nearest strikes
def round_nearest(x, num=50): return int(math.ceil(float(x) / num) * num)


def nearest_strike_bnf(x): return round_nearest(x, 100)


def nearest_strike_nf(x): return round_nearest(x)


# Urls for fetching Data

url_oc = "https://www.nseindia.com/option-chain"
url_bnf = 'https://www.nseindia.com/api/option-chain-indices?symbol=BANKNIFTY'
url_nf = 'https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY'
url_indices = "https://www.nseindia.com/api/allIndices"

# Headers
headers = {
    'authority': 'www.nseindia.com',
    'accept': '*/*',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
    # Requests sorts cookies= alphabetically
    # 'cookie': '_gid=GA1.2.1024607353.1668257424; _ga=GA1.1.120172271.1666283874; nsit=l0wJVYtvci_676GoeFKS5Fs2; AKA_A2=A; ak_bmsc=B3D223420C92CDF691C8760255400E49~000000000000000000000000000000~YAAQBpUvFzp0nTyEAQAAtDn9bhE+VgXIkhvz57nsxPg0JQjzXvnvCphJpB8yV62u7JSuJP+kSbTx1qBOnZhwjD5rdoz2RL++jkTYvG0BTX3gK+sV5JVa70kPHq95mKxsgVklmeBmw+0cpO4xg3U3m7/LEjB4PQ9AS1ItD5aTEbiHAeB+JayoJhmIvlnmkLoFzYCn9aNYu08qr3gGYEHi+GTzJbHXVZkM4WUy1NqXCQYuvqW1PrvvA402P/SuU6o0RGq0B1GMxOyG4V5U9+uYWPY8nEN5NhurgIr2GIU0+6aip3j71xb2PToyKkU/Se87SAZSnv5sxEwymJ47W8XdqHVJ0NVJGhcV3AzEwmGbtjjcxCsPhSPVxunlDXMFRj/vhCxwenTF1khS61/AZYZTnKXdiH330qkEkFY2eHwhVILQW6ygatFBa5NCkVfsU3OImA8scZDJeuZUUmEQQ8c7esM6Zui4Ije0e4wKgWSD5w8is9vcR873WNEy99V2; nseappid=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcGkubnNlIiwiYXVkIjoiYXBpLm5zZSIsImlhdCI6MTY2ODMxMjkzMiwiZXhwIjoxNjY4MzE2NTMyfQ.-mw8gAgEzKMFITLIQQrkpjJM79w6_DephMYtvocOQkE; _ga_PJSKY6CFJH=GS1.1.1668312891.7.1.1668312934.17.0.0; RT="z=1&dm=nseindia.com&si=0066aa64-bd66-422e-81c0-bde052ca4b54&ss=laeuf4te&sl=6&tt=3f0&bcn=%2F%2F684d0d46.akstat.io%2F&ld=ytd"; bm_sv=0F207044829DF7BE4F53099E2E98F7F7~YAAQBpUvFz7EnTyEAQAAyE8zbxEdnUklgrRZZ+7GPwcRYv7DSrZXUC0+1HGOEgM3F/A2h97iqfPO4bha8UY6o7BYQmc7/RY/UPrPOu2fiBCRdjAvSeSl6ze1aIo4sunnXcBRs0PuSXd1pbhqdq3FuN9HJmbivgl6SavKBiheezGt4WzdD1GbbmRM/bdfaLV5Z50bNPkpEU4i9iv/4mZU4ALRvUf0zGlbtiVCbhHoV78YMrx/7W0tO2BS7kUE+PndBLny~1',
    'referer': 'https://www.nseindia.com/option-chain',
    'sec-ch-ua': '"Microsoft Edge";v="108", "Chromium";v="108", "Not=A?Brand";v="24"',
    'sec-ch-ua-mobile': '?1',
    'sec-ch-ua-platform': '"WINDOWS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/107.0.0.0 Mobile Safari/537.36 Edg/107.0.1418.42', }

sess = requests.Session()
cookies = dict()


# Local methods
def set_cookie():
    request = sess.get(url_oc, headers=headers, timeout=5)


def get_ce_strike_near_premium(url, premium):
    response_text = get_data(url)
    data = json.loads(response_text)

    currExpiryDate = data["records"]["expiryDates"][0]

    list_of_ce_premiums = []
    List_of_ce_items = []
    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            try:
                list_of_ce_premiums.append(abs(item["CE"]["lastPrice"] - premium))
            except KeyError:
                list_of_ce_premiums.append(100000)

            List_of_ce_items.append(item["CE"])

            # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"][
            # "openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"][
            # "openInterest"]).rjust(10," ")) + " ]")

    return List_of_ce_items[list_of_ce_premiums.index(min(list_of_ce_premiums))]


def get_pe_strike_near_premium(url, premium):
    response_text = get_data(url)
    data = json.loads(response_text)

    currExpiryDate = data["records"]["expiryDates"][0]

    list_of_pe_premiums = []
    List_of_pe_items = []
    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            try:

                list_of_pe_premiums.append(abs(item["PE"]['lastPrice'] - premium))

            except KeyError:
                list_of_pe_premiums.append(max(list_of_pe_premiums) + 1000000)

            List_of_pe_items.append(item["PE"])

    return List_of_pe_items[list_of_pe_premiums.index(min(list_of_pe_premiums))]

def get_data(url):
    set_cookie()
    global sess
    response = sess.get(url, headers=headers, timeout=5, cookies=cookies)
    if response.status_code == 401:
        try:
            set_cookie()
            response = sess.get(url_nf, headers=headers, timeout=5, cookies=cookies)
        except TimeoutError:
            sess = requests.session()

            headers1 = {
                'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, '
                              'like Gecko) Chrome/106.0.0.0 Mobile Safari/537.36 Edg/106.0.1370.34',
                'accept-language': 'en,gu;q=0.9,hi;q=0.8',
                'accept-encoding': 'gzip, deflate, br'}
            response = sess.get(url_nf, headers=headers1, timeout=5)
            cookies1 = response.cookies
            response = sess.get(url_nf, headers=headers1, timeout=5, cookies=cookies1)

    if response.status_code == 200:
        return response.text
    return ""


# Showing Header in structured format with Last Price and Nearest Strike


# Fetching CE and PE data based on Nearest Expiry Date


def print_oi(url, lot_size):
    response_text = get_data(url)

    data = json.loads(response_text)
    ceinterestarray = []
    peintrestarray = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:

        if item["expiryDate"] == currExpiryDate:
            try:
                ceinterestarray.append(int(item["CE"]["changeinOpenInterest"]))
                peintrestarray.append(int(item["PE"]["changeinOpenInterest"]))
            except KeyError:
                continue

        # print(item)
        # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"]["openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"]["openInterest"]).rjust(10," ")) + " ]")

    return sum(ceinterestarray) * lot_size, sum(peintrestarray) * lot_size


def option_chain(url):
    response_text = get_data(url)

    data = json.loads(response_text)
    list_items = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:

        if item["expiryDate"] == currExpiryDate:
            try:
                list_items.append(item)
            except KeyError:
                continue

        # print(item)
        # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"]["openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"]["openInterest"]).rjust(10," ")) + " ]")

    return list_items


def get_first_last_strike(url):
    try:
        response_text = get_data(url)
    except ReadTimeout:
        time.sleep(1)
        response_text = get_data(url)

    data = json.loads(response_text)

    strikes = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:

        if item["expiryDate"] == currExpiryDate:
            strikes.append(item["strikePrice"])

        # print(item)
        # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"]["openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"]["openInterest"]).rjust(10," ")) + " ]")

    return min(strikes), max(strikes)


def print_ltp(url):
    response_text = get_data(url)
    data = json.loads(response_text)
    currExpiryDate = data["records"]["expiryDates"][0]

    ltpdict = dict()

    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:

            # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"][
            # "openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"][
            # "openInterest"]).rjust(10," ")) + " ]")
            # print(f"{item['PE']['lastPrice']}  {item['PE']['strikePrice']}")
            try:
                ltpdict[f'{item["PE"]["strikePrice"]}PE'] = item['PE']['lastPrice']
            except KeyError:
                ltpdict[f'{item["CE"]["strikePrice"]}CE'] = item['CE']['lastPrice']

    return ltpdict


def print_total_oi(url, lot_size):
    try:
        response_text = get_data(url)
    except ReadTimeout:
        time.sleep(1)
        response_text = get_data(url)
    data = json.loads(response_text)
    ceinterestarray = []
    peintrestarray = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"]["openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"]["openInterest"]).rjust(10," ")) + " ]")
            try:
                ceinterestarray.append(int(item["CE"]["openInterest"]))
                peintrestarray.append(int(item["PE"]["openInterest"]))
            except Exception as e:
                pass

    return sum(ceinterestarray) * lot_size, sum(peintrestarray) * lot_size


def get_oi_chng(url, lot_size, start_strike, end_strike):
    response_text = get_data(url)
    data = json.loads(response_text)
    ceinterestarray = []
    peintrestarray = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            if start_strike <= item["strikePrice"] <= end_strike:
                # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"]["openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"]["openInterest"]).rjust(10," ")) + " ]")
                try:
                    ceinterestarray.append(
                        (int(item["CE"]["changeinOpenInterest"]) * lot_size))
                    peintrestarray.append((int(item["PE"]["changeinOpenInterest"])) * lot_size)
                except Exception as e:
                    pass

    return ceinterestarray, peintrestarray


def get_oi(url, lot_size, start_strike, end_strike):
    response_text = get_data(url)
    data = json.loads(response_text)
    ceinterestarray = []
    peintrestarray = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            if start_strike <= item["strikePrice"] <= end_strike:
                try:
                    ceinterestarray.append(
                        (int(item["CE"]["openInterest"]) * lot_size))
                    peintrestarray.append((int(item["PE"]["openInterest"])) * lot_size)
                except Exception as e:
                    print(e, 269)

    return ceinterestarray, peintrestarray


def get_OI(url, lot_size):
    response_text = get_data(url)
    data = json.loads(response_text)
    ceinterestarray = []
    peintrestarray = []
    currExpiryDate = data["records"]["expiryDates"][0]

    for item in data['records']['data']:
        if item["expiryDate"] == currExpiryDate:
            # print(strCyan(str(item["strikePrice"])) + strGreen(" CE ") + "[ " + strBold(str(item["CE"]["openInterest"]).rjust(10," ")) + " ]" + strRed(" PE ")+"[ " + strBold(str(item["PE"]["openInterest"]).rjust(10," ")) + " ]")
            try:
                ceinterestarray.append(
                    int(item["CE"]["openInterest"]) * lot_size)
                peintrestarray.append((int(item["PE"]["openInterest"])) * lot_size)
            except Exception as e:
                pass

    return ceinterestarray, peintrestarray


# Finding highest Open Interest of People's in CE based on CE data


def oi():
    return print_oi(url_nf, 75)


def total_oi():
    return print_total_oi(url_nf, 50)


def first_last_strike():
    return get_first_last_strike(url_nf)


def bnk_oi():
    Ce_change, Pe_change = print_oi(url_bnf, 25)
    Ce_change = Ce_change
    Pe_change = Pe_change
    return Ce_change, Pe_change


# Finding Highest OI in Call Option In Nifty

# print(print_oi(50, 10, 550,url_DR_Reddy,125))
# nf_highestoi_CE = highest_oi_CE(5, 100, bnf_nearest, url_bnf)

# oi()
# Finding Highest OI in Call Option In Bank Nifty

if __name__ == "__main__":
    ce_strike,pe_strike = get_ce_strike_near_premium(url_nf,200),get_pe_strike_near_premium(url_nf,200)
    print(type(ce_strike['strikePrice']), pe_strike['strikePrice'])
