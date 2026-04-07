import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

const routes = [
  '/',
  '/api/users',
];

//const routes=$(shell curl -s http://localhost:8080/routes)

export default function () {
  routes.forEach(route => {
    http.get(`http://localhost:8080${route}`);
  });

  sleep(1);
}
