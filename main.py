from web3 import Web3
from utils.log import setup_logger

def main():
    
    setup_logger("app")
    logger = setup_logger("app")

    provider = Web3.HTTPProvider("https://rpc.scroll.io/")
    web3 = Web3(provider)

    if web3.is_connected():
        logger.info("Successfully connected to Ethereum mainnet.")
    else:
        logger.error("Failed to connect to Ethereum mainnet.", )

    
if __name__ == "__main__":
    main()
