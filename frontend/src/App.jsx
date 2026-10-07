import React, { useState, useEffect, useMemo } from 'react';
import Map, { Marker, Popup, Source, Layer } from 'react-map-gl';
import { MapPin, Search, AlertCircle, Clock, Map as MapIcon, Database, Activity, Shield, Calendar, Filter, Play, Pause, SkipBack, SkipForward, ZoomIn, ChevronDown, ChevronUp, X, Brain, ToggleLeft, ToggleRight, LogOut, User } from 'lucide-react';
import 'mapbox-gl/dist/mapbox-gl.css';
import './App.css';
import Login from './Login';
import { apiFetch, getSession, clearSession, setUnauthorizedHandler } from './api';
const MAPBOX_TOKEN = process.env.REACT_APP_MAPBOX_TOKEN;

// Helper function to highlight matching keywords in text
const HighlightedText = ({ text, keywords = [], maxLength = 200, theme = 'hacker' }) => {
  if (!text) return null;
  if (!keywords || keywords.length === 0) {
    return <span>{text.substring(0, maxLength)}{text.length > maxLength ? '...' : ''}</span>;
  }
  
  const truncatedText = text.substring(0, maxLength) + (text.length > maxLength ? '...' : '');
  const regex = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi');
  const parts = truncatedText.split(regex);
  
  return (
    <span>
      {parts.map((part, i) => 
        keywords.some(k => k.toLowerCase() === part.toLowerCase()) ? (
          <mark key={i} className={`highlight-match ${theme}`}>{part}</mark>
        ) : (
          <span key={i}>{part}</span>
        )
      )}
    </span>
  );
};

// Timeline Slider Component
const TimelineSlider = ({ cases, dateRange, setDateRange, theme }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  
  const dateBounds = useMemo(() => {
    if (cases.length === 0) return { min: '', max: '' };
    const dates = cases.map(c => new Date(c.timestamp).getTime()).filter(d => !isNaN(d));
    if (dates.length === 0) return { min: '', max: '' };
    return {
      min: new Date(Math.min(...dates)).toISOString().split('T')[0],
      max: new Date(Math.max(...dates)).toISOString().split('T')[0]
    };
  }, [cases]);
  
  useEffect(() => {
    if (!isPlaying || !dateBounds.min) return;
    
    const startDate = new Date(dateBounds.min);
    const endDate = new Date(dateBounds.max);
    const totalDays = (endDate - startDate) / (1000 * 60 * 60 * 24);
    const stepDays = Math.max(30, Math.floor(totalDays / 30));
    
    const interval = setInterval(() => {
      setDateRange(prev => {
        const currentEnd = prev.end ? new Date(prev.end) : startDate;
        const nextEnd = new Date(currentEnd.getTime() + stepDays * 24 * 60 * 60 * 1000);
        
        if (nextEnd >= endDate) {
          setIsPlaying(false);
          return { start: dateBounds.min, end: dateBounds.max };
        }
        
        return { start: dateBounds.min, end: nextEnd.toISOString().split('T')[0] };
      });
    }, 500);
    
    return () => clearInterval(interval);
  }, [isPlaying, dateBounds, setDateRange]);
  
  const handleSliderChange = (e) => {
    const value = parseInt(e.target.value);
    const startDate = new Date(dateBounds.min);
    const endDate = new Date(dateBounds.max);
    const totalDays = (endDate - startDate) / (1000 * 60 * 60 * 24);
    const selectedDate = new Date(startDate.getTime() + (value / 100) * totalDays * 24 * 60 * 60 * 1000);
    
    setDateRange({
      start: dateBounds.min,
      end: selectedDate.toISOString().split('T')[0]
    });
  };
  
  const getSliderValue = () => {
    if (!dateRange.end || !dateBounds.min || !dateBounds.max) return 100;
    const startDate = new Date(dateBounds.min);
    const endDate = new Date(dateBounds.max);
    const currentDate = new Date(dateRange.end);
    const totalDays = (endDate - startDate) / (1000 * 60 * 60 * 24);
    const currentDays = (currentDate - startDate) / (1000 * 60 * 60 * 24);
    return Math.min(100, Math.max(0, (currentDays / totalDays) * 100));
  };
  
  return (
    <div className={`timeline-slider ${theme}`}>
      <div className="timeline-header">
        <span className="timeline-label">{theme === 'hacker' ? '▶ TEMPORAL ANALYSIS' : 'Date Range Filter'}</span>
        <div className="timeline-controls">
          <button className={`timeline-btn ${theme}`} onClick={() => setDateRange({ start: '', end: '' })}>
            <SkipBack size={14} />
          </button>
          <button className={`timeline-btn play-btn ${theme}`} onClick={() => setIsPlaying(!isPlaying)}>
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
          </button>
          <button className={`timeline-btn ${theme}`} onClick={() => setDateRange({ start: dateBounds.min, end: dateBounds.max })}>
            <SkipForward size={14} />
          </button>
        </div>
      </div>
      
      <div className="timeline-track">
        <input
          type="range"
          min="0"
          max="100"
          value={getSliderValue()}
          onChange={handleSliderChange}
          className={`timeline-range ${theme}`}
        />
      </div>
      
      <div className="timeline-labels">
        <span>{dateBounds.min || '---'}</span>
        <span className="timeline-current">{dateRange.end || dateBounds.max || '---'}</span>
        <span>{dateBounds.max || '---'}</span>
      </div>
    </div>
  );
};

