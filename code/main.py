"""Local presentation dashboard for the keyboard authentication prototype."""
import math
import os
import re
import secrets
import time
from collections import OrderedDict
from datetime import datetime, timezone
from threading import RLock

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from auth import authenticate, create_session, get_current_user, is_authenticated, logout
from engine_adapter import evaluate, keyboard_features, recorded_windows

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=512_000, SESSION_COOKIE_HTTPONLY=True,
                  SESSION_COOKIE_SAMESITE='Strict')
states = OrderedDict()
state_lock = RLock()


def get_state():
    sid = session.setdefault('dashboard_id', secrets.token_hex(24))
    now = time.monotonic()
    for key in list(states):
        if now - states[key]['touched'] > 3600:
            del states[key]
    if sid not in states:
        if len(states) >= 128:
            states.popitem(last=False)
        states[sid] = {'history': [], 'mode': None, 'replay_index': 0}
    states[sid]['touched'] = now
    return states[sid]


@app.before_request
def protect_api():
    if request.path.startswith('/api/'):
        if not is_authenticated():
            return jsonify(error='Your session has ended. Please sign in again.'), 401
        if request.method == 'POST' and not secrets.compare_digest(
                request.headers.get('X-CSRF-Token', ''), session.get('csrf', 'missing')):
            return jsonify(error='Session verification failed. Refresh the dashboard.'), 403


@app.route('/')
def home():
    return redirect(url_for('dashboard' if is_authenticated() else 'login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if authenticate(request.form.get('username'), request.form.get('password')):
            session.clear()
            create_session(request.form['username'])
            session['csrf'] = secrets.token_hex(24)
            return redirect(url_for('dashboard'))
        error = 'That username and password don’t match. Please try again.'
    return render_template('login.html', error=error)


@app.route('/dashboard')
def dashboard():
    if not is_authenticated():
        return redirect(url_for('login'))
    session.setdefault('csrf', secrets.token_hex(24))
    return render_template('dashboard.html', username=get_current_user(), csrf=session['csrf'])


@app.route('/logout', methods=['POST'])
def logout_user():
    if not secrets.compare_digest(request.form.get('csrf', ''), session.get('csrf', 'missing')):
        return redirect(url_for('login'))
    with state_lock:
        states.pop(session.get('dashboard_id'), None)
    logout()
    return redirect(url_for('login'))


@app.get('/api/state')
def state():
    with state_lock:
        current = get_state()
        return jsonify(history=current['history'], mode=current['mode'])


@app.post('/api/start')
def start():
    payload = request.get_json(silent=True) or {}
    mode = payload.get('mode') if isinstance(payload, dict) else None
    if mode not in ('live', 'replay'):
        return jsonify(error='Choose keyboard monitoring or recorded replay.'), 400
    with state_lock:
        current = get_state()
        current.update(history=[], mode=mode, replay_index=0)
    return jsonify(ok=True)


def validate_events(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('events'), list):
        raise ValueError('Expected a keyboard event window.')
    events = payload['events']
    if len(events) > 4000:
        raise ValueError('Too many keyboard events in one window.')
    clean = []
    for event in events:
        if not isinstance(event, dict):
            raise ValueError('Invalid keyboard event.')
        elapsed = event.get('elapsed_ms')
        if (isinstance(elapsed, bool) or not isinstance(elapsed, (float, int))
                or not math.isfinite(elapsed) or not 0 <= elapsed < 10000
                or event.get('event') not in ('press', 'release')
                or event.get('key_type') not in ('character', 'special')
                or not re.fullmatch(r'[a-f0-9]{64}', str(event.get('key_id', '')))):
            raise ValueError('Invalid keyboard timing data.')
        clean.append({key: event[key] for key in ('elapsed_ms', 'event', 'key_id', 'key_type')})
    return clean


@app.post('/api/window')
def process_window():
    with state_lock:
        current = get_state()
        try:
            if current['mode'] == 'replay':
                rows = recorded_windows()
                index = current['replay_index']
                if index >= len(rows):
                    return jsonify(done=True)
                features = rows.iloc[index].to_dict()
            elif current['mode'] == 'live':
                features = keyboard_features(validate_events(request.get_json(silent=True)))
            else:
                return jsonify(error='Start a monitoring session first.'), 409
            previous = current['history'][-1] if current['history'] else None
            result = evaluate(features, previous)
        except (ValueError, TypeError) as error:
            if 'keyboard' in str(error).lower() or 'events' in str(error).lower():
                return jsonify(error=str(error)), 400
            app.logger.exception('Engine evaluation failed')
            return jsonify(error='The scoring engine could not evaluate this window. Check the server log.'), 503
        except Exception:
            app.logger.exception('Engine unavailable')
            return jsonify(error='The scoring engine is unavailable. Check the model and installed dependencies.'), 503
        number = current['replay_index'] + 1
        result.update(number=number, timestamp=datetime.now(timezone.utc).isoformat(),
                      elapsed_seconds=number * 10, source=current['mode'])
        current['replay_index'] = number
        current['history'].append(result)
        current['history'] = current['history'][-120:]
        return jsonify(result=result, done=current['mode'] == 'replay' and number >= len(rows))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)))
