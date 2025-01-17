import io
import logging
import threading
import zipfile
from time import sleep

import pandas as pd
import requests
import yaml
from FLATTRADElog import FlatTradeAuth
from OIutils import get_ce_strike_near_premium, get_pe_strike_near_premium
from flask import Flask, render_template
from flask_socketio import SocketIO

from api_helper import NorenApiPy
from kitebotutils import get_expiry, url_nf

app = Flask(__name__)
socketio = SocketIO(app)
api = NorenApiPy()

# Global variables
globals_data = {
    "ce_strike1": 0, "ce_token1": '', "ce_ts1": '',
    "pe_strike1": 0, "pe_token1": '', "pe_ts1": '',
    "ce_strike2": 0, "ce_token2": '', "ce_ts2": '',
    "pe_strike2": 0, "pe_token2": '', "pe_ts2": '',
    "auto_sell_ce_strike": 0, "auto_sell_ce_token": '', "auto_sell_ce_ts": '',
    "auto_sell_pe_strike": 0, "auto_sell_pe_token": '', "auto_sell_pe_ts": '',
    "auto_hedge_ce_strike": 0, "auto_hedge_ce_token": '', "auto_hedge_ce_ts": '',
    "auto_hedge_pe_strike": 0, "auto_hedge_pe_token": '', "auto_hedge_pe_ts": '',
    "PE_dict_st_ts": dict(), "PE_dict_st_tok": dict(),
    "CE_dict_st_ts": dict(), "CE_dict_st_tok": dict(),
    "ltp_data": dict(), "difference": 0,
    "sell_prem": 0, "hedge_prem": 0, "sell_quant": 0, "hedge_quant": 0, "auto_sell_ltps": dict(),
    "auto_hedge_ltps": dict(), "strategy_running": False,
    "ce_ltps": dict(), "pe_ltps": dict(), 'sell_ce_near_premium': 0, 'sell_pe_near_premium': 0,
    'hedge_ce_near_premium': 0, 'hedge_pe_near_premium': 0
}


@app.route('/')
def hello():
    return render_template("index.html")


def buy(ts, quantity):
    order = api.place_order(buy_or_sell='B', product_type='C',
                            exchange='NFO', tradingsymbol=ts,
                            quantity=quantity, discloseqty=0, price_type='MKT',
                            )
    return order


def sell(ts, quantity):
    order = api.place_order(buy_or_sell='S', product_type='C',
                            exchange='NFO', tradingsymbol=ts,
                            quantity=quantity, discloseqty=0, price_type='MKT',
                            )
    return order


@socketio.on('full_buy_order')
def full_buy(data: dict):
    set1 = data.get('set1')
    set2 = data.get('set2')

    buy_ce_strike = int(set1.get('ce'))
    buy_pe_strike = int(set1.get('pe'))
    buy_ce_qty = int(set2.get('ce_qt'))
    buy_pe_qty = int(set2.get('pe_qt'))
    ce_ts = globals_data['CE_dict_st_ts'].get(buy_ce_strike)
    pe_ts = globals_data['PE_dict_st_ts'].get(buy_pe_strike)
    buy_ce = buy(ce_ts, buy_ce_qty)
    buy_pe = buy(pe_ts, buy_pe_qty)
    if buy_ce['stat'] == 'Ok' and buy_pe['stat'] == 'Ok':
        logging.info(buy_ce, buy_pe, "Full Buy order Successful")
    elif buy_ce['stat'] == 'Ok':
        logging.info(buy_ce, "CE Buy Succesful")
    elif buy_pe['stat'] == 'Ok':
        logging.info(buy_pe, "PE Buy Successful")
    else:
        logging.info(buy_ce, buy_pe)


@socketio.on('partial_buy_order')
def partial_buy(data: dict):
    strike = int(data.get('value'))
    quantity = int(data.get('Quantity'))
    Type = data.get('Type')

    trading_symbol = ''
    if Type == 'ce':
        trading_symbol = globals_data['CE_dict_st_ts'].get(strike)
    elif Type == 'pe':
        trading_symbol = globals_data['PE_dict_st_ts'].get(strike)

    Buy = buy(trading_symbol, quantity)

    if Buy['stat'] == 'Ok':
        logging.info(Buy, "Buy order Successful")
    else:
        logging.info(Buy)