// AI Analysis Panel Component
const AIAnalysisPanel = ({ analysis, loading, theme, onClose }) => {
  if (loading) {
    return (
      <div className={`ai-analysis-panel ${theme}`}>
        <div className="ai-header">
          <Brain size={20} />
          <span>{theme === 'hacker' ? 'AI ANALYSIS IN PROGRESS...' : 'Generating Analysis...'}</span>
        </div>
        <div className="ai-loading">
          <div className={`spinner ${theme}`}></div>
        </div>
      </div>
    );
  }
  
  if (!analysis) return null;
  
  const sections = [
    { key: 'behavioral_patterns', title: theme === 'hacker' ? '▶ BEHAVIORAL PATTERNS' : 'Behavioral Patterns' },
    { key: 'victimology', title: theme === 'hacker' ? '▶ VICTIMOLOGY' : 'Victim Analysis' },
    { key: 'geographic_profile', title: theme === 'hacker' ? '▶ GEOGRAPHIC PROFILE' : 'Geographic Analysis' },
    { key: 'temporal_patterns', title: theme === 'hacker' ? '▶ TEMPORAL PATTERNS' : 'Temporal Analysis' },
    { key: 'overlooked_angles', title: theme === 'hacker' ? '▶ OVERLOOKED ANGLES' : 'Additional Investigative Avenues' },
    { key: 'linkage_assessment', title: theme === 'hacker' ? '▶ LINKAGE ASSESSMENT' : 'Case Linkage Assessment' },
    { key: 'recommended_actions', title: theme === 'hacker' ? '▶ RECOMMENDED ACTIONS' : 'Recommended Next Steps' }
  ];
  
  return (
    <div className={`ai-analysis-panel ${theme}`}>
      <div className="ai-header">
        <Brain size={20} />
        <span>{theme === 'hacker' ? 'GEMINI AI ANALYSIS' : 'AI-Assisted Analysis'}</span>
        <button className="ai-close" onClick={onClose}><X size={16} /></button>
      </div>
      <div className="ai-content">
        {sections.map(section => (
          analysis[section.key] && (
            <div key={section.key} className="ai-section">
              <h4>{section.title}</h4>
              <p>{analysis[section.key]}</p>
            </div>
          )
        ))}
      </div>
    </div>
  );
};

// Root: show the login screen until there is a valid session.
export default function App() {
  const [session, setSession] = useState(getSession);

  useEffect(() => {
    // Any 401 from the API (expired token, deactivated account) signs out.
    setUnauthorizedHandler(() => setSession(null));
  }, []);

  const handleLogout = () => {
    clearSession();
    setSession(null);
  };

  if (!session) return <Login onLogin={setSession} />;
  return <EchoCases user={session.user} onLogout={handleLogout} />;
}

