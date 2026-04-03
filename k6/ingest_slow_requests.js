import http from 'k6/http';
import { sleep } from 'k6';

const NGINX_URL = __ENV.NGINX_URL || "http://nginx";

export const options = {
  scenarios: {
    steady_load: {
      executor: 'constant-vus',
      vus: 5,
      duration: '2m',
    },
  },
};

export default function () {
  // Fast endpoints (baseline)
  http.get(`${NGINX_URL}/`);
  http.get(`${NGINX_URL}/api/users`);

  // Inject slow request every ~3 iterations
  if (__ITER % 3 === 0) {
    http.get(`${NGINX_URL}/api/users?delay=1.5`); // simulate 1.5s latency
  }

  sleep(2);
}
