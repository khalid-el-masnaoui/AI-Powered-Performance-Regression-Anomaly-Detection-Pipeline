import http from "k6/http";

import { sleep } from "k6";

export const options = {

  scenarios: {

    // ---------------------------------------------------
    // BASELINE PHASE
    // ---------------------------------------------------

    baseline: {

      executor: "constant-arrival-rate",

      rate: 20,

      timeUnit: "1s",

      duration: "3m",

      preAllocatedVUs: 20,

      exec: "baselinePhase"
    },

    // ---------------------------------------------------
    // GRADUAL DEGRADATION
    // ---------------------------------------------------

    degradation: {

      executor: "constant-arrival-rate",

      rate: 20,

      timeUnit: "1s",

      startTime: "3m",

      duration: "2m",

      preAllocatedVUs: 20,

      exec: "degradationPhase"
    },

    // ---------------------------------------------------
    // MASSIVE REGRESSION SPIKE
    // ---------------------------------------------------

    spike: {

      executor: "constant-arrival-rate",

      rate: 40,

      timeUnit: "1s",

      startTime: "6m",

      duration: "1m",

      preAllocatedVUs: 50,

      exec: "spikePhase"
    },

    // ---------------------------------------------------
    // RECOVERY
    // ---------------------------------------------------

    recovery: {

      executor: "constant-arrival-rate",

      rate: 15,

      timeUnit: "1s",

      startTime: "8m",

      duration: "2m",

      preAllocatedVUs: 20,

      exec: "recoveryPhase"
    }
  }
};

const NGINX_URL = __ENV.NGINX_URL || "http://nginx";


// -------------------------------------------------------
// NORMAL BASELINE
// -------------------------------------------------------

export function baselinePhase() {

  http.get(`${NGINX_URL}/`);

  http.get(`${NGINX_URL}/api/users`);

  sleep(1);
}
