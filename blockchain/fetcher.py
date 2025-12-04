import logging
from web3 import Web3
from eth_abi import decode
from blockchain.client import w3
from blockchain.abis import DEBT_MANAGER_ABI, CASH_PROVIDER_ABI, MULTICALL3_ABI
import config 

# 使用標準 Logger
logger = logging.getLogger("blockchain_fetcher")

class DataFetcher:
    def __init__(self):
        # Initialize contracts
        self.debt_manager = w3.eth.contract(address=config.DEBT_MANAGER_ADDR, abi=DEBT_MANAGER_ABI)
        self.cash_provider = w3.eth.contract(address=config.CASH_DATA_PROVIDER_ADDR, abi=CASH_PROVIDER_ABI)
        self.multicall = w3.eth.contract(address=config.MULTICALL3_ADDR, abi=MULTICALL3_ABI)

    def is_safe(self, address: str) -> bool:
        """Check if an address is a valid Ether.fi Safe."""
        if not w3.is_address(address):
            return False
       
        checksum_addr = w3.to_checksum_address(address)
        try:
            return self.cash_provider.functions.isUserSafe(checksum_addr).call()
        except Exception as e:
            logger.error(f"Error checking safe status for {address}: {e}")
            return False

    def get_ltv_batch(self, addresses: list[str]) -> dict[str, float]:
        """
        Get LTV for multiple addresses using Multicall3.
        """
        if not addresses:
            return {}

        checksum_addrs = [w3.to_checksum_address(addr) for addr in addresses]
        calls = []

        for addr in checksum_addrs:
            call_data = self.debt_manager.encodeABI(fn_name="debtRatioOf", args=[addr])
            calls.append((config.DEBT_MANAGER_ADDR, True, call_data))

        try:
            results = self.multicall.functions.aggregate3(calls).call()
            ltv_map = {}
            
            for i, (success, return_data) in enumerate(results):
                addr = checksum_addrs[i]
                if success and len(return_data) > 0:
                    raw_ratio = decode(['uint256'], return_data)[0]
                    ltv_map[addr] = self._format_ltv(raw_ratio)
                else:
                    ltv_map[addr] = -1.0 # Failed fetch
            
            return ltv_map

        except Exception as e:
            logger.error(f"Multicall failed: {e}")
            return {}

    def _format_ltv(self, raw_value: int) -> float:
        """Convert raw uint256 (WAD) to percentage float."""
        return raw_value / 10**16

Fetcher = DataFetcher()