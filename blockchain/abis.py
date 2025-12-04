# Debt Manager: 用來查 LTV
DEBT_MANAGER_ABI = [
    {
        "inputs": [{"name": "user", "type": "address"}],
        "name": "debtRatioOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Cash Data Provider: 用來驗證是否為 Safe
CASH_PROVIDER_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "isUserSafe",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Multicall3: 用來批次查詢
MULTICALL3_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bool", "name": "allowFailure", "type": "bool"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"}
                ],
                "internalType": "struct Multicall3.Call3[]",
                "name": "calls",
                "type": "tuple[]"
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"internalType": "bool", "name": "success", "type": "bool"},
                    {"internalType": "bytes", "name": "returnData", "type": "bytes"}
                ],
                "internalType": "struct Multicall3.Result[]",
                "name": "returnData",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]