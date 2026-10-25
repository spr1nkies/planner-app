// Optional Cloudflare Worker adapter. Authentication, provider access policy,
// and production rate limits must be configured for the chosen audience.
import {handleApi} from './calendar-backend.js';
export default {async fetch(request,env){if(new URL(request.url).pathname==='/api/calendar-fetch')return handleApi(request);return env.ASSETS.fetch(request)}};
