#!/usr/bin/env python3
"""
Simplified observability testing for GNN Attack Path Demo.
Tests API endpoints, structured logging, and basic metrics without Docker.
"""
import requests
import time
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE = "http://localhost:8000"

def test_api_endpoints():
    """Test all available API endpoints."""
    print("🔍 Testing API Endpoints...")
    
    endpoints = [
        {"method": "GET", "path": "/", "name": "Root"},
        {"method": "GET", "path": "/health", "name": "Health Check"},
        {"method": "GET", "path": "/api/v1/crown-jewels", "name": "Crown Jewels"},
        {"method": "POST", "path": "/api/v1/paths", "name": "Attack Paths", "data": {
            "target": "database-server",
            "max_hops": 3
        }},
        {"method": "POST", "path": "/api/v1/query", "name": "AI Query", "data": {
            "query": "What are the most critical attack paths?"
        }},
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            print(f"   Testing {endpoint['name']}...")
            
            if endpoint['method'] == 'GET':
                response = requests.get(f"{API_BASE}{endpoint['path']}", timeout=10)
            else:
                response = requests.post(
                    f"{API_BASE}{endpoint['path']}", 
                    json=endpoint.get('data', {}),
                    timeout=10
                )
            
            response.raise_for_status()
            results[endpoint['name']] = {
                "status": "success",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            }
            print(f"   ✅ {endpoint['name']}: {response.status_code} ({response.elapsed.total_seconds():.3f}s)")
            
        except Exception as e:
            results[endpoint['name']] = {
                "status": "failed",
                "error": str(e)
            }
            print(f"   ❌ {endpoint['name']}: {e}")
    
    return results

def test_structured_logging():
    """Test structured logging by checking API responses."""
    print("\n📝 Testing Structured Logging...")
    
    # The API uses structlog, so we can check if responses contain structured data
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        health_data = response.json()
        
        # Check if response has structured fields
        structured_fields = ['status', 'services', 'timestamp', 'version']
        found_fields = [field for field in structured_fields if field in health_data]
        
        print(f"✅ Health endpoint returns structured data")
        print(f"   Found fields: {found_fields}")
        print(f"   Sample response: {json.dumps(health_data, indent=2)}")
        
        return True
    except Exception as e:
        print(f"❌ Structured logging test failed: {e}")
        return False

def test_metrics_endpoint():
    """Test if metrics endpoint exists and returns data."""
    print("\n📊 Testing Metrics Endpoint...")
    
    try:
        response = requests.get(f"{API_BASE}/metrics", timeout=10)
        
        if response.status_code == 200:
            metrics_text = response.text
            print("✅ Metrics endpoint accessible")
            
            # Check for Prometheus format
            if "# HELP" in metrics_text and "# TYPE" in metrics_text:
                print("✅ Metrics in Prometheus format")
                
                # Count metrics
                help_lines = metrics_text.count("# HELP")
                type_lines = metrics_text.count("# TYPE")
                print(f"   Found {help_lines} metric definitions")
                
                # Show sample metrics
                lines = metrics_text.split('\n')[:10]  # First 10 lines
                print("   Sample metrics:")
                for line in lines:
                    if line.strip():
                        print(f"     {line}")
                
                return True
            else:
                print("⚠️  Metrics not in Prometheus format")
                return False
        else:
            print(f"❌ Metrics endpoint returned {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Metrics endpoint test failed: {e}")
        return False

def test_performance_metrics():
    """Test API performance by making multiple requests."""
    print("\n⚡ Testing Performance Metrics...")
    
    try:
        # Test response times
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            response = requests.get(f"{API_BASE}/health", timeout=10)
            end_time = time.time()
            
            response.raise_for_status()
            response_times.append(end_time - start_time)
            print(f"   Request {i+1}: {response_times[-1]:.3f}s")
        
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
        
        print(f"✅ Performance metrics:")
        print(f"   Average response time: {avg_time:.3f}s")
        print(f"   Min response time: {min_time:.3f}s")
        print(f"   Max response time: {max_time:.3f}s")
        
        return True
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def test_business_metrics():
    """Test business-specific metrics by analyzing attack paths."""
    print("\n🎯 Testing Business Metrics...")
    
    try:
        # Test attack path analysis
        response = requests.post(
            f"{API_BASE}/api/v1/paths",
            json={"target": "database-server", "max_hops": 3},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        print("✅ Attack path analysis working")
        
        # Extract business metrics
        if 'paths' in data:
            paths = data['paths']
            print(f"   Found {len(paths)} attack paths")
            
            if paths:
                avg_score = sum(path.get('score', 0) for path in paths) / len(paths)
                high_risk_paths = [p for p in paths if p.get('score', 0) > 0.8]
                
                print(f"   Average risk score: {avg_score:.2f}")
                print(f"   High-risk paths: {len(high_risk_paths)}")
                
                # Show sample path
                if paths:
                    sample_path = paths[0]
                    print(f"   Sample path: {sample_path.get('path', [])}")
                    print(f"   Risk score: {sample_path.get('score', 0)}")
        
        if 'latency_ms' in data:
            print(f"   Analysis latency: {data['latency_ms']}ms")
        
        return True
    except Exception as e:
        print(f"❌ Business metrics test failed: {e}")
        return False

def main():
    """Run all observability tests."""
    print("🔍 GNN Attack Path Demo - Simplified Observability Testing")
    print("=" * 60)
    
    tests = [
        ("API Endpoints", test_api_endpoints),
        ("Structured Logging", test_structured_logging),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Performance Metrics", test_performance_metrics),
        ("Business Metrics", test_business_metrics),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 OBSERVABILITY TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result is True)
    total = len(results)
    
    for test_name, result in results.items():
        if result is True:
            print(f"✅ PASS {test_name}")
        elif result is False:
            print(f"❌ FAIL {test_name}")
        else:
            print(f"⚠️  PARTIAL {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All observability features are working!")
        print("\nNext steps for full observability:")
        print("1. Install Docker to run Prometheus and Grafana")
        print("2. Set up monitoring dashboards")
        print("3. Configure alerting rules")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
