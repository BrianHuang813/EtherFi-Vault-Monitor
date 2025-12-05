# blockchain/abis.py

# 1. Debt Manager: 用來查資產與負債
DEBT_MANAGER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "user", "type": "address"}],
        "name": "getUserCurrentState",
        "outputs": [
            # Index 0: totalCollaterals (Array) - 我們暫時不需細項
            {"components": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "internalType": "struct IDebtManager.TokenData[]", "name": "totalCollaterals", "type": "tuple[]"},
            
            # Index 1: 總資產價值 (USD) -> 這是分母
            {"internalType": "uint256", "name": "totalCollateralInUsd", "type": "uint256"}, 
            
            # Index 2: borrowings (Array) - 我們暫時不需細項
            {"components": [{"internalType": "address", "name": "token", "type": "address"}, {"internalType": "uint256", "name": "amount", "type": "uint256"}], "internalType": "struct IDebtManager.TokenData[]", "name": "borrowings", "type": "tuple[]"},
            
            # Index 3: 總負債價值 (USD) -> 這是分子
            {"internalType": "uint256", "name": "totalBorrowings", "type": "uint256"}       
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "etherFiDataProvider",
        "outputs": [{"internalType": "contract IEtherFiDataProvider", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# 2. Data Provider: 用來驗證 Safe 地址 (新版)
ETHERFI_DATA_PROVIDER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "isEtherFiSafe",  
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# 3. Multicall3: 批次查詢 (標準合約，沒變)
MULTICALL3_ABI = [
    {
        "inputs": [{"components": [{"internalType": "address", "name": "target", "type": "address"}, {"internalType": "bool", "name": "allowFailure", "type": "bool"}, {"internalType": "bytes", "name": "callData", "type": "bytes"}], "internalType": "struct Multicall3.Call3[]", "name": "calls", "type": "tuple[]"}],
        "name": "aggregate3",
        "outputs": [{"components": [{"internalType": "bool", "name": "success", "type": "bool"}, {"internalType": "bytes", "name": "returnData", "type": "bytes"}], "internalType": "struct Multicall3.Result[]", "name": "returnData", "type": "tuple[]"}],
        "stateMutability": "view",
        "type": "function"
    }
]