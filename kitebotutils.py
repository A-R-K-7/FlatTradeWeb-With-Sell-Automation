import requests
import json

from dateutil.relativedelta import relativedelta, TH
from requests import ReadTimeout

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
    sess.get(url_oc, headers=headers, timeout=5)


def get_data(url):
    set_cookie()
    global sess
    response = sess.get(url, headers=headers, timeout=5, cookies=cookies)
    if response.status_code == 401:
        try:
            set_cookie()
            response = sess.get(url_nf, headers=headers, timeout=5, cookies=cookies)
        except ReadTimeout:
            sess = requests.session()

            headers1 = {
                'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, '
                              'like Gecko) Chrome/106.0.0.0 Mobile Safari/537.36 Edg/106.0.1370.34',
                'accept-language': 'en,gu;q=0.9,hi;q=0.8',
                'accept-encoding': 'gzip, deflate, br'}
            response = sess.get(url_nf, headers=headers1, timeout=20)
            cookies1 = response.cookies
            response = sess.get(url_nf, headers=headers1, timeout=20, cookies=cookies1)

    if response.status_code == 200:
        return response.text
    return ""


expirys = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
           "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}
re = {"01": "JAN", "02": "FEB", "03": "MAR", "04": "APR",
      "05": "MAY", "06": "JUN", "07": "JULY", "08": "AUG", "09": "SEP",
      "10": "OCT",
      "11": "NOV", "12": "DEC"}


def get_expiry(url):
    response_text = get_data(url)

    data = json.loads(response_text)
    currExpiryDate = data["records"]["expiryDates"][0]
    day = int(currExpiryDate[:2])
    year = int(currExpiryDate[-4:])

    month = int(expirys.get(currExpiryDate[3:-5].upper()))
    print(month)
    print(year)
    print(day)
    import datetime
    if datetime.date.today() > datetime.date(year=year, month=month, day=day):
        currExpiryDate = data["records"]["expiryDates"][1]

    return currExpiryDate.upper()


def get_current_expiry():
    from datetime import datetime
    todayte = datetime.now()

    t = todayte + relativedelta(weekday=TH(1))
    print(t.day)

    current_expiry = f"{t.day}"

    if len(current_expiry) == 1:
        current_expiry = "0" + current_expiry
    return current_expiry


def get_atm_strike(bnknifty_ltp: float, strike_diff: int = 100) -> int:
    return round(float(bnknifty_ltp) / strike_diff) * strike_diff


if __name__ == "__main__":
    print(get_expiry(url_nf))
