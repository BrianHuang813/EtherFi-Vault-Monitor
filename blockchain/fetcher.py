import logging
from web3 import Web3
from eth_abi import decode
from blockchain.client import w3
from blockchain.abis import DEBT_MANAGER_ABI, ETHERFI_DATA_PROVIDER_ABI, MULTICALL3_ABI
import config 

# 使用標準 Logger
logger = logging.getLogger("blockchain_fetcher")

class DataFetcher:
    def __init__(self):
        self.debt_manager = w3.eth.contract(address=config.DEBT_MANAGER_ADDR, abi=DEBT_MANAGER_ABI)
        self.data_provider = w3.eth.contract(address=config.ETHERFI_DATA_PROVIDER_ADDR , abi=ETHERFI_DATA_PROVIDER_ABI)
        self.multicall = w3.eth.contract(address=config.MULTICALL3_ADDR, abi=MULTICALL3_ABI)

    def is_safe(self, address: str) -> bool:
        """Check if an address is a valid Ether.fi Safe."""
        if not w3.is_address(address):
            return False
       
        checksum_addr = w3.to_checksum_address(address)
        try:
            return self.data_provider.functions.isEtherFiSafe(checksum_addr).call()
        except Exception as e:
            logger.error(f"Error checking safe status for {address}: {e}")
            return False

    def get_ltv(self, address: str) -> float:
        """Fetch the Loan-to-Value (LTV) ratio for a given address."""
        checksum_addr = w3.to_checksum_address(address)
        try:
            # 呼叫 getUserCurrentState (回傳 4 個值)
            data = self.debt_manager.functions.getUserCurrentState(checksum_addr).call()

            # Index 1 是總資產 (USD), Index 3 是總負債 (USD)
            total_collateral = data[1]
            total_debt = data[3]

            if total_collateral == 0:
                return 0.0 # 分母為 0，LTV 就是 0

            # 計算公式：(負債 / 資產) * 100
            # 因為單位都是 USD (例如 1e6 或 1e18)，直接除就可以，單位會消掉
            ltv = (total_debt / total_collateral) * 100

            return round(ltv, 2)
        except Exception as e:
            logger.error(f"LTV Check Error: {e}")
            return 0.0

    def get_ltv_batch(self, addresses: list[str]) -> dict[str, float]:
        """ Batch fetch LTV ratios using Multicall3 for efficiency."""
        if not addresses:
            return {}

        checksum_addrs = [w3.to_checksum_address(addr) for addr in addresses]
        calls = []

        # 1. 準備 Multicall 請求
        for addr in checksum_addrs:
            # 使用 getUserCurrentState 查詢
            call_data = self.debt_manager.encodeABI(fn_name="getUserCurrentState", args=[addr])
            # 構造 Call3 結構: (target, allowFailure, callData)
            calls.append((config.DEBT_MANAGER_ADDR, True, call_data))

        try:
            # 2. 發送單次 RPC 請求
            results = self.multicall.functions.aggregate3(calls).call()
            ltv_map = {}
            
            # 定義解碼格式 (根據 ABI)
            # (token_data[], totalCollateral, token_data[], totalDebt)
            output_type_str = '((address,uint256)[],uint256,(address,uint256)[],uint256)'

            # 3. 解析結果
            for i, (success, return_data) in enumerate(results):
                addr = checksum_addrs[i]
                if success and len(return_data) > 0:
                    try:
                        decoded_data = decode([output_type_str], return_data)[0]
                        total_collateral = decoded_data[1]
                        total_debt = decoded_data[3]
                        
                        if total_collateral == 0:
                            ltv_map[addr] = 0.0
                        else:
                            ltv_map[addr] = round((total_debt / total_collateral) * 100, 2)
                    except Exception as decode_err:
                        logger.error(f"Decode error for {addr}: {decode_err}")
                        ltv_map[addr] = -1.0
                else:
                    ltv_map[addr] = -1.0
            
            return ltv_map

        except Exception as e:
            logger.error(f"Multicall failed: {e}")
            return {}
        
Fetcher = DataFetcher()