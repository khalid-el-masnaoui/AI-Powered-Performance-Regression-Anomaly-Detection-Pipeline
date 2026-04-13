import http from 'k6/http';
import { sleep } from 'k6';

export const options = {
  vus: 20,
  duration: '2m',
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
