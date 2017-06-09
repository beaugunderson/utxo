#!/usr/bin/env python3

import sys
import traceback

from collections import defaultdict
from pprint import pprint

from blockchain_parser.blockchain import Blockchain
from blockchain_parser.script import CScriptInvalidError


spent = defaultdict(lambda: defaultdict(dict))
invalid = []
seen_count = 0

blockchain = Blockchain('/Users/beau/Library/Application Support/Bitcoin/blocks/')

year = 0
month = 0

try:
    for block in blockchain.get_unordered_blocks():
        timestamp = block.header.timestamp
        timestamp_format = timestamp.isoformat()

        if timestamp.year > year:
            year = timestamp.year
            month = 0

        if timestamp.year == year and timestamp.month > month:
            month = timestamp.month
            print(timestamp_format)

        for transaction in block.transactions:
            for i, output in enumerate(transaction.outputs):
                if i in spent[transaction.hash]:
                    continue

                spent[transaction.hash][i]['spent'] = False

                if output.script.value == 'INVALID_SCRIPT':
                    invalid.append(f'{transaction.hash},{output.script.hex}')
                    spent[transaction.hash][i]['address'] = 'invalid'
                elif output.addresses:
                    addresses = ','.join(a.address for a in output.addresses)
                    spent[transaction.hash][i]['address'] = f'"{addresses}"'
                else:
                    spent[transaction.hash][i]['address'] = 'unknown'

                spent[transaction.hash][i]['block_timestamp'] = timestamp_format
                spent[transaction.hash][i]['value'] = output.value

            if not transaction.is_coinbase():
                # seen_count += 1

                for input in transaction.inputs:
                    spent[input.transaction_hash][input.transaction_index]['spent'] = True

        # if seen_count > 250:
        #     break
except Exception as e:
    traceback.print_exc(file=sys.stderr)

    from IPython import embed
    embed()
finally:
    print('writing utxo.txt...')

    with open('utxo.txt', 'w') as utxo:
        for txid, outputs in spent.items():
            for sequence, output in outputs.items():
                if output['spent'] == False:
                    timestamp = output.get('block_timestamp', 'unknown')
                    address = output.get('address', 'unknown')
                    value = output.get('value', 'unknown')

                    if timestamp == 'unknown':
                        print(txid)
                        pprint(output)
                        print()
                    else:
                        utxo.write(f'{timestamp},{txid},{sequence},{address},{value}\n')

    print('writing invalid.txt...')

    with open('invalid.txt', 'wb') as invalid_file:
        invalid_file.writelines(invalid)
