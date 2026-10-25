## Quick daily tasks

The homepage includes Add a task for today. Each task is saved under the current date, has a completion checkbox and also appears in Daily routine for that date. Completed tasks count in recorded check-ins and active-day progress. Tasks are included in planner JSON backups and the Data explorer.

## Progress reviews and compound-interest savings

Progress & reviews replaces the earlier Monthly & yearly page. Select a month or year to see goals due in that period, update their completion, add period goals, see recorded check-ins and diary totals, and track an optional active-days target. Save a reflection to read it back, with Edit review available later. Existing reflections remain available.

The dedicated roadmap page has been removed; dated long-term goals remain in Goals & tasks.

Savings projections now include an optional nominal annual interest rate and annual, quarterly, monthly or daily compounding. Contributions occur at the end of each monthly period, using an equivalent monthly growth rate for the chosen frequency. The calculation separates deposits, projected interest and projected balance, and estimates the monthly contribution needed for a target. It does not change the actual saved amount. A zero rate retains simple savings projections. Periods are rounded up to whole months; fees, taxes and inflation are excluded. Calculation checks cover zero-rate, one-year, monthly-contribution and multiple-frequency scenarios.

## Daily-use improvements

Colour palette selection applies immediately and is saved. Goal and schedule forms save in place and remember the selected page on reload. Recurring schedule controls are labelled Edit; the Change from field determines when recurring changes apply.

The homepage includes today's habits and scheduled tasks, with a preview of tomorrow's timetable. Daily routine includes a diary with an explicit Save entry button, multiple timestamped entries per day, Add another entry and Edit entry. Editing retains the original timestamp and adds an edited timestamp. Existing notes are preserved as earlier entries; their original times are marked unavailable rather than invented. Drafts are saved as you write.

Diary entries are included in JSON backups, the Data explorer and (in local server mode) the diary_entries SQLite table.

# Planner

## Live demo