@socketio.on('full_sell_order')
def full_sell(data: dict):
    set1 = data.get('set1')
    set2 = data.get('set2')

    sell_ce_strike = int(set1.get('ce'))
    sell_pe_strike = int(set1.get('pe'))
    sell_ce_qty = int(set2.get('ce_qt'))
    sell_pe_qty = int(set2.get('pe_qt'))
    ce_ts = globals_data['CE_dict_st_ts'].get(sell_ce_strike)
    pe_ts = globals_data['PE_dict_st_ts'].get(sell_pe_strike)
    sell_ce = sell(ce_ts, sell_ce_qty)
    sell_pe = sell(pe_ts, sell_pe_qty)
    if sell_ce['stat'] == 'Ok' and sell_pe['stat'] == 'Ok':
        logging.info(sell_ce, sell_pe, "Full sell order Successful")
    elif sell_ce['stat'] == 'Ok':
        logging.info(sell_ce, "CE sell Succesful")
    elif sell_pe['stat'] == 'Ok':
        logging.info(sell_pe, "PE sell Successful")
    else:
        logging.info(sell_ce, sell_pe)


@socketio.on('send_diff')
def handle_diff_input(data: dict):
    globals_data.update({"sell_prem": int(data['set1']['sell_prem'])})
    globals_data.update({"hedge_prem": int(data['set1']['hedge_prem'])})
    globals_data.update({"sell_quant": int(data['set2']['sell_quant'])})
    globals_data.update({"hedge_quant": int(data['set2']['hedge_quant'])})
    globals_data.update({"difference": int(data['difference'])})

    # pe_near_premium = get_pe_strike_near_premium(url_nf, globals_data['sell_prem'])


def get_ce_strike_near_prem(prem):
    print(globals_data["ce_ltps"])
    closest_strike = min(globals_data['ce_ltps'], key=lambda strike: abs(globals_data['ce_ltps'][strike] - prem))
    return closest_strike


def get_pe_strike_near_prem(prem):
    print(globals_data["pe_ltps"])
    closest_strike = min(globals_data['pe_ltps'], key=lambda strike: abs(globals_data['pe_ltps'][strike] - prem))
    return closest_strike


def ce_ltp_mapping(tick_data):
    try:
        ce_ltps = {ce_strike: float(tick_data.get('lp'))
                   for ce_strike, ce_token in globals_data["CE_dict_st_tok"].items() if tick_data['tk'] == ce_token}
        globals_data['ce_ltps'].update(ce_ltps)
    except Exception as e:
        return None


def pe_ltp_mapping(tick_data):
    try:
        pe_ltps = {pe_strike: float(tick_data.get('lp'))
                   for pe_strike, pe_token in globals_data["PE_dict_st_tok"].items() if tick_data['tk'] == pe_token}
        globals_data['pe_ltps'].update(pe_ltps)
    except Exception as e:
        return None


