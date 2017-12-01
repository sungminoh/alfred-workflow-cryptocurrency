#-*- coding: utf-8 -*-
import urllib as request
import re
import argparse
from workflow import Workflow
import os
import pickle
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

URL = "https://min-api.cryptocompare.com/data/pricemultifull?fsyms={coins}&tsyms={currencies}"
COINS = ['BTC', 'ETH', 'ETC', 'XRP', 'LTC', 'DASH', 'BCH', 'XMR', 'QTUM', 'ZEC', 'BTG']
CURRENCIES = dict(main='KRW', sub='USD')
WARNING_ICON = './icons/warning.png'
RED_ICON = './icons/red-arrow-up.png'
BLUE_ICON = './icons/blue-arrow-down.png'
COIN_ICON = './icons/coin.png'
CURRENCY_ICON = './icons/flags.png'
ALLOWED = ['reset', 'add', 'set']

class Coin(Workflow):
    COINS_PICKLE = './coins.pkl'
    CURRENCIES_PICKLE = './currencies.pkl'

    def __init__(self, *args):
        super(Coin, self).__init__()
        self.arguments = args
        self.load_coins()
        self.load_currencies()

    def reset_coins(self):
        pickle.dump(COINS, open(self.COINS_PICKLE, 'wb'))

    def load_coins(self):
        if not os.path.exists(self.COINS_PICKLE):
            self.reset_coins()
        self.coins = pickle.load(open(self.COINS_PICKLE, 'rb'))

    def reset_currencies(self):
        pickle.dump(CURRENCIES, open(self.CURRENCIES_PICKLE, 'wb'))

    def load_currencies(self):
        if not os.path.exists(self.CURRENCIES_PICKLE):
            self.reset_currencies()
        self.currencies = pickle.load(open(self.CURRENCIES_PICKLE, 'rb'))

    def fetch(self):
        rq = request.urlopen(URL.format(coins=','.join(self.coins),
                                        currencies=','.join(self.currencies.values())))
        data = json.loads(rq.read())
        return data['DISPLAY']

    def get_price(self, *args):
        if args and args[0] in ALLOWED:
            return self.run(*args)
        data = self.fetch()
        for coin in self.coins:
            info = data.get(coin)
            if not info:
                item = dict(valid=True, arg=coin, icon=WARNING_ICON,
                            title='%s 에 대한 정보가 없습니다.',
                            modifier_subtitles={'alt': 'Remove from the list.'})
            else:
                main = info[self.currencies['main']]
                sub = info[self.currencies['sub']]
                if args:
                    main, sub = sub, main
                main['COIN'] = sub['COIN'] = coin
                item = dict(valid=True, arg=coin,
                            icon=BLUE_ICON if '-' in main['CHANGE24HOUR'] else RED_ICON,
                            title='{COIN:<5}\t{PRICE:<30}\t({CHANGE24HOUR})  {TOTALVOLUME24H}'.format(**main),
                            subtitle='{LASTUPDATE}, H:{HIGH24HOUR}, L:{LOW24HOUR}'.format(**main),
                            modifier_subtitles={
                                'cmd': '{COIN:<5}\t{PRICE:<30}\t({CHANGE24HOUR})  {TOTALVOLUME24H}'.format(**sub),
                                'alt': 'Remove from the list.'
                            })
            self.add_item(**item)
        self.add_item(valid=False, title='Instruction: any letter to switch currency')
        self.add_item(valid=False, title='Instruction: add <COIN> <POSITION(optional)>')
        self.add_item(valid=False, title="Instruction: set <CURRENCY> <'main'(default) or 'sub'>")
        self.add_item(valid=False, title="Instruction: reset <'coin' or 'currency'>")
        return self

    def reset(self, *args):
        if args:
            target = args[0]
            if target.startswith('co'):
                target = 'coin'
                icon = COIN_ICON
            elif target.startswith('cu'):
                target = 'currency'
                icon = CURRENCY_ICON
            self.add_item(valid=True, icon=icon,
                          title='Reset %s' % (target),
                          arg=' '.join(['reset_commit', target]))
        else:
            self.add_item(valid=True,
                          title="Reset <'coin' or 'currency'>")

    def reset_commit(self, *args):
        if not args: return
        if args[0] == 'coin':
            self.reset_coins()
        elif args[0] == 'currency':
            self.reset_currencies()

    def remove(self, *args):
        self.coins.remove(args[0])
        pickle.dump(self.coins, open(self.COINS_PICKLE, 'wb'))
        return self

    def add(self, *args):
        if len(args) >= 2 and args[1].isdigit():
            self.add_item(valid=True, icon=COIN_ICON,
                          title='Add %s to the list at position %s' % (args[0].upper(), args[1]),
                          arg=' '.join(['add_commit'] + args))
        elif args:
            self.add_item(valid=True, icon=COIN_ICON,
                          title='Add %s to the list' % (args[0].upper()),
                          arg=' '.join(['add_commit'] + args))
        else:
            self.add_item(valid=False, icon=COIN_ICON,
                          title='add <COIN> <POSITION(optional)>')
        return self

    def add_commit(self, *args):
        if not args: return
        if len(args) >= 2 and args[1].isdigit():
            self.coins.insert(int(args[1])-1, args[0].upper())
        else:
            self.coins.append(args[0].upper())
        pickle.dump(self.coins, open(self.COINS_PICKLE, 'wb'))
        return self

    def set(self, *args):
        if args:
            if len(args) >= 2 and args[1].lower().startswith('s'):
                set_to = 'sub'
            else:
                set_to = 'main'
            currency = args[0].upper()
            args = [currency, set_to]
            self.add_item(valid=True, icon=CURRENCY_ICON,
                          title='Set %s as a %s currency' % (currency, set_to),
                          arg=' '.join(['set_commit'] + args))
        else:
            self.add_item(valid=False, icon=CURRENCY_ICON,
                          title="set <CURRENCY> <'main'(default) or 'sub'>")
        return self

    def set_commit(self, *args):
        if not args: return
        if len(args) >= 2:
            self.currencies[args[1].lower()] = args[0].upper()
        pickle.dump(self.currencies, open(self.CURRENCIES_PICKLE, 'wb'))
        return self

    def run(self, command, *args):
        getattr(self, command)(*args)
        return self


def main():
    command = sys.argv[1]
    Coin()\
        .run(command, *sys.argv[2:])\
        .send_feedback()


if __name__ == '__main__':
    main()
