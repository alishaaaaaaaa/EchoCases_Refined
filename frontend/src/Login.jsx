import React, { useState } from 'react';
import { Shield, Lock } from 'lucide-react';
import { login } from './api';

export default function Login({ onLogin, theme = 'hacker' }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const hacker = theme === 'hacker';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      const session = await login(username, password);
      setPassword('');
      onLogin(session);
    } catch (err) {
      setError(err.message === 'Failed to fetch'
        ? 'Cannot reach the server. Is the backend running?'
        : err.message);
    }
    setSubmitting(false);
  };

  return (
    <div className={`app login-screen ${theme}`}>
      {hacker && <div className="scanline"></div>}
      <form className={`login-card ${theme}`} onSubmit={handleSubmit}>
        <div className="login-brand">
          <Shield className={`shield-icon ${theme}`} size={40} />
          <div>
            <h1>{hacker ? 'ECHOCASES' : 'EchoCases'}</h1>
            <p className="login-subtitle">
              {hacker ? '║ AUTHORIZED PERSONNEL ONLY ║' : 'Sign in to access case data'}
            </p>
          </div>
        </div>

        <label className="login-label" htmlFor="login-username">
          {hacker ? 'OPERATOR ID' : 'Username'}
        </label>
        <input
          id="login-username"
          className={`login-input ${theme}`}
          autoComplete="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
          required
        />

        <label className="login-label" htmlFor="login-password">
          {hacker ? 'PASSPHRASE' : 'Password'}
        </label>
        <input
          id="login-password"
          type="password"
          className={`login-input ${theme}`}
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        {error && <div className={`login-error ${theme}`} role="alert">{error}</div>}

        <button type="submit" className={`login-button ${theme}`} disabled={submitting}>
          <Lock size={16} />
          {submitting
            ? (hacker ? 'AUTHENTICATING...' : 'Signing in...')
            : (hacker ? '[AUTHENTICATE]' : 'Sign in')}
        </button>

        <p className="login-footnote">
          Accounts are issued by an administrator. Access is logged.
        </p>
      </form>
    </div>
  );
}