**[Try Planner in your browser](https://spr1nkies.github.io/planner-app/)**

Choose **Explore sample planner** to try fictional sample data, or complete the welcome form to start your own planner. No account or installation is required. Your entries stay in your browser; there is no cross-device sync.

The public demo supports tasks, habits, diary entries, recurring schedules, progress reviews, savings calculations and `.ics` file import. **Live calendar subscriptions require a backend and are not enabled on GitHub Pages.**

The demo is built from an explicit static asset list and contains no personal database, diary, timetable or subscription links.


A responsive personal planning app that connects daily habits, recurring schedules and long-term goals.

Built with HTML, CSS, vanilla JavaScript and an optional Python/SQLite backend. No frontend framework or package installation is required for local use.

## About the project

Planner started as a way to turn a weekly timetable into daily actions and connect those actions with bigger goals. It supports routines that change over time, including university timetables that apply for a single semester.

This portfolio edition starts with a blank setup. Users enter their own name, priorities, habits, goals and schedule.

## Features

- **Personal onboarding:** daily habits, monthly goals, yearly direction, themes and a personal intention.
- **Calendar-style week view:** timed activity blocks, overlapping sessions, week navigation and a Today button.
- **Semester schedules:** recurring weekdays, activity times, start dates and optional end dates.
- **Flexible changes:** edit one day, update future occurrences, skip a session or end a recurring activity while retaining earlier records.
- **Daily routine:** complete habits and scheduled sessions and record reflections.
- **Goals grouped by year:** add, edit, complete and delete goals; undated goals have their own section.
- **Progress reviews:** weekly tracking and monthly/yearly reflections and check-in totals.
- **Calendar imports:** preview and import `.ics` files, including recurring events and exceptions.
- **Calendar subscriptions:** HTTPS and `webcal` links through a calendar-fetch backend, with manual refresh and automatic refresh while the app is open.
- **Data tools:** JSON backup/restore, CSV export and a read-only data explorer. Local server mode adds SQLite storage and database export.

## Technology

| Component | Technology |
| --- | --- |
| Interface | HTML, CSS, vanilla JavaScript |
| Browser storage | localStorage |
| Optional local server | Python standard library |
| Local database | SQLite |
| iCalendar parsing | Vendored ical.js 2.2.1 |
| Optional hosted calendar endpoint | JavaScript Worker |

## Run locally

### Browser-only mode

Open `index.html` in a modern browser. Entries stay in the current browser. Direct-file storage behaviour may vary by browser.

Calendar **file upload** works without a backend. Calendar **subscription links** require the Python server or a hosted calendar endpoint.

### Python and SQLite mode

Use Python 3.10 or newer. In the project folder, run:

```sh
python3 server.py
```

On Windows:

```powershell
py -3 server.py
```

You can also use `start_mac_linux.sh` or `start_windows.bat`.

Open **http://127.0.0.1:8765**. The server creates `data/planner.sqlite3`. Press `Ctrl+C` to stop it; saved entries remain on disk.

To choose another port:

```sh
python3 server.py --port 8767
```

No `pip install` is needed.

## How to use it

1. Complete the welcome setup, or import an existing planner JSON backup.
2. Add habits and goals that reflect your priorities.
3. In **My schedule**, add recurring activities with weekdays, times and semester dates.
4. In **Daily routine**, complete activities for the selected date.
5. Review progress in **Weekly tracker** and **Progress & reviews**.
6. In **Goals & tasks**, use target dates to organise goals under year headings.

To connect a calendar, choose **My schedule → Connect calendar**, enter a subscription URL or select an `.ics` file, preview the events and confirm the import.

## Calendar behaviour

- File imports are snapshots; subscription links refresh on opening and every 30 minutes while the app is visible.
- Imported events cover the past 90 days and next 12 months.
- Recurrence rules, excluded dates, moved exceptions, cancellations, all-day/multi-day events and time zones are handled by the import pipeline.
- Imported events are read-only; edit their source calendar to change their schedule. You can complete or skip occurrences in Planner.
- Stable identifiers preserve completion history across refreshes. A failed refresh keeps the last successful event set.
- Flexible habits and scheduled sessions are separate tracking items.

## Data and privacy

Browser-only entries are stored on the current device. Local server mode also writes to SQLite; its database state takes precedence when loading from the server.

Use **Settings & backup** to export/import JSON. Backups can include private subscription links. Do not commit them to a public repository.

This repository excludes personal databases, timetable files, backups, credentials and personal screenshots. The local server binds to localhost and is not intended to be exposed publicly as-is. See [hosting options](docs/hosting.md) for the static demo and hosted calendar endpoint.

## Project structure

```text
index.html              App shell
styles.css              Themes, responsive layout and calendar styling
app.js                  Planner state, rendering and interactions
calendar-core.js        iCalendar parsing and event expansion
calendar_fetch.py       Safe local calendar retrieval
server.py               Local HTTP server and SQLite persistence
vendor/                 ical.js and its licence
hosting/                Optional hosted calendar endpoint and adapter
scripts/build-web.mjs   Build an explicit static asset bundle
docs/hosting.md         Hosting capabilities and limitations
```

## Design decisions

- **Vanilla JavaScript** keeps the project easy to run and inspect without a build system.
- **Versioned recurring activities** preserve earlier schedules when a semester or routine changes.
- **Single-day exceptions** let users change one occurrence without rewriting future weeks.
- **Separate event and completion records** keep calendar updates from erasing personal progress.
- **A local-first workflow** lets users begin without creating an account.

## Validation and limitations

Development checks covered JavaScript syntax, recurring schedule date boundaries, overlapping calendar events, onboarding, goal edits, imported recurrence exceptions, cancellations, stable identifiers, time-zone conversion and calendar endpoint URL restrictions. Representative screens were inspected in a browser.

A comprehensive automated test suite is not included yet. There are no cloud accounts, cross-device data sync, reminders or two-way calendar editing. Overnight manually entered activities should be split into two entries. The hosted endpoint supports a provider-domain allowlist; other feeds can use file upload. A static deployment alone cannot refresh subscription URLs.

## Future improvements

- Account-backed storage and cross-device sync.
- Reminders and notifications.
- More calendar providers and configurable sync settings.
- Broader accessibility and browser testing.
- Modularising the application code and adding automated tests.

## Development approach

Developed iteratively with AI-assisted implementation and debugging, guided by the planner's product requirements and design feedback.

## Licence and third-party code

A project-wide open-source licence has not been selected yet. Public source visibility does not grant an open-source licence.

The vendored ical.js library is distributed under MPL-2.0; its licence is included in [vendor/ICAL-LICENSE](vendor/ICAL-LICENSE).
