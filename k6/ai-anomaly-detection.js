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
