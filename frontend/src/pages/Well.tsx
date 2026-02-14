import React, { useEffect, useState } from "react";
import UploadLas from "../components/UploadLas";
import LogViewer from "../components/LogViewer";
import { api } from "../api/client";

const POLL_INTERVAL = 2000;

interface WellProps {
  initialWellId?: string | null;
  onWellIdChange?: (id: string) => void;
  // NEW PROP
  onDataLoaded?: (stats: { minDepth: number; maxDepth: number; curves: string[] }) => void;
}

const Well: React.FC<WellProps> = ({ initialWellId = null, onWellIdChange, onDataLoaded }) => {
  const [wellId, setWellId] = useState<string | null>(initialWellId);
  const [ready, setReady] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  
  // Data State
  const [curves, setCurves] = useState<string[]>([]);
  const [minDepth, setMinDepth] = useState<number>(0);
  const [maxDepth, setMaxDepth] = useState<number>(0);
  
  // Viewer State
  const [selectedCurves, setSelectedCurves] = useState<string[]>([]);
  const [fromDepth, setFromDepth] = useState<number>(0);
  const [toDepth, setToDepth] = useState<number>(0);

  useEffect(() => {
    if (!wellId) return;

    let cancelled = false;
    let interval: any;

    const poll = async () => {
      try {
        const progRes = await api.get(`/wells/${wellId}/progress`);
        if (!cancelled) setProgress(progRes.data.progress ?? 0);

        const wellRes = await api.get(`/wells/${wellId}`);
        if (!wellRes.data?.is_ready || cancelled) return;

        const curvesRes = await api.get<string[]>(`/wells/${wellId}/curves`);
        const depthRes = await api.get(`/wells/${wellId}/depth-range`);

        if (cancelled) return;

        setCurves(curvesRes.data);
        setMinDepth(depthRes.data.min_depth);
        setMaxDepth(depthRes.data.max_depth);
        setFromDepth(depthRes.data.min_depth);
        setToDepth(depthRes.data.max_depth);
        setReady(true);
        
        // NEW: Inform Parent (App.tsx) that data is ready
        if (onDataLoaded) {
          onDataLoaded({
            minDepth: depthRes.data.min_depth,
            maxDepth: depthRes.data.max_depth,
            curves: curvesRes.data
          });
        }

        clearInterval(interval);
      } catch (e) {
        if (!cancelled) setError("Processing failed.");
      }
    };

    poll();
    interval = setInterval(poll, POLL_INTERVAL);
    return () => { cancelled = true; clearInterval(interval); };
  }, [wellId]);

  const handleUploadSuccess = (id: string) => {
    setWellId(id);
    if (onWellIdChange) onWellIdChange(id);
    setReady(false);
    setCurves([]);
    setProgress(0);
    setError(null);
  };

  if (!wellId) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', height: '80vh', width: '100%' }}>
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center', maxWidth: '500px' }}>
          <h1>Analyze Well Data</h1>
          <p style={{ color: '#6d5353', marginBottom: '2rem' }}>Upload a .LAS file to generate logs and AI insights.</p>
          <UploadLas onUploaded={handleUploadSuccess} isCompact={false} />
          {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
      </div>
    );
  }

// Inside your Well.tsx return statement...

// ...
  // --- STATE 2: DASHBOARD ---
  return (
    // Changed maxWidth to 100% and added overflow hidden to prevent horizontal scroll
    <div style={{ padding: '20px', width: '100%', boxSizing: 'border-box', overflowX: 'hidden' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Well Dashboard</h2>
        <UploadLas onUploaded={handleUploadSuccess} isCompact={true} />
      </div>

      {!ready && (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <h3>Processing File... {progress.toFixed(0)}%</h3>

          <div
            style={{
              width: '100%',
              maxWidth: '400px',
              height: '10px',
              background: '#333',
              margin: '10px auto',
              borderRadius: '5px',
              overflow: 'hidden'
            }}
          >
            <div
              style={{
                width: `${Math.min(progress, 100)}%`,
                height: '100%',
                background: '#646cff',
                borderRadius: '5px',
                transition: 'width 0.4s ease'
              }}
            />
          </div>

          {error && <p style={{ color: 'red' }}>{error}</p>}
        </div>
      )}


      {ready && (
        <div style={{ width: '100%' }}>
            <LogViewer
              wellId={wellId!}
              availableCurves={curves}
              minDepth={minDepth}
              maxDepth={maxDepth}
              selectedCurves={selectedCurves}
              setSelectedCurves={setSelectedCurves}
              fromDepth={fromDepth}
              toDepth={toDepth}
              setFromDepth={setFromDepth}
              setToDepth={setToDepth}
            />
        </div>
      )}
    </div>
  );
// ...
};

export default Well;