def Premium_diff_strategy():
    globals_data['strategy_running'] = True

    globals_data['sell_ce_near_premium'] = get_ce_strike_near_prem(globals_data['sell_prem'])
    globals_data['sell_pe_near_premium'] = get_pe_strike_near_prem(globals_data['sell_prem'])

    globals_data['hedge_ce_near_premium'] = get_ce_strike_near_prem(globals_data['hedge_prem'])
    globals_data['hedge_pe_near_premium'] = get_pe_strike_near_prem(globals_data['hedge_prem'])
    # print(sell_pe_near_premium)
    # print(sell_pe_near_premium)
    globals_data.update({"auto_sell_ce_strike": globals_data['sell_ce_near_premium']})
    globals_data.update({"auto_sell_pe_strike": globals_data['sell_pe_near_premium']})
    globals_data.update({"auto_hedge_ce_strike": globals_data['hedge_ce_near_premium']})
    globals_data.update({"auto_hedge_pe_strike": globals_data['hedge_pe_near_premium']})
    full_buy({
        "set1": {'ce': globals_data['hedge_ce_near_premium'], 'pe': globals_data['hedge_pe_near_premium']},
        "set2": {'ce_qt': globals_data['hedge_quant'], 'pe_qt': globals_data['hedge_quant']}
    })
    full_sell({
        "set1": {'ce': globals_data['sell_ce_near_premium'], 'pe': globals_data['auto_sell_pe_strike']},
        "set2": {'ce_qt': globals_data['sell_quant'], 'pe_qt': globals_data['sell_quant']}
    })

    globals_data.update({
        "auto_sell_ce_ts": globals_data["CE_dict_st_ts"].get(globals_data["auto_sell_ce_strike"]),
        "auto_sell_ce_token": globals_data["CE_dict_st_tok"].get(globals_data["auto_sell_ce_strike"]),
        "auto_sell_pe_ts": globals_data["PE_dict_st_ts"].get(globals_data["auto_sell_pe_strike"]),
        "auto_sell_pe_token": globals_data["PE_dict_st_tok"].get(globals_data["auto_sell_pe_strike"]),

        "auto_hedge_ce_ts": globals_data["CE_dict_st_ts"].get(globals_data["auto_hedge_ce_strike"]),
        "auto_hedge_ce_token": globals_data["CE_dict_st_tok"].get(globals_data["auto_hedge_ce_strike"]),
        "auto_hedge_pe_ts": globals_data["PE_dict_st_ts"].get(globals_data["auto_hedge_pe_strike"]),
        "auto_hedge_pe_token": globals_data["PE_dict_st_tok"].get(globals_data["auto_hedge_pe_strike"])
    })
    # instruments = [
    #     f"NFO|{globals_data['auto_sell_ce_token']}",
    #     f"NFO|{globals_data['auto_sell_pe_token']}",
    #     f"NFO|{globals_data['auto_hedge_ce_token']}",
    #     f"NFO|{globals_data['auto_hedge_pe_token']}"
    # ]
    # api.subscribe(instruments)
    # logging.info("-----------------")
    # logging.info(globals_data['strategy_running'])
    # logging.info(globals_data['auto_sell_ce_token'])
    # logging.info(globals_data['auto_sell_pe_token'])
    # logging.info(globals_data['auto_sell_ce_strike'])
    # logging.info(globals_data['auto_sell_pe_strike'])
    # logging.info("-----------------")


strategy_thread: threading.Thread = None


@socketio.on('run_premium_diff')
def run_premium_diff():
    global strategy_thread
    if not globals_data["strategy_running"]:
        Premium_diff_strategy()


@socketio.on('stop_premium_diff')
def stop_premium_diff():
    if globals_data["strategy_running"]:
        globals_data["strategy_running"] = False

        globals_data['sell_ce_near_premium'] = 0
        globals_data['sell_pe_near_premium'] = 0

        globals_data['hedge_ce_near_premium'] = 0
        globals_data['hedge_pe_near_premium'] = 0

        globals_data['auto_sell_ce_token'] = ''
        globals_data['auto_sell_pe_token'] = ''

        globals_data['auto_sell_pe_strike'] = 0
        globals_data['auto_sell_ce_strike'] = 0

        globals_data["auto_hedge_ltps"] = dict()
        globals_data["auto_sell_ltps"] = dict()


@socketio.on('partial_sell_order')
def partial_sell(data: dict):
    strike = int(data.get('value'))
    quantity = int(data.get('Quantity'))
    Type = data.get('Type')

    trading_symbol = ''
    if Type == 'ce':
        trading_symbol = globals_data['CE_dict_st_ts'].get(strike)
    elif Type == 'pe':
        trading_symbol = globals_data['PE_dict_st_ts'].get(strike)

    Sell = sell(trading_symbol, quantity)

    if Sell['stat'] == 'Ok':
        logging.info(sell, "Buy order Successful")
    else:
        logging.info(Sell)


