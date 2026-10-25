#!/usr/bin/env python3
"""Planner: local web server + visible SQLite database.

Standard library only; no pip installs or online services needed.
Run: python server.py
Browser: http://127.0.0.1:8765
Database: ./data/planner.sqlite3

Security: binds to localhost only. Do not expose this server publicly.
"""
from __future__ import annotations
from calendar_fetch import fetch_calendar

import argparse
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sqlite3
import tempfile
from urllib.parse import urlsplit
import threading
import webbrowser

ROOT = Path(__file__).resolve().parent
DB = ROOT / 'data' / 'planner.sqlite3'
MAX_JSON_BYTES = 8 * 1024 * 1024

DDL = '''
CREATE TABLE IF NOT EXISTS planner_state (
    id INTEGER PRIMARY KEY CHECK(id=1),
    state_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY, title TEXT, area TEXT, due TEXT, completed INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS daily_entries (
    day TEXT PRIMARY KEY, note TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS diary_entries (
    day TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL,
    created_at TEXT, updated_at TEXT, PRIMARY KEY(day, id)
);
CREATE TABLE IF NOT EXISTS daily_checks (
    day TEXT NOT NULL, task TEXT NOT NULL, completed INTEGER NOT NULL,
    PRIMARY KEY(day, task)
);
CREATE TABLE IF NOT EXISTS weekly_counts (
    week_start TEXT NOT NULL, category TEXT NOT NULL, count INTEGER NOT NULL,
    PRIMARY KEY(week_start, category)
);
CREATE TABLE IF NOT EXISTS weekly_targets (
    category TEXT PRIMARY KEY, target INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS monthly_reviews (
    month TEXT PRIMARY KEY, focus TEXT, wins TEXT, adjustment TEXT
);
CREATE TABLE IF NOT EXISTS yearly_reviews (
    year TEXT PRIMARY KEY, focus TEXT, success TEXT, reflection TEXT
);
CREATE TABLE IF NOT EXISTS savings (
    category TEXT PRIMARY KEY, target REAL, saved REAL, monthly_amount REAL
);
CREATE TABLE IF NOT EXISTS other_settings (
    key TEXT PRIMARY KEY, value TEXT NOT NULL
);
'''


def connect(db_path: Path = DB):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=8)
    conn.execute('PRAGMA busy_timeout=8000')
    conn.executescript(DDL)
    return conn


def validate(state):
    if (not isinstance(state, dict) or state.get('version') != 1 or
        not isinstance(state.get('goals'), list) or
        not isinstance(state.get('daily'), dict) or
        not isinstance(state.get('weeklyStats'), dict) or
        not isinstance(state.get('weeklyGoals'), dict) or
        not isinstance(state.get('finance'), dict)):
        raise ValueError('Unsupported planner data: expected backup version 1')
    return state


def to_text(value):
    return str(value if value is not None else '')


def to_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError, OverflowError):
        return 0


def save_state(state: dict, db_path: Path = DB) -> str:
    state = validate(state)
    timestamp = datetime.now(timezone.utc).isoformat(timespec='seconds')
    # Keep complete JSON AND human-readable relational tables in one transaction.
    with connect(db_path) as db:
        db.execute('INSERT INTO planner_state(id,state_json,updated_at) VALUES(1,?,?) '
                   'ON CONFLICT(id) DO UPDATE SET state_json=excluded.state_json,updated_at=excluded.updated_at',
                   (json.dumps(state, ensure_ascii=False), timestamp))
        for name in ('goals', 'daily_entries', 'diary_entries', 'daily_checks', 'weekly_counts', 'weekly_targets',
                     'monthly_reviews', 'yearly_reviews', 'savings', 'other_settings'):
            db.execute(f'DELETE FROM {name}')
        for goal in state.get('goals', []):
            if not isinstance(goal, dict):
                continue
            db.execute('INSERT OR REPLACE INTO goals VALUES (?,?,?,?,?)',
                       (to_text(goal.get('id')), to_text(goal.get('title')), to_text(goal.get('area')),
                        to_text(goal.get('due')), int(bool(goal.get('done')))))
        for day, value in state.get('daily', {}).items():
            if not isinstance(value, dict):
                continue
            db.execute('INSERT INTO daily_entries VALUES (?,?)', (to_text(day), to_text(value.get('note'))))
            for entry in value.get('diaryEntries', []):
                if isinstance(entry, dict):
                    db.execute('INSERT OR REPLACE INTO diary_entries VALUES (?,?,?,?,?)',
                               (to_text(day), to_text(entry.get('id')), to_text(entry.get('text')),
                                to_text(entry.get('createdAt')), to_text(entry.get('updatedAt'))))
            for task, done in (value.get('checks') or {}).items():
                db.execute('INSERT INTO daily_checks VALUES (?,?,?)', (to_text(day), to_text(task), int(bool(done))))
        for week, counts in state.get('weeklyStats', {}).items():
            if not isinstance(counts, dict):
                continue
            for category, count in counts.items():
                db.execute('INSERT INTO weekly_counts VALUES (?,?,?)', (to_text(week), to_text(category), int(to_number(count))))
        for category, target in state.get('weeklyGoals', {}).items():
            db.execute('INSERT INTO weekly_targets VALUES (?,?)', (to_text(category), int(to_number(target))))
        for month, review in state.get('monthReviews', {}).items():
            if isinstance(review, dict):
                db.execute('INSERT INTO monthly_reviews VALUES (?,?,?,?)',
                           (to_text(month), to_text(review.get('focus')), to_text(review.get('wins')), to_text(review.get('adjust'))))
        for year, review in state.get('yearReviews', {}).items():
            if isinstance(review, dict):
                db.execute('INSERT INTO yearly_reviews VALUES (?,?,?,?)',
                           (to_text(year), to_text(review.get('focus')), to_text(review.get('success')), to_text(review.get('reflection'))))
        fin = state.get('finance') or {}
        for category in ('wedding', 'education'):
            db.execute('INSERT INTO savings VALUES (?,?,?,?)',
                       (category, to_number(fin.get(category+'Goal')), to_number(fin.get(category+'Saved')),
                        to_number(fin.get(category+'Monthly'))))
        settings = {
            'jobStatus': state.get('jobStatus', 'searching'),
            'educationChoice': state.get('educationChoice', 'exploring'),
            **{'notes.'+k: v for k, v in (state.get('notes') or {}).items()},
        }
        for key, value in settings.items():
            db.execute('INSERT INTO other_settings VALUES (?,?)', (to_text(key), to_text(value)))
    return timestamp


