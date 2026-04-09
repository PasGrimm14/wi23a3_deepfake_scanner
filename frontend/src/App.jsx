import React, { useState, useEffect, useRef } from 'react';

// --- Icons (using inline SVG for simplicity in single file) ---
const IconShield = () => <svg className="w-8 h-8 text-sky-500 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>;
const IconMenu = () => <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16"/></svg>;
const IconScanner = () => <svg className="w-4 h-4 mr-1 text-sky-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>;
const IconCheck = () => <svg className="w-6 h-6 text-emerald-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>;

export default function App() {
  const [currentView, setCurrentView] = useState('home');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [data, setData] = useState({ quiz: [], scenarios: [] });
  
  // State for Quiz
  const [quizScore, setQuizScore] = useState(0);
  const [quizAnswered, setQuizAnswered] = useState({});

  // State for Scenarios
  const [scenarioAnswered, setScenarioAnswered] = useState({});

  // State for Scanner
  const [scanState, setScanState] = useState('idle'); 
  const [scanResult, setScanResult] = useState(null);
  const fileInputRef = useRef(null);

  // Load Data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/content');
        if (response.ok) {
          const json = await response.json();
          setData(json);
        }
      } catch (e) { console.error("Data fetch failed", e); }
    };
    fetchData();
  }, []);

  const handleNavClick = (view) => {
    setCurrentView(view);
    setMobileMenuOpen(false);
    window.scrollTo(0, 0);
  };

  const NavButton = ({ target, label, icon }) => {
    const active = currentView === target;
    return (
      <button
        onClick={() => handleNavClick(target)}
        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center ${active ? 'bg-slate-800 text-sky-400' : 'text-slate-300 hover:bg-slate-700 hover:text-white'}`}
      >
        {icon}
        {label}
      </button>
    );
  };

  // --- View Components ---

  const HomeView = () => (
    <div className="fade-in text-center py-16">
      <h1 className="text-5xl font-extrabold tracking-tight text-white sm:text-6xl mb-6">
        Seeing / Hearing <br /><span className="text-sky-500">is not believing.</span>
      </h1>
      <p className="mt-4 max-w-2xl text-xl text-slate-400 mx-auto">
        Künstliche Intelligenz macht es Cyberkriminellen heute leichter denn je. Willkommen im Awareness-Portal.
      </p>
      <div className="mt-10 flex flex-col sm:flex-row justify-center gap-4">
        <button onClick={() => handleNavClick('info')} className="px-8 py-3 rounded-md text-white bg-sky-600 hover:bg-sky-700 font-medium">Gefahren verstehen</button>
        <button onClick={() => handleNavClick('scanner')} className="px-8 py-3 rounded-md text-sky-400 bg-slate-800 hover:bg-slate-700 border border-slate-700 font-medium flex items-center justify-center">
          <IconScanner /> X2-DFD Scanner
        </button>
      </div>
    </div>
  );

  const InfoView = () => (
    <div className="fade-in">
      <h2 className="text-3xl font-bold text-white mb-8 border-b border-slate-700 pb-4">Bedrohungen & Szenarien</h2>
      <div className="prose prose-invert max-w-none text-slate-300 mb-8">
          <p className="text-lg leading-relaxed">
              Deepfakes sind durch maschinelles Lernen manipulierte Medien, die täuschend echt wirken. Angreifer nutzen KI, um Vertrauen zu erschleichen.
          </p>
      </div>
    </div>
  );

  const ProtectionView = () => (
    <div className="fade-in">
      <h2 className="text-3xl font-bold text-white mb-8 border-b border-slate-700 pb-4">Schutzmaßnahmen</h2>
      <div className="bg-sky-900/30 border border-sky-500/50 p-6 rounded-xl mb-8">
        <h3 className="text-2xl font-bold text-white mb-6">Die 5-Punkte-Checkliste zur Verifikation</h3>
        <ul className="space-y-4 text-slate-300">
            <li>1. Druck und Dringlichkeit erkennen</li>
            <li>2. Zweitkanal-Verifikation (Out-of-Band)</li>
            <li>3. Codewörter nutzen</li>
            <li>4. Prozesse einhalten (Zero Trust)</li>
            <li>5. Verdachtsmomente melden</li>
        </ul>
      </div>
    </div>
  );

  const QuizView = () => {
    const handleAnswer = (qId, isRealGuess, isActuallyReal, explanation) => {
      if (quizAnswered[qId]) return;
      const correct = isRealGuess === isActuallyReal;
      if (correct) setQuizScore(prev => prev + 1);
      setQuizAnswered(prev => ({ ...prev, [qId]: { correct, explanation } }));
    };

    return (
      <div className="fade-in">
        <div className="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
          <h2 className="text-3xl font-bold text-white">Quiz: Echt oder Fake?</h2>
          <div className="text-sky-400 font-bold bg-sky-900/40 px-4 py-2 rounded-lg">Score: {quizScore} / {data.quiz.length}</div>
        </div>
        <div className="space-y-6">
          {data.quiz.map((q, i) => (
            <div key={q.id} className="bg-slate-800 p-6 rounded-xl border border-slate-700">
              <h3 className="text-xl font-bold text-white mb-2">Fall {i + 1}: {q.title}</h3>
              <p className="text-slate-300 mb-4">{q.description}</p>
              {!quizAnswered[q.id] ? (
                <div className="flex gap-4">
                  <button onClick={() => handleAnswer(q.id, true, q.isReal, q.explanation)} className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded">Echt</button>
                  <button onClick={() => handleAnswer(q.id, false, q.isReal, q.explanation)} className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded">Fake</button>
                </div>
              ) : (
                <div className={`p-4 rounded border ${quizAnswered[q.id].correct ? 'bg-emerald-900/30 border-emerald-500' : 'bg-rose-900/30 border-rose-500'}`}>
                  <p className="text-sm">{quizAnswered[q.id].explanation}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const ScenariosView = () => (
    <div className="fade-in">
      <h2 className="text-3xl font-bold text-white mb-8 border-b border-slate-700 pb-4">Interaktive Szenarien</h2>
      <div className="space-y-8">
        {data.scenarios.map((s, i) => (
          <div key={s.id} className="bg-slate-900 p-6 rounded-xl border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4">Szenario {i+1}</h3>
            <p className="text-slate-300 mb-6 bg-slate-800 p-4 rounded">{s.context}</p>
            <div className="space-y-3">
              {s.options.map((opt, idx) => (
                <button key={idx} onClick={() => setScenarioAnswered({...scenarioAnswered, [s.id]: idx})} className={`w-full text-left p-4 rounded border ${scenarioAnswered[s.id] === idx ? 'border-sky-500 bg-slate-700' : 'border-slate-600 bg-slate-800'}`}>
                  {opt.text}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const ScannerView = () => {
    const handleFileSelect = async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      setScanState('scanning');
      const formData = new FormData();
      formData.append("file", file);
      try {
        const response = await fetch('/api/scan', { method: 'POST', body: formData });
        const result = await response.json();
        setScanResult(result);
        setScanState('result');
      } catch (error) { setScanState('idle'); }
    };

    return (
      <div className="fade-in">
        <div className="flex items-center gap-3 border-b border-slate-700 pb-4 mb-8">
            <IconScanner />
            <h2 className="text-3xl font-bold text-white">X2-DFD KI-Scanner</h2>
        </div>

        {scanState === 'idle' && (
          <div onClick={() => fileInputRef.current.click()} className="border-2 border-dashed border-slate-600 hover:border-sky-500 bg-slate-800/50 rounded-xl p-16 text-center cursor-pointer transition-colors">
            <input type="file" ref={fileInputRef} className="hidden" accept="image/*" onChange={handleFileSelect} />
            <span className="text-white font-semibold block text-lg">Klicken zum Auswählen eines Bildes</span>
          </div>
        )}

        {scanState === 'scanning' && (
          <div className="border border-sky-500 bg-slate-800/50 rounded-xl p-16 text-center">
             <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-sky-500 border-t-transparent mb-4"></div>
             <p className="text-sky-400 font-bold text-lg">X2-DFD Framework Analyse läuft...</p>
          </div>
        )}

        {scanState === 'result' && scanResult && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center">
              <div>
                <h3 className="text-xl font-bold text-white">X2-DFD Analysebericht</h3>
                <span className="text-xs text-sky-400 font-mono">Multimodal Reasoning</span>
              </div>
              <span className={`px-3 py-1 rounded text-sm font-bold uppercase ${scanResult.is_fake ? 'bg-rose-500' : 'bg-emerald-500'}`}>
                {scanResult.is_fake ? 'Deepfake Verdacht' : 'Wahrscheinlich Echt'}
              </span>
            </div>
            
            <div className="p-6">
                <div className="mb-8">
                    <div className="flex justify-between text-sm mb-2">
                        <span className="text-slate-300">KI-Wahrscheinlichkeit</span>
                        <span className="font-bold">{scanResult.probability}%</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-3">
                        <div className={`h-3 rounded-full transition-all duration-1000 ${scanResult.is_fake ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${scanResult.probability}%` }}></div>
                    </div>
                </div>

                {/* X2-DFD Feature Grid */}
                {scanResult.features && (
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
                    {Object.entries(scanResult.features).map(([key, val]) => (
                      <div key={key} className="bg-slate-900/50 p-3 rounded border border-slate-700">
                        <span className="text-[10px] uppercase text-slate-500 font-bold block mb-1">{key.replace('_', ' ')}</span>
                        <p className="text-sm text-slate-200">{val}</p>
                      </div>
                    ))}
                  </div>
                )}

                <div className="bg-slate-900 p-5 rounded-lg border border-slate-700">
                    <h4 className="text-white font-bold mb-2">Erklärbarkeit (Reasoning):</h4>
                    <p className="text-slate-300 italic mb-4 text-sm bg-slate-800 p-3 rounded border-l-2 border-sky-500">{scanResult.reasoning}</p>
                    <ul className="list-disc list-inside text-slate-300 text-sm space-y-1">
                        {scanResult.artifacts.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </div>
                <button onClick={() => setScanState('idle')} className="mt-8 w-full py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg">Neu scannen</button>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 flex flex-col font-sans">
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 flex justify-between h-16">
          <div className="flex items-center cursor-pointer" onClick={() => handleNavClick('home')}>
            <IconShield /><span className="font-bold text-xl text-white">SecAware</span>
          </div>
          <div className="hidden md:flex items-center space-x-1">
            <NavButton target="home" label="Start" />
            <NavButton target="info" label="Bedrohungen" />
            <NavButton target="protection" label="Schutz" />
            <NavButton target="quiz" label="Quiz" />
            <NavButton target="scenarios" label="Szenarien" />
            <NavButton target="scanner" label="X2-DFD Scanner" icon={<IconScanner/>} />
          </div>
        </div>
      </nav>

      <main className="flex-grow max-w-4xl w-full mx-auto px-4 py-10">
        {currentView === 'home' && <HomeView />}
        {currentView === 'info' && <InfoView />}
        {currentView === 'protection' && <ProtectionView />}
        {currentView === 'quiz' && <QuizView />}
        {currentView === 'scenarios' && <ScenariosView />}
        {currentView === 'scanner' && <ScannerView />}
      </main>

      <footer className="bg-slate-900 border-t border-slate-800 py-8 text-center text-slate-500 text-sm">
        <p>Ein Universitätsprojekt zur Cybersecurity-Awareness.</p>
        <p className="mt-2">Deployed on <a href="https://www.pasgri-cloud.de" className="text-sky-400 hover:underline">pasgri-cloud.de</a></p>
      </footer>
    </div>
  );
}