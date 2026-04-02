import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

const NGINX_URL = __ENV.NGINX_URL || "http://nginx";

const routes = [
  '/',
  '/api/users',
];

export default function () {
  routes.forEach(route => {
    http.get(`${NGINX_URL}${route}`);
  });

  sleep(1);
}