# def exit_position(ts, position_details):
#     """
#     Exit an options position based on the current position details
#
#     Parameters:
#     ts (str): Trading symbol of the option
#     position_details (dict): Position details containing quantity and other information
#
#     Returns:
#     dict: Order response from the API
#     """
#     try:
#         quantity = abs(int(position_details.get('netqty', 0)))
#         if quantity == 0:
#             return {'stat': 'Error', 'emsg': 'No position to exit'}
#
#         # If quantity is negative, we have a sell position, so we need to buy to exit
#         # If quantity is positive, we have a buy position, so we need to sell to exit
#         if float(position_details.get('netqty', 0)) < 0:
#             order = buy(ts, quantity)
#         else:
#             order = sell(ts, quantity)
#
#         return order
#     except Exception as e:
#         return {'stat': 'Error', 'emsg': str(e)}
#
#
# def exit_all_positions():
#     """
#     Exit all currently open options positions
#
#     Returns:
#     list: List of order responses for each position exit
#     """
#     try:
#         positions = api.get_positions()
#         if not isinstance(positions, list) or not positions or positions[0].get('stat') != 'Ok':
#             return [{'stat': 'Error', 'emsg': 'Unable to fetch positions'}]
#
#         exit_responses = []
#         for position in positions:
#             # Skip positions with no quantity
#             if float(position.get('netqty', 0)) == 0:
#                 continue
#
#             ts = position.get('tsym')
#             if ts:
#                 response = exit_position(ts, position)
#                 exit_responses.append({
#                     'trading_symbol': ts,
#                     'original_quantity': position.get('netqty'),
#                     'exit_order': response
#                 })
#
#         return exit_responses
#     except Exception as e:
#         return [{'stat': 'Error', 'emsg': str(e)}]
#
#
# # Socket.IO handler for exit requests
# @socketio.on('exit_positions')
# def handle_exit_positions(data):
#     """
#     Handle exit position requests from the frontend
#
#     data can contain:
#     - 'type': 'all' to exit all positions
#     - 'type': 'single' and 'trading_symbol' to exit specific position
#     """
#     try:
#         exit_type = data.get('type', 'all')
#
#         if exit_type == 'all':
#             responses = exit_all_positions()
#             socketio.emit('exit_response', {
#                 'status': 'complete',
#                 'responses': responses
#             })
#         elif exit_type == 'single':
#             ts = data.get('trading_symbol')
#             if not ts:
#                 socketio.emit('exit_response', {
#                     'status': 'error',
#                     'message': 'Trading symbol not provided'
#                 })
#                 return
#
#             positions = api.get_positions()
#             position = next((p for p in positions if p.get('tsym') == ts), None)
#
#             if position:
#                 response = exit_position(ts, position)
#                 socketio.emit('exit_response', {
#                     'status': 'complete',
#                     'responses': [{
#                         'trading_symbol': ts,
#                         'original_quantity': position.get('netqty'),
#                         'exit_order': response
#                     }]
#                 })
#             else:
#                 socketio.emit('exit_response', {
#                     'status': 'error',
#                     'message': f'No position found for {ts}'
#                 })
#     except Exception as e:
#         socketio.emit('exit_response', {
#             'status': 'error',
#             'message': str(e)
#         })

# Handle NIFTY LTP updates


@socketio.on('exit_all')
def exit_all():
    """
    Exit all currently open options positions
    Emits the results through socketio
    """
    try:
        positions = api.get_positions()
        if not isinstance(positions, list) or not positions or positions[0].get('stat') != 'Ok':
            socketio.emit('exit_response', {'status': 'error', 'message': 'Unable to fetch positions'})
            return

        exit_responses = []
        for position in positions:
            # Skip positions with no quantity
            netqty = float(position.get('netqty', 0))
            if netqty == 0:
                continue

            ts = position.get('tsym')
            quantity = abs(int(netqty))

            # If quantity is negative, we have a sell position, so we need to buy to exit
            # If quantity is positive, we have a buy position, so we need to sell to exit
            if netqty < 0:
                response = buy(ts, quantity)
            else:
                response = sell(ts, quantity)

            exit_responses.append({
                'trading_symbol': ts,
                'quantity': netqty,
                'order_response': response
            })
        print("Exit Success", exit_responses)
        # socketio.emit('exit_response', {
        #     'status': 'success',
        #     'responses': exit_responses
        # })

    except Exception as e:
        print("Error in exiting", e)
        # socketio.emit('exit_response', {
        #     'status': 'error',
        #     'message': str(e)
        # })


