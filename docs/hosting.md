## Public GitHub Pages demo

The repository workflow builds the static demo with `node scripts/build-web.mjs --demo` from the repository root, then uploads only `dist/`. Configure repository Settings → Pages → Source → GitHub Actions.

The demo runs at https://spr1nkies.github.io/planner-app/ . It offers a fictional sample planner and a fresh personal setup, saving records in the current browser. Calendar-file uploads work; subscription URL controls are hidden because GitHub Pages cannot run the calendar-fetch backend.

# Hosting options

## Static portfolio demo

The root `index.html`, `styles.css`, `app.js`, `calendar-core.js` and `vendor/` directory run without a build step. Host these files together. The app saves each visitor's data in their browser.

A static host does not execute `server.py` or provide `/api/calendar-fetch`. Calendar file upload works in static mode. Subscription links need a backend on the same origin; they will otherwise show an explanatory error.

`scripts/build-web.mjs` creates an explicit `dist/` asset bundle without databases, backups or backend source files. It requires Node.js. This bundle is suitable for static hosting; it does not add a calendar backend.

## Calendar subscription backend

`calendar_fetch.py` implements the localhost Python endpoint. It validates public DNS addresses and pins the connection to a checked IP, with HTTPS, response limits, timeouts and redirect validation.

`hosting/calendar-backend.js` provides a hosted Worker implementation. It permits subscription links from a bounded set of Google, Outlook and iCloud domains and validates every redirect. Other calendars can use `.ics` file upload. `hosting/worker.js` is an optional adapter expecting an `ASSETS` static asset binding.

Before exposing a hosted backend publicly, configure its audience/authentication and rate limits. Review any additions to the feed-domain allowlist. Never commit actual subscription links, tokens or planner records. No particular cloud account, existing private Site identity or credentials are included in this repository.

## Storage

This version does not have an account-backed online database. Hosting the interface does not add cross-device syncing. Export/import JSON to move entries between browsers or origins. Subscription links are included in planner backups, so keep those backups private.
