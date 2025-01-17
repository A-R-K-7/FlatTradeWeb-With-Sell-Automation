def Premium_diff_strategy():
    globals_data['strategy_running'] = True

    sell_ce_near_premium = get_ce_strike_near_prem(globals_data['sell_prem'])
    sell_pe_near_premium = get_pe_strike_near_prem(globals_data['sell_prem'])

    hedge_ce_near_premium = get_ce_strike_near_prem(globals_data['hedge_prem'])
    hedge_pe_near_premium = get_pe_strike_near_prem(globals_data['hedge_prem'])
    print(sell_pe_near_premium)
    print(sell_pe_near_premium)
    full_buy({
        "set1": {'ce': hedge_ce_near_premium, 'pe': hedge_pe_near_premium},
        "set2": {'ce_qt': globals_data['hedge_quant'], 'pe_qt': globals_data['hedge_quant']}
    })
    full_sell({
        "set1": {'ce': sell_ce_near_premium, 'pe': sell_pe_near_premium},
        "set2": {'ce_qt': globals_data['sell_quant'], 'pe_qt': globals_data['sell_quant']}
    })

    globals_data.update({"auto_sell_ce_strike": sell_ce_near_premium})
    globals_data.update({"auto_sell_pe_strike": sell_pe_near_premium})

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
    logging.info("-----------------")
    logging.info(globals_data['strategy_running'])
    logging.info(globals_data['auto_sell_ce_token'])
    logging.info(globals_data['auto_sell_pe_token'])
    logging.info(globals_data['auto_sell_ce_strike'])
    logging.info(globals_data['auto_sell_pe_strike'])
    logging.info("-----------------")

    while globals_data['strategy_running']:
        try:
            ce_ltp = globals_data["auto_sell_ltps"]['ce_ltp']
            pe_ltp = globals_data["auto_sell_ltps"]['pe_ltp']
            diff = ce_ltp - pe_ltp
            if abs(diff) >= globals_data['difference']:
                if diff > 0:
                    partial_buy({"value": sell_pe_near_premium, "Type": "pe", "Quantity": globals_data['sell_quant']})
                    logging.info("Partial buy completed")
                    sell_pe_near_premium = get_pe_strike_near_prem(ce_ltp)
                    logging.info(f"pe near premium:{sell_pe_near_premium}")
                    partial_sell({"value": sell_pe_near_premium, "Type": "pe", "Quantity": globals_data['sell_quant']})
                    globals_data.update({
                        "auto_sell_pe_strike": sell_pe_near_premium,
                        "auto_sell_pe_ts": globals_data["PE_dict_st_ts"].get(sell_pe_near_premium),
                        "auto_sell_pe_token": globals_data["PE_dict_st_tok"].get(sell_pe_near_premium)
                    })
                else:
                    partial_buy({"value": sell_ce_near_premium, "Type": "ce", "Quantity": globals_data['sell_quant']})
                    sell_ce_near_premium = get_ce_strike_near_prem(pe_ltp)
                    partial_sell({"value": sell_ce_near_premium, "Type": "ce", "Quantity": globals_data['sell_quant']})
                    globals_data.update({
                        "auto_sell_ce_strike": sell_ce_near_premium,
                        "auto_sell_ce_ts": globals_data["CE_dict_st_ts"].get(sell_ce_near_premium),
                        "auto_sell_ce_token": globals_data["CE_dict_st_tok"].get(sell_ce_near_premium)
                    })
        except Exception as e:
            continue


strategy_thread: threading.Thread = None


@socketio.on('run_premium_diff')
def run_premium_diff():
    global strategy_thread
    if not globals_data["strategy_running"]:
        strategy_thread = threading.Thread(target=Premium_diff_strategy, daemon=True)
        strategy_thread.start()


@socketio.on('stop_premium_diff')
def stop_premium_diff():
    if globals_data["strategy_running"]:
        globals_data["strategy_running"] = False
        if strategy_thread and strategy_thread.is_alive():
            strategy_thread.join(timeout=1.0)