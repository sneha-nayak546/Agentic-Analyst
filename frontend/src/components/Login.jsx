import React, { useState } from 'react';
import { Sparkles, ArrowRight, Lock, Mail, ShieldCheck } from 'lucide-react';
import Spotlight from './Spotlight';
import './Login.css';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please enter both email and password');
      return;
    }
    
    setIsLoading(true);
    // Simulate authentication
    setTimeout(() => {
      setIsLoading(false);
      onLogin();
    }, 1500);
  };

  return (
    <div className="login-container">
      {/* 3D Background with Aceternity Spotlight */}
      <div className="login-bg-elements">
        <Spotlight
          className="login-spotlight-gold"
          fill="#F59E0B"
          fillOpacity={0.20}
          filterId="login-spotlight-gold"
        />
        <Spotlight
          className="login-spotlight-blue"
          fill="#1677FF"
          fillOpacity={0.10}
          filterId="login-spotlight-blue"
        />
        <div className="login-orb"></div>
        <div className="login-orb-glow"></div>
        <div className="login-grid"></div>
      </div>

      <div className="login-card premium-card animate-slide-up">
        <div className="login-header">
          <div className="login-logo">
            <Sparkles size={24} className="primary-sparkle" />
            <span>JGH Intelligence</span>
          </div>
          <h1 className="login-title">Welcome Back</h1>
          <p className="login-subtitle">Sign in to your enterprise data hub</p>
        </div>

        {error && (
          <div className="login-error">
            <Lock size={14} />
            <span>{error}</span>
          </div>
        )}

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Email Address</label>
            <div className="input-wrapper">
              <Mail size={16} className="input-icon" />
              <input 
                type="email" 
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(''); }}
                placeholder="admin@jgh.com" 
              />
            </div>
          </div>

          <div className="input-group">
            <label>Password</label>
            <div className="input-wrapper">
              <Lock size={16} className="input-icon" />
              <input 
                type="password" 
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(''); }}
                placeholder="••••••••" 
              />
            </div>
          </div>

          <button 
            type="submit" 
            className={`login-submit-btn ${isLoading ? 'loading' : ''}`}
            disabled={isLoading}
          >
            {isLoading ? (
              <div className="login-spinner"></div>
            ) : (
              <>
                Sign In to Dashboard <ArrowRight size={16} />
              </>
            )}
          </button>
        </form>

        <div className="login-footer">
          <ShieldCheck size={14} />
          <span>Secured by JGH Enterprise Auth</span>
        </div>
      </div>
    </div>
  );
};

export default Login;
