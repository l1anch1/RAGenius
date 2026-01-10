#!/usr/bin/env python3
"""
Quick test script to verify backend connection
快速测试后端连接
"""
import requests
import sys

def test_backend(backend_url="http://localhost:8000"):
    """测试后端连接"""
    print("="*60)
    print("🧪 Testing RAGenius Backend Connection")
    print("="*60)
    print()
    
    # 1. 健康检查
    print(f"1️⃣  Testing health endpoint: {backend_url}/api/health")
    try:
        response = requests.get(f"{backend_url}/api/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        print()
        print("💡 Make sure the backend is running:")
        print("   docker compose up -d")
        sys.exit(1)
    
    print()
    
    # 2. 系统信息
    print(f"2️⃣  Testing info endpoint: {backend_url}/api/info")
    try:
        response = requests.get(f"{backend_url}/api/info", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ System info retrieved")
            print(f"   Model: {data.get('model', 'N/A')}")
            print(f"   Embedding: {data.get('embedding_model', 'N/A')}")
            print(f"   Initialized: {data.get('initialized', False)}")
        else:
            print(f"   ⚠️  Info check returned: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Info check failed: {e}")
    
    print()
    
    # 3. 文档列表
    print(f"3️⃣  Testing documents endpoint: {backend_url}/api/documents")
    try:
        response = requests.get(f"{backend_url}/api/documents", timeout=5)
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            print(f"   ✅ Documents retrieved: {len(docs)} files")
            if docs:
                print(f"   📄 Files: {', '.join(docs[:3])}")
                if len(docs) > 3:
                    print(f"         ... and {len(docs) - 3} more")
        else:
            print(f"   ⚠️  Documents check returned: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Documents check failed: {e}")
    
    print()
    
    # 4. 测试查询
    print(f"4️⃣  Testing query endpoint: {backend_url}/api/query")
    try:
        response = requests.post(
            f"{backend_url}/api/query",
            json={"query": "什么是RAG？"},
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                answer = data.get('answer', '')
                sources = data.get('sources', [])
                print("   ✅ Query successful")
                print(f"   Answer length: {len(answer)} chars")
                print(f"   Sources: {len(sources)} documents")
                print(f"   Preview: {answer[:100]}...")
            else:
                print(f"   ⚠️  Query failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"   ❌ Query failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  Query test failed: {e}")
    
    print()
    print("="*60)
    print("✅ Backend connection test complete!")
    print("="*60)
    print()
    print("💡 You can now run the full evaluation:")
    print("   ./evaluation/run_evaluation.sh")
    print()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test RAGenius backend connection')
    parser.add_argument(
        '--backend-url',
        type=str,
        default='http://localhost:8000',
        help='Backend API URL (default: http://localhost:8000)'
    )
    
    args = parser.parse_args()
    test_backend(args.backend_url)