// Main dashboard (only rendered for signed-in users)
function EchoCases({ user, onLogout }) {
  const isAdmin = user.role === 'admin';
  const [cases, setCases] = useState([]);
  const [filteredCases, setFilteredCases] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [similarCases, setSimilarCases] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [view, setView] = useState('map');
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [popupInfo, setPopupInfo] = useState(null);
  const [selectedCluster, setSelectedCluster] = useState(null);
  const [showClusterFootprints, setShowClusterFootprints] = useState(true);
  const [expandedClusters, setExpandedClusters] = useState({});
  
  // Theme toggle: 'hacker' or 'government'
  const [theme, setTheme] = useState('hacker');
  
  // AI Analysis state
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [showAiPanel, setShowAiPanel] = useState(false);
  
  // Map state - centered on North America
  const [viewState, setViewState] = useState({
    longitude: -98.5795,
    latitude: 39.8283,
    zoom: 4
  });
  
  // Filter states
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [categoryFilter, setCategoryFilter] = useState('all');
  
  const [terminalLines, setTerminalLines] = useState([
    '> ECHOCASES COLD CASE INTELLIGENCE v3.0',
    '> Initializing case linkage protocols...',
    '> Neural pattern recognition: ACTIVE',
    '> Gemini AI Integration: STANDBY',
    '> System status: OPERATIONAL'
  ]);

  useEffect(() => {
    loadCases();
    loadClusters();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [cases, dateRange, categoryFilter]);

  const loadCases = async () => {
    try {
      const response = await apiFetch('/cases');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setCases(data);
      setFilteredCases(data);
      addTerminalLine(`Loaded ${data.length} cold case records`);
      
      // Center map on data if available
      if (data.length > 0) {
        const lats = data.map(c => c.lat);
        const lons = data.map(c => c.lon);
        setViewState({
          longitude: (Math.min(...lons) + Math.max(...lons)) / 2,
          latitude: (Math.min(...lats) + Math.max(...lats)) / 2,
          zoom: 4
        });
      }
    } catch (error) {
      console.error('Error loading cases:', error);
      addTerminalLine('ERROR: Failed to retrieve case database');
    }
  };

  const loadClusters = async () => {
    try {
      const response = await apiFetch('/clusters');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setClusters(data);
      addTerminalLine(`Detected ${data.length} potential crime series`);
    } catch (error) {
      console.error('Error loading clusters:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...cases];
    
    if (dateRange.start) {
      filtered = filtered.filter(c => new Date(c.timestamp) >= new Date(dateRange.start));
    }
    if (dateRange.end) {
      filtered = filtered.filter(c => new Date(c.timestamp) <= new Date(dateRange.end));
    }
    
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(c => c.category === categoryFilter);
    }
    
    setFilteredCases(filtered);
  };

  const addTerminalLine = (line) => {
    setTerminalLines(prev => [...prev.slice(-5), `> ${line}`]);
  };

  const handleCaseClick = async (caseId) => {
    setLoading(true);
    setAiAnalysis(null);
    setShowAiPanel(false);
    
    const clickedCase = cases.find(c => c.case_id === caseId);
    setSelectedCase(clickedCase);
    setSelectedCluster(null);
    
    if (clickedCase) {
      setViewState({
        longitude: clickedCase.lon,
        latitude: clickedCase.lat,
        zoom: 8
      });
    }
    
    addTerminalLine(`Analyzing case ${caseId}...`);

    try {
      const response = await apiFetch(`/similar/${encodeURIComponent(caseId)}?top_k=10`);
      const data = await response.json();
      setSimilarCases(data.similar_cases || []);
      addTerminalLine(`Found ${data.similar_cases?.length || 0} potential matches`);
    } catch (error) {
      console.error('Error finding similar cases:', error);
      addTerminalLine('ERROR: Pattern matching failed');
    }
    setLoading(false);
  };

  // Generate local investigative analysis based on case data
  const generateLocalAnalysis = (caseData, relatedCases) => {
    const category = caseData.category?.toLowerCase() || 'unknown';
    const weapon = caseData.weapon || 'unknown';
    const entryMethod = caseData.entry_method || 'unknown';
    const narrative = caseData.narrative || '';
    const city = caseData.city || 'Unknown';
    const state = caseData.state || 'Unknown';
    const timestamp = caseData.timestamp ? new Date(caseData.timestamp) : null;
    
    // Extract key details from narrative
    const narrativeLower = narrative.toLowerCase();
    const hasWitness = narrativeLower.includes('witness') || narrativeLower.includes('seen') || narrativeLower.includes('observed');
    const hasVehicle = narrativeLower.includes('vehicle') || narrativeLower.includes('car') || narrativeLower.includes('truck');
    const hasForensic = narrativeLower.includes('dna') || narrativeLower.includes('fingerprint') || narrativeLower.includes('forensic');
    const isNighttime = narrativeLower.includes('night') || narrativeLower.includes('evening') || narrativeLower.includes('dark');
    const isResidential = narrativeLower.includes('home') || narrativeLower.includes('residence') || narrativeLower.includes('apartment');
    
    // Calculate patterns from similar cases
    const avgDistance = relatedCases.length > 0 
      ? (relatedCases.reduce((sum, c) => sum + (c.geo_distance_km || 0), 0) / relatedCases.length).toFixed(1)
      : 'N/A';
    const avgTimeDiff = relatedCases.length > 0
      ? Math.round(relatedCases.reduce((sum, c) => sum + (c.time_distance_days || 0), 0) / relatedCases.length)
      : 'N/A';
    const highMatchCount = relatedCases.filter(c => c.score > 0.7).length;
    
    // Day of week analysis
    const dayOfWeek = timestamp ? ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][timestamp.getDay()] : 'Unknown';
    const timeOfDay = timestamp ? (timestamp.getHours() < 12 ? 'morning' : timestamp.getHours() < 18 ? 'afternoon' : 'evening/night') : 'unknown time';
    
    return {
      behavioral_patterns: [
        `• Offense category "${category}" suggests ${category === 'homicide' ? 'high-risk, potentially planned behavior' : category === 'assault' ? 'impulsive or confrontational tendencies' : category === 'robbery' ? 'economically motivated offending' : 'specific behavioral patterns requiring further analysis'}`,
        weapon !== 'unknown' ? `• Weapon choice (${weapon}) indicates ${weapon.includes('gun') || weapon.includes('firearm') ? 'potential firearms access/familiarity' : weapon.includes('knife') ? 'close-contact comfort level' : 'opportunistic or planned weapon selection'}` : '• Weapon information unavailable - recommend reviewing evidence inventory',
        entryMethod !== 'unknown' ? `• Entry method "${entryMethod}" suggests ${entryMethod.includes('force') ? 'willingness to create noise/evidence' : 'possible familiarity with location or pre-planning'}` : null,
        isNighttime ? '• Nighttime occurrence suggests offender comfort operating in low-visibility conditions' : '• Daytime occurrence may indicate boldness or opportunistic timing',
        `• Occurred on ${dayOfWeek} ${timeOfDay} - cross-reference with similar cases for temporal patterns`
      ].filter(Boolean).join('\n'),
      
      victimology: [
        isResidential ? '• Residential location suggests victim may have been specifically targeted or location was pre-selected' : '• Non-residential location may indicate opportunistic encounter',
        hasWitness ? '• Witness presence noted - recommend re-interviewing for additional details' : '• No witnesses mentioned - consider canvassing for unreported observations',
        `• Location: ${city}, ${state} - analyze local crime patterns and demographic factors`,
        '• Recommend reviewing victim\'s routine, social connections, and recent activities',
        '• Cross-reference victim profile with similar cases for common vulnerability factors'
      ].join('\n'),
      
      geographic_profile: [
        `• Primary location: ${city}, ${state}`,
        relatedCases.length > 0 ? `• ${relatedCases.length} similar cases found with average distance of ${avgDistance} km` : '• Limited geographic data from similar cases',
        highMatchCount > 0 ? `• ${highMatchCount} high-confidence matches (>70%) suggest potential serial pattern` : '• No high-confidence pattern matches detected',
        hasVehicle ? '• Vehicle mentioned - offender may have transportation, expanding potential travel radius' : '• No vehicle mentioned - offender may be local to area',
        '• Recommend mapping similar cases to identify anchor points and travel corridors',
        '• Consider proximity to major highways, public transit, and commercial areas'
      ].join('\n'),
      
      temporal_patterns: [
        timestamp ? `• Incident date: ${timestamp.toLocaleDateString()} (${dayOfWeek})` : '• Date information unavailable',
        `• Time context: ${timeOfDay}`,
        relatedCases.length > 0 ? `• Average time between similar cases: ${avgTimeDiff} days` : '• Insufficient data for temporal pattern analysis',
        '• Recommend creating timeline of similar incidents to identify escalation patterns',
        '• Check for correlation with local events, paydays, or seasonal factors'
      ].join('\n'),
      
      overlooked_angles: [
        hasForensic ? '• Forensic evidence mentioned - ensure all samples have been processed with current technology' : '• Consider requesting forensic review with updated DNA/fingerprint databases',
        '• Review original case file for leads that weren\'t followed due to resource constraints',
        '• Check if any witnesses have since come forward or if alibis can now be verified',
        '• Cross-reference with newly solved cases for potential informant information',
        '• Consider geographic profiling software analysis if multiple linked cases exist',
        hasVehicle ? '• Vehicle mentioned - check for any unprocessed traffic camera or ALPR data' : '• Canvass for any historical surveillance footage that may exist'
      ].join('\n'),
      
      linkage_assessment: [
        relatedCases.length > 0 ? `• ${relatedCases.length} potentially linked cases identified by pattern analysis` : '• No strong case linkages detected',
        highMatchCount > 2 ? `• HIGH PRIORITY: ${highMatchCount} cases show >70% similarity - recommend formal linkage analysis` : null,
        relatedCases.length > 0 ? `• Common keywords with similar cases: ${relatedCases[0]?.explanation?.shared_keywords?.slice(0, 5).join(', ') || 'analysis pending'}` : null,
        '• Recommend ViCAP/regional database query for additional matches',
        '• Consider multi-jurisdictional task force if cases span multiple areas'
      ].filter(Boolean).join('\n'),
      
      recommended_actions: [
        '1. Re-interview any available witnesses with cognitive interview techniques',
        '2. Submit/resubmit forensic evidence to updated databases (CODIS, AFIS, NIBIN)',
        highMatchCount > 0 ? `3. Conduct formal linkage analysis with ${highMatchCount} high-match cases` : '3. Expand search parameters for additional case connections',
        '4. Review original suspect list against current criminal databases',
        '5. Consider media appeal for new information if case allows',
        hasVehicle ? '6. Query historical ALPR/traffic camera data for mentioned vehicle' : '6. Canvass for any available historical surveillance footage'
      ].join('\n')
    };
  };

  const requestAIAnalysis = async () => {
    if (!selectedCase) return;
    
    setAiLoading(true);
    setShowAiPanel(true);
    addTerminalLine(`Generating investigative analysis for ${selectedCase.case_id}...`);
    
    // Try backend first, fall back to local analysis
    try {
      const response = await apiFetch(`/analyze/${encodeURIComponent(selectedCase.case_id)}`);
      if (response.ok) {
        const data = await response.json();
        setAiAnalysis(data.ai_analysis);
        addTerminalLine(`AI analysis complete (${data.ai_provider})`);
      } else {
        throw new Error('Backend unavailable');
      }
    } catch (error) {
      // Generate local analysis when backend is unavailable
      console.log('Using local analysis generator');
      
      // Simulate brief processing time for UX
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const localAnalysis = generateLocalAnalysis(selectedCase, similarCases);
      setAiAnalysis(localAnalysis);
      addTerminalLine(`Analysis complete (Local Pattern Engine)`);
    }
    setAiLoading(false);
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    addTerminalLine(`Processing query: "${searchQuery}"`);
    
    try {
      const response = await apiFetch('/llm-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.results && data.results.length > 0) {
          setFilteredCases(data.results);
          addTerminalLine(`Query returned ${data.results.length} results`);
        }
      }
    } catch (error) {
      // Fallback to simple semantic search
      const fallbackResponse = await apiFetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery })
      });
      const fallbackData = await fallbackResponse.json();
      if (fallbackData.results) {
        setFilteredCases(fallbackData.results);
        addTerminalLine(`Semantic search: ${fallbackData.results.length} results`);
      }
    }
    setLoading(false);
  };

  const uploadDataset = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    setLoading(true);
    addTerminalLine(`Uploading dataset: ${file.name}`);
    
    try {
      const response = await apiFetch('/upload', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (!response.ok) {
        addTerminalLine(`ERROR: ${data.error || 'Upload failed'}`);
        setLoading(false);
        return;
      }
      addTerminalLine(`Processed ${data.num_cases} cases, ${data.num_clusters} series`);
      loadCases();
      loadClusters();
    } catch (error) {
      addTerminalLine('ERROR: Upload failed');
    }
    setLoading(false);
  };

  const resetFilters = () => {
    setDateRange({ start: '', end: '' });
    setCategoryFilter('all');
    setFilteredCases(cases);
    addTerminalLine('Filters reset');
  };

  const categories = ['all', ...new Set(cases.map(c => c.category).filter(Boolean))];

  // Generate cluster footprint GeoJSON
  const clusterFootprints = useMemo(() => {
    if (!showClusterFootprints || clusters.length === 0) return null;
    
    return {
      type: 'FeatureCollection',
      features: clusters.map(cluster => {
        const center = [cluster.center_lon, cluster.center_lat];
        const radiusKm = Math.max(50, cluster.geo_spread_km || 100);
        const points = 32;
        const coords = [];
        
        for (let i = 0; i <= points; i++) {
          const angle = (i / points) * 2 * Math.PI;
          const dx = radiusKm * Math.cos(angle) / 111.32;
          const dy = radiusKm * Math.sin(angle) / 110.574;
          coords.push([center[0] + dx, center[1] + dy]);
        }
        
        return {
          type: 'Feature',
          properties: { cluster_id: cluster.cluster_id, num_cases: cluster.num_cases },
          geometry: { type: 'Polygon', coordinates: [coords] }
        };
      })
    };
  }, [clusters, showClusterFootprints]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'hacker' ? 'government' : 'hacker');
  };

  return (
    <div className={`app ${theme}`}>
      {theme === 'hacker' && <div className="scanline"></div>}
      
      {/* Header */}
      <header className={`header ${theme}`}>
        <div className="header-content">
          <div className="header-top">
            <div className="logo-section">
              <Shield className={`shield-icon ${theme}`} size={36} />
              <div>
                <h1>{theme === 'hacker' ? 'ECHOCASES' : 'EchoCases'}</h1>
                <p className="subtitle">
                  {theme === 'hacker' 
                    ? '║ COLD CASE INTELLIGENCE SYSTEM ║ PATTERN RECOGNITION ACTIVE ║'
                    : 'Cold Case Analysis & Pattern Recognition System'}
                </p>
              </div>
            </div>
            
            <div className="header-right">
              <div className={`user-badge ${theme}`} title={`Signed in as ${user.username}`}>
                <User size={16} />
                <span>{user.username}</span>
                <span className={`role-tag ${user.role} ${theme}`}>
                  {theme === 'hacker' ? user.role.toUpperCase() : user.role}
                </span>
              </div>

              <button className={`theme-toggle ${theme}`} onClick={toggleTheme}>
                {theme === 'hacker' ? <ToggleLeft size={20} /> : <ToggleRight size={20} />}
                <span>{theme === 'hacker' ? 'TACTICAL' : 'Standard'}</span>
              </button>
              
              {isAdmin && (
                <label className={`upload-btn ${theme}`}>
                  {theme === 'hacker' ? '[UPLOAD DATA]' : 'Upload Dataset'}
                  <input
                    type="file"
                    accept=".csv"
                    style={{display: 'none'}}
                    onChange={(e) => e.target.files[0] && uploadDataset(e.target.files[0])}
                  />
                </label>
              )}

              <button className={`theme-toggle ${theme}`} onClick={onLogout}>
                <LogOut size={18} />
                <span>{theme === 'hacker' ? 'LOGOUT' : 'Sign out'}</span>
              </button>
            </div>
          </div>
          
          {theme === 'hacker' && (
            <div className="terminal">
              {terminalLines.map((line, i) => (
                <div key={i} className="terminal-line">{line}</div>
              ))}
            </div>
          )}

          <TimelineSlider cases={cases} dateRange={dateRange} setDateRange={setDateRange} theme={theme} />

          <div className={`filters-section ${theme}`}>
            <div className="filter-group">
              <Filter size={16} />
              <label>{theme === 'hacker' ? 'CATEGORY:' : 'Category:'}</label>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className={`filter-select ${theme}`}
              >
                {categories.map(cat => (
                  <option key={cat} value={cat}>{cat.toUpperCase()}</option>
                ))}
              </select>
            </div>
            
            <button onClick={resetFilters} className={`reset-btn ${theme}`}>
              {theme === 'hacker' ? '[RESET]' : 'Reset Filters'}
            </button>
            
            <div className="filter-results">
              {filteredCases.length} / {cases.length} {theme === 'hacker' ? 'CASES' : 'cases'}
            </div>
          </div>

          <div className={`search-container ${theme}`}>
            <div className="search-wrapper">
              <Search className="search-icon" size={20} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                placeholder={theme === 'hacker' 
                  ? "[QUERY] e.g., 'highway homicides in Texas'" 
                  : "Search cases... e.g., 'unsolved shootings 2020'"}
                className={`search-input ${theme}`}
              />
            </div>
            <button onClick={handleSearch} className={`execute-btn ${theme}`} disabled={loading}>
              {loading ? (theme === 'hacker' ? '[PROCESSING...]' : 'Searching...') : (theme === 'hacker' ? '[EXECUTE]' : 'Search')}
            </button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <nav className={`tabs ${theme}`}>
        <div className="tabs-container">
          {[
            { id: 'map', icon: MapIcon, label: theme === 'hacker' ? 'GEOGRAPHIC' : 'Map View' },
            { id: 'list', icon: Database, label: theme === 'hacker' ? 'CASE FILES' : 'Case List' },
            { id: 'clusters', icon: Activity, label: theme === 'hacker' ? 'SERIES ANALYSIS' : 'Crime Series' }
          ].map(v => (
            <button
              key={v.id}
              onClick={() => setView(v.id)}
              className={`tab ${theme} ${view === v.id ? 'active' : ''}`}
            >
              <v.icon size={18} />
              {theme === 'hacker' ? `[${v.label}]` : v.label}
            </button>
          ))}
          
          {view === 'map' && (
            <label className={`footprint-toggle ${theme}`}>
              <input
                type="checkbox"
                checked={showClusterFootprints}
                onChange={(e) => setShowClusterFootprints(e.target.checked)}
              />
              {theme === 'hacker' ? 'CLUSTER ZONES' : 'Show Series Areas'}
            </label>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main className={`main-content ${theme}`}>
        <div className="main-panel">
          {/* Map View */}
          {view === 'map' && (
            <div className={`panel ${theme}`}>
              <div className="map-container">
                {MAPBOX_TOKEN ? (
                  <Map
                    {...viewState}
                    onMove={evt => setViewState(evt.viewState)}
                    mapboxAccessToken={MAPBOX_TOKEN}
                    style={{width: '100%', height: 550}}
                    mapStyle={theme === 'hacker' 
                      ? "mapbox://styles/mapbox/dark-v11"
                      : "mapbox://styles/mapbox/light-v11"}
                  >
                    {clusterFootprints && (
                      <Source id="cluster-footprints" type="geojson" data={clusterFootprints}>
                        <Layer
                          id="cluster-fill"
                          type="fill"
                          paint={{
                            'fill-color': theme === 'hacker' ? '#0f0' : '#3b82f6',
                            'fill-opacity': 0.1
                          }}
                        />
                        <Layer
                          id="cluster-line"
                          type="line"
                          paint={{
                            'line-color': theme === 'hacker' ? '#0f0' : '#3b82f6',
                            'line-width': 2,
                            'line-dasharray': [2, 2]
                          }}
                        />
                      </Source>
                    )}
                    
                    {filteredCases.map(c => (
                      <Marker
                        key={c.case_id}
                        longitude={c.lon}
                        latitude={c.lat}
                        anchor="bottom"
                        onClick={e => {
                          e.originalEvent.stopPropagation();
                          setPopupInfo(c);
                        }}
                      >
                        <MapPin 
                          size={selectedCase?.case_id === c.case_id ? 36 : 24} 
                          color={selectedCase?.case_id === c.case_id 
                            ? '#f00' 
                            : (theme === 'hacker' ? '#0f0' : '#dc2626')}
                          fill={selectedCase?.case_id === c.case_id 
                            ? 'rgba(255,0,0,0.3)' 
                            : (theme === 'hacker' ? 'rgba(0,255,0,0.2)' : 'rgba(220,38,38,0.2)')}
                          style={{ cursor: 'pointer' }}
                        />
                      </Marker>
                    ))}

                    {popupInfo && (
                      <Popup
                        anchor="top"
                        longitude={popupInfo.lon}
                        latitude={popupInfo.lat}
                        onClose={() => setPopupInfo(null)}
                        closeButton={true}
                      >
                        <div className={`map-popup ${theme}`}>
                          <strong>{popupInfo.case_id}</strong><br />
                          <span className="popup-meta">
                            {popupInfo.city}, {popupInfo.state}<br />
                            {new Date(popupInfo.timestamp).toLocaleDateString()}<br />
                            {popupInfo.category?.toUpperCase()}
                          </span>
                          <p className="popup-narrative">{popupInfo.narrative?.substring(0, 100)}...</p>
                          <button onClick={() => handleCaseClick(popupInfo.case_id)} className={`popup-btn ${theme}`}>
                            {theme === 'hacker' ? '[ANALYZE]' : 'View Details'}
                          </button>
                        </div>
                      </Popup>
                    )}
                  </Map>
                ) : (
                  <div className={`map-placeholder ${theme}`}>
                    <MapPin size={64} />
                    <p>Mapbox token not configured</p>
                    <p className="small">Add REACT_APP_MAPBOX_TOKEN to .env</p>
                    <p>{filteredCases.length} cases loaded</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* List View */}
          {view === 'list' && (
            <div className={`panel ${theme}`}>
              <div className={`panel-header ${theme}`}>
                {theme === 'hacker' ? `║ CASE DATABASE ║ ${filteredCases.length} RECORDS ║` : `Case Database (${filteredCases.length} records)`}
              </div>
              <div className="case-list">
                {filteredCases.slice(0, 100).map(c => (
                  <div
                    key={c.case_id}
                    onClick={() => handleCaseClick(c.case_id)}
                    className={`case-item ${theme} ${selectedCase?.case_id === c.case_id ? 'selected' : ''}`}
                  >
                    <div className="case-content">
                      <div className="case-info">
                        <div className="case-id">{c.case_id}</div>
                        <div className="case-location">{c.city}, {c.state}</div>
                        <div className="case-narrative">{c.narrative?.substring(0, 150)}...</div>
                        <div className="case-meta">
                          <span><Clock size={12} /> {new Date(c.timestamp).toLocaleDateString()}</span>
                          <span>{c.category?.toUpperCase()}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Clusters View */}
          {view === 'clusters' && (
            <div className={`clusters-container ${theme}`}>
              <div className={`clusters-header ${theme}`}>
                {theme === 'hacker' ? `║ CRIME SERIES ║ ${clusters.length} PATTERNS ║` : `Detected Crime Series (${clusters.length})`}
              </div>
              {clusters.map(cluster => (
                <div key={cluster.cluster_id} className={`cluster-item ${theme}`}>
                  <div className="cluster-header" onClick={() => setExpandedClusters(prev => ({...prev, [cluster.cluster_id]: !prev[cluster.cluster_id]}))}>
                    <div className="cluster-info">
                      <h3>
                        {theme === 'hacker' ? `SERIES #${cluster.cluster_id.toString().padStart(3, '0')}` : `Series ${cluster.cluster_id}`}
                        {expandedClusters[cluster.cluster_id] ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </h3>
                      <p className="cluster-mo">{cluster.common_mo}</p>
                      <div className="cluster-stats">
                        <span>{cluster.num_cases} cases</span>
                        <span>~{cluster.geo_spread_km?.toFixed(0)} km spread</span>
                      </div>
                    </div>
                    <span className={`series-badge ${theme}`}>
                      {theme === 'hacker' ? '[SERIES]' : 'Linked'}
                    </span>
                  </div>
                  
                  {expandedClusters[cluster.cluster_id] && (
                    <div className="cluster-expanded">
                      <div className="cluster-keywords">
                        {cluster.common_keywords?.map((kw, i) => (
                          <span key={i} className={`keyword-tag ${theme}`}>{kw}</span>
                        ))}
                      </div>
                      <button 
                        className={`view-all-btn ${theme}`}
                        onClick={() => {
                          setViewState({ longitude: cluster.center_lon, latitude: cluster.center_lat, zoom: 6 });
                          setView('map');
                        }}
                      >
                        {theme === 'hacker' ? '[VIEW ON MAP]' : 'View on Map'}
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel - Case Details */}
        <aside className={`panel right-panel ${theme}`}>
          {selectedCase ? (
            <>
              <div className={`selected-case-header ${theme}`}>
                <h2>{theme === 'hacker' ? 'ACTIVE CASE' : 'Case Details'}</h2>
                <p className="selected-case-id">{selectedCase.case_id}</p>
              </div>
              
              <div className="selected-case-details">
                <div className="case-location-detail">
                  <MapPin size={14} /> {selectedCase.city}, {selectedCase.state}
                </div>
                <p className="selected-narrative">
                  <HighlightedText 
                    text={selectedCase.narrative || ''} 
                    keywords={similarCases[0]?.explanation?.shared_keywords || []}
                    maxLength={400}
                    theme={theme}
                  />
                </p>
                <div className={`selected-meta ${theme}`}>
                  <div><strong>Date:</strong> {new Date(selectedCase.timestamp).toLocaleString()}</div>
                  <div><strong>Category:</strong> {selectedCase.category?.toUpperCase()}</div>
                  {selectedCase.weapon && <div><strong>Weapon:</strong> {selectedCase.weapon}</div>}
                  {selectedCase.entry_method && <div><strong>Entry:</strong> {selectedCase.entry_method}</div>}
                </div>
                
                {/* AI Analysis Button */}
                <button 
                  className={`ai-analyze-btn ${theme}`}
                  onClick={requestAIAnalysis}
                  disabled={aiLoading}
                >
                  <Brain size={18} />
                  {aiLoading 
                    ? (theme === 'hacker' ? 'ANALYZING...' : 'Analyzing...') 
                    : (theme === 'hacker' ? '[AI ANALYSIS]' : 'Get AI Analysis')}
                </button>
              </div>

              {/* AI Analysis Panel */}
              {showAiPanel && (
                <AIAnalysisPanel 
                  analysis={aiAnalysis} 
                  loading={aiLoading} 
                  theme={theme}
                  onClose={() => setShowAiPanel(false)}
                />
              )}

              {/* Similar Cases */}
              <div className={`matches-section ${theme}`}>
                <h3 className="matches-title">
                  <AlertCircle size={18} />
                  {theme === 'hacker' ? 'PATTERN MATCHES' : 'Similar Cases'}
                </h3>
                
                {loading ? (
                  <div className="loading-container">
                    <div className={`spinner ${theme}`}></div>
                  </div>
                ) : (
                  <div className="matches-list">
                    {similarCases.slice(0, 5).map((similar, idx) => (
                      <div 
                        key={idx} 
                        className={`match-item ${theme} priority-${similar.score > 0.7 ? 'high' : similar.score > 0.5 ? 'medium' : 'low'}`}
                        onClick={() => handleCaseClick(similar.case_id)}
                      >
                        <div className="match-header">
                          <span className="match-id">{similar.case_id}</span>
                          <div className="match-score">
                            <span className="score-value">{(similar.score * 100).toFixed(0)}%</span>
                          </div>
                        </div>
                        
                        <p className="match-narrative">
                          <HighlightedText 
                            text={similar.narrative || ''} 
                            keywords={similar.explanation?.shared_keywords || []}
                            maxLength={100}
                            theme={theme}
                          />
                        </p>
                        
                        <div className="match-stats">
                          <span>{similar.geo_distance_km?.toFixed(0)} km</span>
                          <span>{similar.time_distance_days?.toFixed(0)} days</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className={`empty-state ${theme}`}>
              <AlertCircle size={48} />
              <p>{theme === 'hacker' ? 'NO CASE SELECTED' : 'No Case Selected'}</p>
              <p className="small">{theme === 'hacker' ? 'SELECT A CASE TO ANALYZE' : 'Click a case to view details'}</p>
            </div>
          )}
        </aside>
      </main>

      {/* Footer Warning */}
      <footer className={`warning-container ${theme}`}>
        <div className={`warning-box ${theme}`}>
          <AlertCircle size={20} />
          <div className="warning-text">
            <strong>{theme === 'hacker' ? 'CLASSIFICATION: INVESTIGATIVE ASSISTANCE ONLY' : 'Important Notice'}</strong><br />
            This system identifies potential connections between cases, NOT individuals. 
            All matches require human verification. AI analysis is suggestive only.
          </div>
        </div>
      </footer>
    </div>
  );
}
