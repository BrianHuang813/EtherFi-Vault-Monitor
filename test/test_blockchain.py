from blockchain.fetcher import DataFetcher
import time

def main():
    fetcher = DataFetcher()
    
    # 1. 測試單一地址
    # 請填入一個真實的 Safe 地址 (例如從你的 Event Log 抓到的)
    test_safe = "0x7ca0b75e67e33c0014325b739a8d019c4fe445f0" 
    
    print(f"--- Testing Single Check for {test_safe} ---")
    is_safe = fetcher.is_safe(test_safe)
    print(f"Is valid safe? {is_safe}")
    
    ltv = fetcher.get_ltv(test_safe)
    print(f"Current LTV: {ltv}%")

    # 2. 測試批次查詢 (Multicall)
    print("\n--- Testing Batch Check ---")
    # 故意混入一個假地址來測試容錯能力
    batch_list = [
        test_safe,
        "0x000000000000000000000000000000000000dead" 
    ]
    
    start_time = time.time()
    results = fetcher.get_ltv_batch(batch_list)
    end_time = time.time()
    
    print(f"Batch Result (took {end_time - start_time:.4f}s):")
    for addr, val in results.items():
        print(f"{addr}: {val}%")

if __name__ == "__main__":
    main()