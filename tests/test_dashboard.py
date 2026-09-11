"""Integration checks against the repository's actual saved model."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'code'))
from main import app, states
from engine_adapter import evaluate, keyboard_features, recorded_windows
from src.authentication.engine import AuthenticationEngine


class DashboardTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        states.clear()
        self.client = app.test_client()
        self.client.post('/login', data={'username': 'anjali', 'password': 'password123'})
        with self.client.session_transaction() as session:
            self.headers = {'X-CSRF-Token': session['csrf']}

    def post(self, path, data):
        return self.client.post(path, json=data, headers=self.headers)

    def test_authentication_and_csrf(self):
        anonymous = app.test_client()
        self.assertEqual(anonymous.get('/api/state').status_code, 401)
        self.assertEqual(anonymous.get('/dashboard').status_code, 302)
        self.assertEqual(self.client.post('/api/start', json={'mode': 'live'}).status_code, 403)
        response = anonymous.post('/login', data={'username': 'anjali', 'password': 'wrong'})
        self.assertIn(b'don\xe2\x80\x99t match', response.data)
        self.assertEqual(self.client.get('/dashboard').status_code, 200)

    def test_replay_matches_stateful_engine_and_holds_idle_trust(self):
        self.post('/api/start', {'mode': 'replay'})
        engine = AuthenticationEngine()
        results = []
        for _, row in recorded_windows().iterrows():
            expected = engine.process_window(row)
            response = self.post('/api/window', {})
            self.assertEqual(response.status_code, 200)
            result = response.json['result']
            for key in ('trust_score', 'status', 'decision', 'is_active', 'prediction'):
                self.assertEqual(result[key], expected[key])
            results.append(result)
        self.assertFalse(results[-1]['is_active'])
        self.assertEqual(results[-1]['trust_score'], results[-2]['trust_score'])
        self.assertTrue(response.json['done'])
        self.assertEqual(self.post('/api/window', {}).json, {'done': True})
        self.assertEqual(len(self.client.get('/api/state').json['history']), 7)

    def test_live_metrics_and_idle_windows(self):
        self.post('/api/start', {'mode': 'live'})
        idle = self.post('/api/window', {'events': []}).json['result']
        self.assertIsNone(idle['trust_score'])
        events = []
        for i in range(10):
            for action, offset in [('press', 0), ('release', 100)]:
                events.append({'event': action, 'elapsed_ms': i * 350 + offset,
                               'key_id': f'{i:064x}', 'key_type': 'character'})
        response = self.post('/api/window', {'events': events})
        self.assertEqual(response.status_code, 200)
        result = response.json['result']
        self.assertEqual(result['metrics']['characters_per_second'], 1)
        self.assertEqual(result['metrics']['mean_hold_ms'], 100)
        self.assertEqual(result['metrics']['mean_flight_ms'], 250)
        self.assertEqual(result['metrics']['std_hold_ms'], 0)
        self.assertEqual(result['metrics']['pause_count'], 0)
        idle = self.post('/api/window', {'events': []}).json['result']
        self.assertEqual(idle['trust_score'], result['trust_score'])
        self.assertEqual(idle['decision'], result['decision'])

    def test_sparse_and_unmatched_events_do_not_crash_extractor(self):
        for action in ('press', 'release'):
            result = keyboard_features([dict(event=action, elapsed_ms=10,
                                            key_id='a' * 64, key_type='character')])
            self.assertFalse(result['is_active'])
            self.assertIsNone(evaluate(result)['trust_score'])

    def test_invalid_input_and_session_isolation(self):
        self.assertEqual(self.post('/api/start', {'mode': 'mouse'}).status_code, 400)
        self.post('/api/start', {'mode': 'live'})
        for payload in ([], {}, {'events': [None]}, {'events': [{'elapsed_ms': -1}]},
                        {'events': [{'elapsed_ms': 5, 'event': 'press', 'key_id': 'raw-key', 'key_type': 'character'}]}):
            self.assertEqual(self.post('/api/window', payload).status_code, 400)
        self.post('/api/window', {'events': []})
        other = app.test_client()
        other.post('/login', data={'username': 'anjali', 'password': 'password123'})
        self.assertEqual(other.get('/api/state').json['history'], [])
        self.assertEqual(len(self.client.get('/api/state').json['history']), 1)

    def test_engine_failure_is_explicit(self):
        self.post('/api/start', {'mode': 'replay'})
        with patch('main.evaluate', side_effect=FileNotFoundError('model missing')):
            with self.assertLogs(app.logger, level='ERROR'):
                response = self.post('/api/window', {})
        self.assertEqual(response.status_code, 503)
        self.assertIn('unavailable', response.json['error'])
        self.assertEqual(self.client.get('/api/state').json['history'], [])

    def test_logout_clears_state(self):
        self.post('/api/start', {'mode': 'live'})
        self.client.post('/logout', data={'csrf': self.headers['X-CSRF-Token']})
        self.assertEqual(self.client.get('/api/state').status_code, 401)
        self.assertEqual(len(states), 0)


if __name__ == '__main__':
    unittest.main()
