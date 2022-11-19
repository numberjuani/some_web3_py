import asyncio
import json
from web3 import Web3
from websockets import connect
from price_oracle import ABI,ADDRESS
ETH_WS=  'wss://eth-mainnet.g.alchemy.com/v2/mNmqOwPIwA_-dOpWTm2bOJbKQ5xoAWAU'
ETH_HTTP='https://mainnet.infura.io/v3/b03923dc68e54937b578a73a58ce6773'
WBTC=Web3.to_checksum_address('0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599')

def get_contract():
    """
    Gets the contract
    """
    try:
        w3 = Web3(Web3.HTTPProvider(ETH_HTTP))
        cToken_address = Web3.to_checksum_address(ADDRESS)
        ctoken_contract = w3.eth.contract(address=cToken_address, abi=ABI)
        return ctoken_contract  
    except Exception as e:
        print('Error in get_ctoken_contract {e}'.format(e=e))
        return None

async def binance_websocket():
    global eth_price
    global btc_price_okx
    async with connect('wss://stream.binance.com:9443/stream?streams=btcusdt@ticker/ethusdt@ticker') as websocket:
        await websocket.send('{"method": "SUBSCRIBE","params":["btcusdt@ticker","btcusdt@ticker"],"id": 1}')
        async for message in websocket:
            message = json.loads(message)
            try:
                market = message['data']['s']
                match market:
                    case 'ETHUSDT':
                        eth_price = float(message['data']['a'])
                    case 'BTCUSDT':
                        btc_price_okx = float(message['data']['a'])   
                        spread = btc_price_okx - btc_price_aave if btc_price_aave else None
                        if spread:
                            print(f'spread {spread}')
            except:
                pass

async def aave_price():
    global eth_price
    global btc_price_aave
    contract = get_contract()
    async with connect(ETH_WS) as websocket:
        await websocket.send('{"jsonrpc":"2.0","id":1,"method":"eth_subscribe","params":["newHeads"]}')
        async for _ in websocket:
            price_in_eth = (contract.functions.getAssetPrice(WBTC).call())/1e18
            btc_price_aave = price_in_eth * eth_price if eth_price else None

async def both():
    await asyncio.gather(binance_websocket(), aave_price())


global eth_price
global btc_price_okx
global btc_price_aave
btc_price_okx = None
eth_price = None
asyncio.run(both())