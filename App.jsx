
import React, { useEffect, useState } from 'react';
import './App.css';

function App() {
  const [source, setSource] = useState('video');
  const [vehicleCount, setVehicleCount] = useState(0);
  const [streamUrl, setStreamUrl] = useState('');
  const [showStream, setShowStream] = useState(false);

  const handleStart = () => {
    const url = `http://localhost:5000/video_feed?source=${source}`;
    setStreamUrl(url);
    setShowStream(true);
  };

  const handleStop = async () => {
    await fetch('http://localhost:5000/stop_webcam', { method: 'POST' });
    setShowStream(false);
    setVehicleCount(0);
  };

  useEffect(() => {
    let interval;
    if (showStream) {
      interval = setInterval(() => {
        fetch('http://localhost:5000/vehicle_count')
          .then(res => res.json())
          .then(data => setVehicleCount(data.count))
          .catch(err => console.error('Error:', err));
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [showStream]);

  return (
    <div className="App">
      <h1>🚗 Traffic Surveillance System</h1>
      <div className="controls">
        <label>Select Source: </label>
        <select value={source} onChange={e => setSource(e.target.value)}>
          <option value="video">Video</option>
          <option value="webcam">Webcam</option>
        </select>
        <button onClick={handleStart}>Start Feed</button>
        <button onClick={handleStop}>Stop Feed</button>
      </div>

      {showStream && (
        <div className="video-section">
          <img src={streamUrl} alt="Live Feed" style={{ maxWidth: '100%', border: '2px solid #ccc' }} />
          <h2>Vehicle Count: <span>{vehicleCount}</span></h2>
        </div>
      )}
    </div>
  );
}

export default App;
