/**
 * K6 performance tests for GNN Attack Path Demo API
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95% of requests under 2s
    http_req_failed: ['rate<0.1'],     // Error rate under 10%
    errors: ['rate<0.1'],              // Custom error rate under 10%
  },
};

const BASE_URL = 'http://localhost:8000';

export function setup() {
  // Health check before starting tests
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check passed': (r) => r.status === 200,
  });
  
  if (healthResponse.status !== 200) {
    throw new Error('API is not healthy');
  }
  
  return { baseUrl: BASE_URL };
}

export default function(data) {
  const baseUrl = data.baseUrl;
  
  // Test 1: Health check
  const healthResponse = http.get(`${baseUrl}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(healthResponse.status !== 200);
  
  sleep(1);
  
  // Test 2: Get attack paths
  const attackPathsPayload = JSON.stringify({
    target: 'crown-jewel-db-001',
    algorithm: 'hybrid',
    max_hops: 4,
    k: 5
  });
  
  const attackPathsResponse = http.post(`${baseUrl}/api/v1/paths`, attackPathsPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(attackPathsResponse, {
    'attack paths status is 200': (r) => r.status === 200,
    'attack paths response time < 2000ms': (r) => r.timings.duration < 2000,
    'attack paths has paths array': (r) => {
      const body = JSON.parse(r.body);
      return Array.isArray(body.paths);
    },
  });
  errorRate.add(attackPathsResponse.status !== 200);
  
  sleep(1);
  
  // Test 3: Get crown jewels
  const crownJewelsResponse = http.get(`${baseUrl}/api/v1/crown-jewels`);
  check(crownJewelsResponse, {
    'crown jewels status is 200': (r) => r.status === 200,
    'crown jewels response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  errorRate.add(crownJewelsResponse.status !== 200);
  
  sleep(1);
  
  // Test 4: Process natural language query
  const queryPayload = JSON.stringify({
    query: "Where's my riskiest path to the crown jewel database?",
    context: {}
  });
  
  const queryResponse = http.post(`${baseUrl}/api/v1/query`, queryPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(queryResponse, {
    'query status is 200': (r) => r.status === 200,
    'query response time < 5000ms': (r) => r.timings.duration < 5000,
    'query has results': (r) => {
      const body = JSON.parse(r.body);
      return body.results && typeof body.results === 'object';
    },
  });
  errorRate.add(queryResponse.status !== 200);
  
  sleep(1);
  
  // Test 5: Simulate remediation
  const remediationPayload = JSON.stringify({
    actions: [
      "remove_public_ingress:sg-web-001",
      "apply_patch:vm-app-001",
      "revoke_iam_permission:ci-user"
    ],
    simulate: true
  });
  
  const remediationResponse = http.post(`${baseUrl}/api/v1/remediate`, remediationPayload, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  check(remediationResponse, {
    'remediation status is 200': (r) => r.status === 200,
    'remediation response time < 3000ms': (r) => r.timings.duration < 3000,
    'remediation has risk reduction': (r) => {
      const body = JSON.parse(r.body);
      return typeof body.risk_reduction === 'number';
    },
  });
  errorRate.add(remediationResponse.status !== 200);
  
  sleep(1);
}

export function teardown(data) {
  // Cleanup if needed
  console.log('Performance test completed');
}