def get_state(db_path: Path = DB):
    with connect(db_path) as db:
        row = db.execute('SELECT state_json,updated_at FROM planner_state WHERE id=1').fetchone()
    return (json.loads(row[0]), row[1]) if row else (None, None)


class Handler(BaseHTTPRequestHandler):
    server_version = 'Planner/2.0'

    def send_json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == '/api/state':
            value, updated = get_state()
            return self.send_json({'state': value, 'updatedAt': updated, 'database': 'data/planner.sqlite3'})
        if path == '/api/health':
            return self.send_json({'ok': True, 'database': 'data/planner.sqlite3'})
        if path == '/api/download-db':
            # Use SQLite's online backup API so download is a consistent, standalone copy.
            with tempfile.TemporaryDirectory() as td:
                target = Path(td) / 'planner.sqlite3'
                with connect() as src, sqlite3.connect(target) as dst:
                    src.backup(dst)
                content = target.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'application/vnd.sqlite3')
            self.send_header('Content-Disposition', 'attachment; filename="planner.sqlite3"')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            return self.wfile.write(content)
        assets = {'/': ('index.html', 'text/html; charset=utf-8'),
                  '/index.html': ('index.html', 'text/html; charset=utf-8'),
                  '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
                  '/calendar-core.js': ('calendar-core.js', 'text/javascript; charset=utf-8'),
                  '/vendor/ical.js': ('vendor/ical.js', 'text/javascript; charset=utf-8'),
                  '/app.js': ('app.js', 'text/javascript; charset=utf-8')}
        if path not in assets:
            return self.send_error(404, 'Not found')
        filename, mime = assets[path]
        body = (ROOT / filename).read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if urlsplit(self.path).path not in ('/api/state','/api/calendar-fetch'):
            return self.send_error(404)
        origin = self.headers.get('Origin')
        # Do not accept writes cross-origin, even from other locally opened websites.
        if origin and origin not in (f'http://127.0.0.1:{self.server.server_port}',
                                    f'http://localhost:{self.server.server_port}'):
            return self.send_json({'error': 'Cross-origin writes are not permitted'}, 403)
        if not self.headers.get('Content-Type', '').startswith('application/json'):
            return self.send_json({'error': 'Use application/json'}, 415)
        try:
            n = int(self.headers.get('Content-Length', '0'))
            if n <= 0 or n > MAX_JSON_BYTES:
                return self.send_json({'error': 'Invalid or oversized request'}, 413)
            state = json.loads(self.rfile.read(n))
            if urlsplit(self.path).path == '/api/calendar-fetch':
                try:
                    return self.send_json({'calendar': fetch_calendar(state.get('url',''))})
                except Exception:
                    return self.send_json({'error':'Could not retrieve this calendar. Use an accessible HTTPS/webcal subscription link (not a sharing page).'}, 400)
            stamp = save_state(state)
            return self.send_json({'saved': True, 'updatedAt': stamp})
        except (ValueError, TypeError, sqlite3.Error) as e:
            return self.send_json({'error': str(e)}, 400)


def main():
    parser = argparse.ArgumentParser(description='Run your private life planner with local SQLite storage')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--no-browser', action='store_true')
    options = parser.parse_args()
    connect().close()
    url = f'http://127.0.0.1:{options.port}'
    print(f'\nPlanner running: {url}')
    print(f'Database file: {DB}')
    print('Close the terminal or press Ctrl+C to stop.\n')
    if not options.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        ThreadingHTTPServer(('127.0.0.1', options.port), Handler).serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped. Your database stays saved on disk.')


if __name__ == '__main__':
    main()