def handle_nifty_ltp(tick_data):
    try:
        # print(tick_data)
        if tick_data['tk'] == '26000':  # Token for NIFTY
            nifty_ltp = float(tick_data['lp'])
            socketio.emit('update_ltp', {'nifty_ltp': nifty_ltp})
            # logging.info(f"NIFTY LTP emitted: {nifty_ltp}")
    except Exception as e:
        logging.error(f"Error in handling NIFTY LTP: {e}")


# Handle Option LTP updates
def handle_opt_ltps(tick_data):
    try:
        ltp_data = {
            'set1': {},
            'set2': {},
        }
        for set_name in ['set1', 'set2']:
            for opt_type in ['ce', 'pe']:
                token_key = f"{opt_type}_token{set_name[-1]}"
                if globals_data[token_key] == tick_data['tk']:
                    ltp_key = f"{opt_type}_ltp"
                    ltp_data[set_name][ltp_key] = float(tick_data['lp'])
        socketio.emit('update_opt_ltp', ltp_data)
        globals_data.update({"ltp_data": ltp_data})
        # logging.info(f"Option LTPs emitted: {ltp_data}")
    except Exception as e:
        logging.error(f"Error in handling Option LTPs: {e}")


# Main WebSocket event handler
def websocket_event_handler_feed_update(tick_data):
    """
    Handles live feed updates and emits LTPs for NIFTY and selected CE/PE strikes.
    """
    try:
        # Process NIFTY LTP
        handle_nifty_ltp(tick_data)

        # Process Option LTPs
        handle_opt_ltps(tick_data)
        ce_ltp_mapping(tick_data)
        pe_ltp_mapping(tick_data)
        # logging.info(type(tick_data['tk']))
        # logging.info(type(globals_data['auto_sell_ce_token']))
        if tick_data['tk'] == globals_data['auto_sell_ce_token']:  # Token for NIFTY
            globals_data["auto_sell_ltps"]['ce_ltp'] = float(tick_data['lp'])
            # logging.info(globals_data["auto_sell_ltps"]['ce_ltp'])
            # logging.info(type(globals_data["auto_sell_ltps"]['ce_ltp']))
        elif tick_data['tk'] == globals_data['auto_sell_pe_token']:
            globals_data["auto_sell_ltps"]['pe_ltp'] = float(tick_data['lp'])
        elif tick_data['tk'] == globals_data['auto_hedge_ce_token']:
            globals_data["auto_hedge_ltps"]['ce_ltp'] = float(tick_data['lp'])
        elif tick_data['tk'] == globals_data['auto_hedge_pe_token']:
            globals_data["auto_hedge_ltps"]['pe_ltp'] = float(tick_data['lp'])
        if globals_data['strategy_running']:
            try:
                ce_ltp = globals_data["auto_sell_ltps"]['ce_ltp']
                pe_ltp = globals_data["auto_sell_ltps"]['pe_ltp']
                diff = ce_ltp - pe_ltp
                if abs(diff) >= globals_data['difference']:
                    if diff > 0:
                        partial_buy(
                            {"value": globals_data['auto_sell_pe_strike'], "Type": "pe",
                             "Quantity": globals_data['sell_quant']})
                        # logging.info("Partial buy completed")
                        globals_data['auto_sell_pe_strike'] = get_pe_strike_near_prem(ce_ltp)
                        # logging.info(f"pe near premium:{sell_pe_near_premium}")
                        partial_sell(
                            {"value": globals_data['auto_sell_pe_strike'], "Type": "pe",
                             "Quantity": globals_data['sell_quant']})
                        globals_data.update({
                            "auto_sell_pe_strike": globals_data['auto_sell_pe_strike'],
                            "auto_sell_pe_ts": globals_data["PE_dict_st_ts"].get(globals_data['auto_sell_pe_strike']),
                            "auto_sell_pe_token": globals_data["PE_dict_st_tok"].get(
                                globals_data['auto_sell_pe_strike'])
                        })
                    else:
                        partial_buy(
                            {"value": globals_data['sell_ce_near_premium'], "Type": "ce",
                             "Quantity": globals_data['sell_quant']})
                        globals_data['sell_ce_near_premium'] = get_ce_strike_near_prem(pe_ltp)
                        partial_sell(
                            {"value": globals_data['sell_ce_near_premium'], "Type": "ce",
                             "Quantity": globals_data['sell_quant']})
                        globals_data.update({
                            "auto_sell_ce_strike": globals_data['sell_ce_near_premium'],
                            "auto_sell_ce_ts": globals_data["CE_dict_st_ts"].get(globals_data['sell_ce_near_premium']),
                            "auto_sell_ce_token": globals_data["CE_dict_st_tok"].get(
                                globals_data['sell_ce_near_premium'])
                        })
            except Exception as e:
                pass
        socketio.emit('auto_ltps', {
            "auto_sell_ltps": globals_data["auto_sell_ltps"],
            "auto_hedge_ltps": globals_data["auto_hedge_ltps"]
        })

    except Exception as e:
        logging.error(f"Error in WebSocket feed update handler: {e}")


