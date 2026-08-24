import React from 'react';

export const UserAvatar = ({ size = 36, showOnline = true, name = "Administrator" }) => {
  return (
    <div style={{
      position: 'relative',
      width: `${size}px`,
      height: `${size}px`,
      borderRadius: '50%',
      flexShrink: 0
    }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          border: '1.5px solid rgba(229, 169, 60, 0.4)',
          background: 'linear-gradient(135deg, #1E293B 0%, #0F172A 100%)',
          boxShadow: '0 2px 6px rgba(0, 0, 0, 0.15)'
        }}
      >
        <defs>
          <linearGradient id="avatarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1D4ED8" />
          </linearGradient>
          <linearGradient id="hairGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#E5A93C" />
            <stop offset="100%" stopColor="#B45309" />
          </linearGradient>
        </defs>
        
        {/* Background circle */}
        <circle cx="20" cy="20" r="20" fill="url(#avatarGrad)" />
        
        {/* Person Head & Hair Silhouette */}
        <path d="M20 9C15.5 9 13.5 12.5 13.5 16.5C13.5 21 16.2 24.5 20 24.5C23.8 24.5 26.5 21 26.5 16.5C26.5 12.5 24.5 9 20 9Z" fill="#FDE68A" />
        <path d="M13.5 15C13.5 11 16 8 20 8C24 8 26.5 11 26.5 15C25.5 11.5 23 10.5 20 10.5C17 10.5 14.5 11.5 13.5 15Z" fill="url(#hairGrad)" />
        
        {/* Person Torso / Suit */}
        <path d="M8.5 36C8.5 29.5 13.5 25.5 20 25.5C26.5 25.5 31.5 29.5 31.5 36C31.5 37.5 20 38 20 38C20 38 8.5 37.5 8.5 36Z" fill="#1E293B" />
        
        {/* Collar & Tie Accent */}
        <path d="M17.5 25.5L20 29.5L22.5 25.5H17.5Z" fill="#FFFFFF" />
        <path d="M19.3 29.5L18.8 35L20 36.5L21.2 35L20.7 29.5H19.3Z" fill="#E5A93C" />
      </svg>

      {showOnline && (
        <span style={{
          position: 'absolute',
          bottom: '0px',
          right: '0px',
          width: `${Math.max(8, Math.round(size * 0.24))}px`,
          height: `${Math.max(8, Math.round(size * 0.24))}px`,
          borderRadius: '50%',
          backgroundColor: '#10B981',
          border: '1.5px solid #FFFFFF',
          boxShadow: '0 0 4px rgba(16, 185, 129, 0.6)'
        }} />
      )}
    </div>
  );
};

export default UserAvatar;
