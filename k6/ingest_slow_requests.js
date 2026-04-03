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
