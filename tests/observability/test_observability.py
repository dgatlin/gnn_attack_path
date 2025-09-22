#!/usr/bin/env python3
"""
Comprehensive observability testing script for GNN Attack Path Demo.
Tests Prometheus metrics, Grafana dashboards, and structured logging.
"""
import requests
import time
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE = "http://localhost:8000"
PROMETHEUS_BASE = "http://localhost:9090"
GRAFANA_BASE = "http://localhost:3001"

def test_api_health():
    """Test API health endpoint and check for metrics."""
    print("🔍 Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        response.raise_for_status()
        health_data = response.json()
        print(f"✅ API Health: {health_data['status']}")
        print(f"   Services: {health_data['services']}")
        return True
    except Exception as e:
        print(f"❌ API Health failed: {e}")
        return False

def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    print("\n📊 Testing Metrics Endpoint...")
    try:
        response = requests.get(f"{API_BASE}/metrics", timeout=10)
        response.raise_for_status()
        metrics_text = response.text
        
        # Check for key metrics
        key_metrics = [
            "http_requests_total",
            "http_request_duration_seconds",
            "attack_paths_analyzed_total"
        ]
        
        found_metrics = []
        for metric in key_metrics:
            if metric in metrics_text:
                found_metrics.append(metric)
        
        print(f"✅ Metrics endpoint accessible")
        print(f"   Found metrics: {found_metrics}")
        return len(found_metrics) > 0
    except Exception as e:
        print(f"❌ Metrics endpoint failed: {e}")
        return False

def test_prometheus_connection():
    """Test Prometheus server connection."""
    print("\n🔍 Testing Prometheus Connection...")
    try:
        # Test Prometheus API
        response = requests.get(f"{PROMETHEUS_BASE}/api/v1/query?query=up", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'success':
            print("✅ Prometheus API accessible")
            
            # Check for our API target
            targets_response = requests.get(f"{PROMETHEUS_BASE}/api/v1/targets", timeout=10)
            targets_data = targets_response.json()
            
            api_targets = [t for t in targets_data['data']['activeTargets'] 
                          if 'gnn-demo-api' in t.get('labels', {}).get('job', '')]
            
            if api_targets:
                print(f"✅ Found {len(api_targets)} API targets in Prometheus")
                for target in api_targets:
                    print(f"   - {target['labels']['job']}: {target['health']}")
            else:
                print("⚠️  No API targets found in Prometheus")
            
            return True
        else:
            print(f"❌ Prometheus query failed: {data}")
            return False
    except Exception as e:
        print(f"❌ Prometheus connection failed: {e}")
        return False

def test_grafana_connection():
    """Test Grafana server connection."""
    print("\n📈 Testing Grafana Connection...")
    try:
        response = requests.get(f"{GRAFANA_BASE}/api/health", timeout=10)
        response.raise_for_status()
        print("✅ Grafana server accessible")
        return True
    except Exception as e:
        print(f"❌ Grafana connection failed: {e}")
        return False

def generate_test_traffic():
    """Generate test traffic to create metrics and logs."""
    print("\n🚀 Generating Test Traffic...")
    
    test_requests = [
        {"endpoint": "/health", "method": "GET"},
        {"endpoint": "/metrics", "method": "GET"},
        {"endpoint": "/analyze-paths", "method": "POST", "data": {
            "target": "database-server",
            "max_hops": 3
        }},
        {"endpoint": "/crown-jewels", "method": "GET"},
        {"endpoint": "/algorithms", "method": "GET"},
    ]
    
    successful_requests = 0
    for i, req in enumerate(test_requests, 1):
        try:
            print(f"   Request {i}/{len(test_requests)}: {req['method']} {req['endpoint']}")
            
            if req['method'] == 'GET':
                response = requests.get(f"{API_BASE}{req['endpoint']}", timeout=10)
            else:
                response = requests.post(
                    f"{API_BASE}{req['endpoint']}", 
                    json=req.get('data', {}),
                    timeout=10
                )
            
            response.raise_for_status()
            successful_requests += 1
            print(f"   ✅ Success (status: {response.status_code})")
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
        
        # Small delay between requests
        time.sleep(0.5)
    
    print(f"\n📊 Generated {successful_requests}/{len(test_requests)} successful requests")
    return successful_requests > 0

def test_structured_logging():
    """Test structured logging by checking Docker logs."""
    print("\n📝 Testing Structured Logging...")
    try:
        # This would require docker-compose to be running
        import subprocess
        result = subprocess.run(
            ["docker-compose", "logs", "--tail=10", "api"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            logs = result.stdout
            print("✅ Docker logs accessible")
            
            # Check for JSON structured logs
            json_logs = []
            for line in logs.split('\n'):
                if line.strip().startswith('{'):
                    try:
                        json.loads(line.strip())
                        json_logs.append(line.strip())
                    except:
                        pass
            
            if json_logs:
                print(f"✅ Found {len(json_logs)} structured JSON logs")
                print("   Sample log entry:")
                print(f"   {json_logs[0][:100]}...")
            else:
                print("⚠️  No structured JSON logs found")
            
            return len(json_logs) > 0
        else:
            print("❌ Docker logs not accessible (is docker-compose running?)")
            return False
    except Exception as e:
        print(f"❌ Structured logging test failed: {e}")
        return False

def main():
    """Run all observability tests."""
    print("🔍 GNN Attack Path Demo - Observability Testing")
    print("=" * 50)
    
    tests = [
        ("API Health", test_api_health),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Prometheus Connection", test_prometheus_connection),
        ("Grafana Connection", test_grafana_connection),
        ("Test Traffic Generation", generate_test_traffic),
        ("Structured Logging", test_structured_logging),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 OBSERVABILITY TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All observability features are working!")
        print("\nNext steps:")
        print("1. Open Grafana: http://localhost:3001")
        print("2. Check Prometheus: http://localhost:9090")
        print("3. View API metrics: http://localhost:8000/metrics")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check the output above for details.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