def websocket_open_callback():
    """
    Callback function when the WebSocket connection is established.
    """
    logging.info("WebSocket connection established!")

    # Subscribe to NIFTY token initially
    try:
        instruments = ['NSE|26000']  # NIFTY token
        # print(globals_data["CE_dict_st_tok"].values(), globals_data["PE_dict_st_tok"].values(), sep="Fuck\n")
        tokens: list = list(globals_data["CE_dict_st_tok"].values())
        tokens.extend(globals_data["PE_dict_st_tok"].values())

        ce_insts = [f"NFO|{token}" for token in tokens]
        instruments.extend(ce_insts)
        api.subscribe(instruments)
        logging.info(f"Subscribed to NIFTY: {instruments}")
    except Exception as e:
        logging.error(f"Error during NIFTY subscription: {e}")


@socketio.on('send_data')
def handle_strike_input(data):
    """
    Handles selected strikes and updates global tokens. Subscribes to option tokens.
    """
    globals_data.update({
        "ce_strike1": int(data['set1']['ce']),
        "pe_strike1": int(data['set1']['pe']),
        "ce_strike2": int(data['set2']['ce']),
        "pe_strike2": int(data['set2']['pe']),
    })
    get_token_ts()


    # Subscribe to the selected option tokens
    # try:
    #     instruments = [
    #         f"NFO|{globals_data['ce_token1']}",
    #         f"NFO|{globals_data['pe_token1']}",
    #         f"NFO|{globals_data['ce_token2']}",
    #         f"NFO|{globals_data['pe_token2']}"
    #     ]
    #     # instruments = list(globals_data['PE_dict_st_tok'].values())
    #     # instruments = [f"{inst}" for inst in instruments]
    #     # api.subscribe(instruments)
    #
    #     logging.info(f"Subscribed to option tokens: {instruments}")
    # except Exception as e:
    #     logging.error(f"Error during option token subscription: {e}")


def get_token_ts():
    """
    Updates trading symbols and tokens for selected strikes in globals_data.
    """
    globals_data.update({
        "ce_ts1": globals_data["CE_dict_st_ts"].get(globals_data["ce_strike1"]),
        "ce_token1": globals_data["CE_dict_st_tok"].get(globals_data["ce_strike1"]),
        "pe_ts1": globals_data["PE_dict_st_ts"].get(globals_data["pe_strike1"]),
        "pe_token1": globals_data["PE_dict_st_tok"].get(globals_data["pe_strike1"]),

        "ce_ts2": globals_data["CE_dict_st_ts"].get(globals_data["ce_strike2"]),
        "ce_token2": globals_data["CE_dict_st_tok"].get(globals_data["ce_strike2"]),
        "pe_ts2": globals_data["PE_dict_st_ts"].get(globals_data["pe_strike2"]),
        "pe_token2": globals_data["PE_dict_st_tok"].get(globals_data["pe_strike2"])
    })


def api_login():
    try:
        auth = FlatTradeAuth(config_path='flattradecred.yaml')
        token = auth.fetch_session_token()
        logging.info(f"SESSION_TOKEN :: {token}")

        with open('flattradecred.yaml', 'r') as f:
            data = yaml.safe_load(f)

        ret = api.set_session(userid=data["user"], password=data["pwd"], usertoken=token)
        logging.info(f"API Session Response: {ret}")

        limits = api.get_limits()
        logging.info(f"Account Limits: {limits}")
    except FileNotFoundError:
        logging.error("flattradecred.yaml file not found. Please check the path.")
    except Exception as e:
        logging.error(f"Error during API session setup: {e}")


