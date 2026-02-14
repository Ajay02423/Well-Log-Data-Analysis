import React from "react";

interface Props {
  onStart: () => void;
}

const Welcome: React.FC<Props> = ({ onStart }) => {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      width: '100%',
      minHeight: '90vh',
      textAlign: 'center',
      position: 'relative',
      overflow: 'hidden'
    }}>
      
      {/* 1. The Header */}
      <header className="hero-header" style={{ position: 'relative', zIndex: 2, marginBottom: '2.5rem' }}>
        <h1 className="hero-title" style={{ fontSize: '4rem', marginBottom: '0.5rem', fontWeight: 700 }}>
          Well Insights
        </h1>
        <p className="hero-sub" style={{ color: '#7881bd', fontSize: '1.3rem', marginTop: 0 }}>
          AI-assisted well log visualization and interpretation.
        </p>
      </header>

      {/* 2. The Card (Centered Text & Button) */}
      <div className="glass-card" style={{ 
        position: 'relative', 
        zIndex: 2, 
        maxWidth: '600px', 
        padding: '3rem', 
        textAlign: 'center', /* Forces text to middle */
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        margin: '0 20px'
      }}>
        <h2 style={{ fontSize: '2rem', marginBottom: '1rem', marginTop: 0 }}>Welcome</h2>
        <p style={{ marginBottom: '2rem', lineHeight: '1.6', fontSize: '1.1rem', color: '#537296' }}>
          Upload a LAS file to visualize logs, view cross-plots, and generate AI insights about your well data.
        </p>

        <button 
          className="btn primary" 
          onClick={onStart} 
          style={{ padding: '0.9rem 3rem', fontSize: '1.1rem' }}
        >
          Get Started
        </button>
      </div>

      {/* 3. The Visual Pulse (Moved to background for symmetry) */}
      <div style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 1,
        pointerEvents: 'none' // Ensures clicks go through to the card
      }}>
        <div className="pulse" style={{ width: '400px', height: '400px', opacity: 0.3 }} />
      </div>

    </div>
  );
};

export default Welcome;