import logging
from web3 import Web3
import config

logger = logging.getLogger("blockchain_client")

class EthereumClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info(f"Connecting to RPC: {config.SCROLL_RPC_URL}...")
            cls._instance = super(EthereumClient, cls).__new__(cls)
            cls._instance.w3 = Web3(Web3.HTTPProvider(config.SCROLL_RPC_URL))
            
            if cls._instance.w3.is_connected():
                logger.info("RPC Connection successful.")
            else:
                logger.critical("Failed to connect to RPC node.")
                raise ConnectionError("Failed to connect to RPC")
        return cls._instance

    def get_w3(self):
        return self.w3

client = EthereumClient()
w3 = client.get_w3()