def load_nfo_symbols():
    """
    Load NFO symbols, filter options data, and subscribe to all option instruments.
    """
    url = "https://api.shoonya.com/NFO_symbols.txt.zip"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                text_file_name = z.namelist()[0]
                with z.open(text_file_name) as file:
                    df = pd.read_csv(file, delimiter=",")
                    df.to_csv("NFOSym.csv", index=False)

                    # Filter for NIFTY options contracts of the current expiry
                    filtered_df = df[(df["Symbol"] == "NIFTY") & (df["Expiry"] == get_expiry(url_nf))]

                    # Create mappings for CE and PE options
                    globals_data["PE_dict_st_ts"] = create_option_mapping(filtered_df, "PE", "TradingSymbol")
                    globals_data["PE_dict_st_tok"] = create_option_mapping(filtered_df, "PE", "Token")
                    globals_data["CE_dict_st_ts"] = create_option_mapping(filtered_df, "CE", "TradingSymbol")
                    globals_data["CE_dict_st_tok"] = create_option_mapping(filtered_df, "CE", "Token")

                    logging.info("NFO symbols loaded successfully.")
        else:
            logging.error(f"Failed to download the ZIP file. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error loading NFO symbols: {e}")


def create_option_mapping(df, option_type, column_name):
    return {int(row["StrikePrice"]): str(row[column_name]) for _, row in df.iterrows() if
            row["OptionType"] == option_type}


def emit_pnl_updates():
    while True:
        try:
            # ret = [{"stat": "Ok", "uid": "POORNA", "actid": "POORNA", "exch": "NSE", "tsym": "ACC-EQ", "prarr": "C",
            #         "pp": "2", "ls": "1", "ti": "5.00", "mult": "1", "prcftr": "1.000000", "daybuyqty": "2",
            #         "daysellqty": "2", "daybuyamt": "2610.00", "daybuyavgprc": "1305.00", "daysellamt": "2610.00",
            #         "daysellavgprc": "1305.00", "cfbuyqty": "0", "cfsellqty": "0", "cfbuyamt": "0.00",
            #         "cfbuyavgprc": "0.00", "cfsellamt": "0.00", "cfsellavgprc": "0.00", "openbuyqty": "0",
            #         "opensellqty": "23", "openbuyamt": "0.00", "openbuyavgprc": "0.00", "opensellamt": "30015.00",
            #         "opensellavgprc": "1305.00", "netqty": "0", "netavgprc": "0.00", "lp": "0.00", "urmtom": "0.00",
            #         "rpnl": "0.00", "cforgavgprc": "0.00"
            #
            #         }
            #        ]
            ret = api.get_positions()
            if isinstance(ret, list) and ret and ret[0].get('stat') == 'Ok':
                total_mtm, total_pnl = 0, 0
                processed_positions = [
                    {
                        "symbol": pos.get('tsym', '-'),
                        "quantity": pos.get('netqty', '-'),
                        "netavg": pos.get('netavgprc', '-'),
                        "price": pos.get('lp', 0.0),
                        "pnl": round(float(pos.get('urmtom', 0)) + float(pos.get('rpnl', 0)), 2),
                    }
                    for pos in ret
                ]
                total_mtm = sum(float(pos['pnl']) for pos in processed_positions)
                total_pnl = total_mtm  # Adjust logic as needed

                # Emit only if there's a significant change

                socketio.emit('pnl_update', {
                    "positions": processed_positions,
                    "total_pnl": round(total_mtm + total_pnl, 2)
                })


            else:
                socketio.emit('pnl_update', {"error": ret[0].get('emsg', 'Unknown error')})

            sleep(0.01)  # Introduce delay
        except Exception as e:
            logging.error(f"Error in emit_pnl_updates: {e}")


if __name__ == '__main__':
    api_login()
    load_nfo_symbols()
    api.start_websocket(
        subscribe_callback=websocket_event_handler_feed_update,
        socket_open_callback=websocket_open_callback
    )
    threading.Thread(target=emit_pnl_updates, daemon=True).start()

    app.run()
