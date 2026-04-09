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
  const [quizAnswered, setQuizAnswered] = useState({}); // { id: { isCorrect, guess, explanation } }

  // State for Scenarios
  const [scenarioAnswered, setScenarioAnswered] = useState({}); // { id: selectedOptionIndex }

  // State for Scanner
  const [scanState, setScanState] = useState('idle'); // 'idle', 'scanning', 'result'
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
        } else {
          useFallbackData();
        }
      } catch (e) {
        useFallbackData();
      }
    };

    const useFallbackData = () => {
      setData({
        quiz: [
          { id: "q1", title: "Sprachnachricht vom CEO", type: "Audio", description: "WhatsApp-Audio: 'Brauche sofort eine Überweisung von 50k. Nicht anrufen.'", isReal: false, explanation: "Fake. Typischer CEO-Fraud via Voice-Cloning. Kontext: Geldforderung, Dringlichkeit." },
          { id: "q2", title: "Internes Newsletter-Video", type: "Video", description: "Das monatliche Update-Video der HR-Abteilung im Intranet. Die Bildqualität schwankt leicht.", isReal: true, explanation: "Echt. Schwankende Bildqualität ist normal. Keine Aufforderung zu kritischen Handlungen." },
          { id: "q3", title: "Teams-Call vom IT-Support", type: "Video/Audio", description: "Video-Anruf auf Teams. Bild friert sofort ein. Stimme fordert 6-stelligen MFA-Code.", isReal: false, explanation: "Fake/Scam. Eingefrorenes Bild verbirgt oft visuelle Fehler. IT fragt NIE nach MFA-Codes." }
        ],
        scenarios: [
          { id: "s1", context: "CFO ruft an: 'Hochgeheime Akquisition, sofort 150.000 EUR überweisen.'", options: [ { text: "Ich rufe Sie auf der internen Nummer zurück.", risk: "low", feedback: "Best Practice! Verifizierter Out-of-Band-Kanal." }, { text: "Ich fordere eine E-Mail Bestätigung an.", risk: "medium", feedback: "Besser, aber Mailboxen können auch kompromittiert sein." }, { text: "Ich überweise sofort.", risk: "high", feedback: "Kritisches Risiko! CEO-Fraud." } ] },
          { id: "s2", context: "Ein neuer Mitarbeiter im IT-Support bittet per Video-Call um administrative Rechte. Das Video wirkt beim Blinzeln leicht unscharf.", options: [ { text: "Ich gewähre die Rechte, er sieht aus wie auf dem Foto.", risk: "high", feedback: "Hohes Risiko. Visuelle Artefakte deuten auf Live-Deepfakes hin." }, { text: "Ich bitte ihn, eine Hand vor das Gesicht zu halten.", risk: "medium", feedback: "Guter Ansatz. Deepfakes haben oft Probleme mit Verdeckungen." }, { text: "Ich fordere ihn auf, den formellen Request-Prozess im Ticket-System zu nutzen.", risk: "low", feedback: "Best Practice! Ein strikter technischer Autorisierungsprozess schlägt jeden Deepfake." } ] }
        ]
      });
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

  // --- Views ---

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
          <IconScanner /> KI-Scanner
        </button>
      </div>

      <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-left">
          <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
              <div className="w-12 h-12 bg-sky-500/20 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Voice Cloning</h3>
              <p className="text-slate-400">Wenige Sekunden einer Audioaufnahme genügen, um die Stimme eines Vorgesetzten perfekt zu klonen.</p>
          </div>
          <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
              <div className="w-12 h-12 bg-sky-500/20 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Deepfake Video</h3>
              <p className="text-slate-400">Manipulierte Videoanrufe können visuell und akustisch eine völlig falsche Identität vortäuschen.</p>
          </div>
          <div className="bg-slate-800/50 p-6 rounded-xl border border-slate-700">
              <div className="w-12 h-12 bg-sky-500/20 rounded-lg flex items-center justify-center mb-4">
                  <svg className="w-6 h-6 text-sky-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
              </div>
              <h3 className="text-xl font-bold text-white mb-2">Social Engineering</h3>
              <p className="text-slate-400">Technik ist nur das Mittel zum Zweck. Das Ziel ist es, Sie unter Druck zu Fehlentscheidungen zu drängen.</p>
          </div>
      </div>
    </div>
  );

  const InfoView = () => (
    <div className="fade-in">
      <h2 className="text-3xl font-bold text-white mb-8 border-b border-slate-700 pb-4">Bedrohungen & Szenarien</h2>
      <div className="prose prose-invert max-w-none text-slate-300 mb-8">
          <p className="text-lg leading-relaxed">
              Deepfakes sind durch maschinelles Lernen manipulierte Medien (Audio, Bild oder Video), die täuschend echt wirken. In der Cybersecurity verschmilzt diese Technologie zunehmend mit traditionellem <strong>Social Engineering</strong>. Angreifer nutzen KI nicht als Selbstzweck, sondern um Vertrauen zu erschleichen und Sicherheitsbarrieren im menschlichen Verstand zu umgehen.
          </p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800 p-6 rounded-lg border-l-4 border-rose-500">
          <h4 className="text-xl font-bold text-white mb-2">Der CEO-Fraud (Fake President)</h4>
          <p className="text-sm text-slate-400 mb-3">Zielgruppe: Finance, HR, Management</p>
          <p className="text-slate-300">Ein Angreifer ruft als Geschäftsführer an. Die Stimme wurde geklont. Unter dem Vorwand einer geheimen Firmenübernahme wird eine dringende Überweisung gefordert.</p>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border-l-4 border-orange-500">
          <h4 className="text-xl font-bold text-white mb-2">Der IT-Support-Scam</h4>
          <p className="text-sm text-slate-400 mb-3">Zielgruppe: Alle Mitarbeitenden</p>
          <p className="text-slate-300">Ein "Kollege" aus der IT ruft per Teams an und fordert wegen eines "Sicherheitsvorfalls" die sofortige Freigabe eines MFA-Tokens oder Passworts.</p>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border-l-4 border-yellow-500">
          <h4 className="text-xl font-bold text-white mb-2">Familien-Notfall</h4>
          <p className="text-sm text-slate-400 mb-3">Zielgruppe: Privatpersonen</p>
          <p className="text-slate-300">Ein Anruf von einem Familienmitglied. Die geklonte Stimme weint oder klingt panisch: "Ich hatte einen Unfall, ich brauche dringend Geld."</p>
        </div>
        <div className="bg-slate-800 p-6 rounded-lg border-l-4 border-blue-500">
          <h4 className="text-xl font-bold text-white mb-2">Fake-Job-Interviews</h4>
          <p className="text-sm text-slate-400 mb-3">Zielgruppe: HR, Externe</p>
          <p className="text-slate-300">Angreifer nutzen Live-Deepfakes, um sich bei Remote-Interviews als Experten auszugeben, um Zugang zum Firmennetzwerk zu erhalten.</p>
        </div>
      </div>
    </div>
  );

  const ProtectionView = () => (
    <div className="fade-in">
      <h2 className="text-3xl font-bold text-white mb-8 border-b border-slate-700 pb-4">Schutzmaßnahmen</h2>
      
      <div className="bg-sky-900/30 border border-sky-500/50 p-6 rounded-xl mb-8">
        <h3 className="text-2xl font-bold text-white mb-6">Die 5-Punkte-Checkliste zur Verifikation</h3>
        <ul className="space-y-6">
          <li className="flex items-start">
            <span className="flex-shrink-0 h-8 w-8 rounded-full bg-sky-500 flex items-center justify-center text-white font-bold mr-4 mt-1">1</span>
            <div>
              <strong className="text-white text-lg block">Druck und Dringlichkeit erkennen</strong>
              <p className="text-slate-400 mt-1">Social Engineering funktioniert fast immer über Zeitdruck oder Autorität. Seien Sie extrem misstrauisch, wenn etwas "sofort und streng geheim" passieren muss.</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 h-8 w-8 rounded-full bg-sky-500 flex items-center justify-center text-white font-bold mr-4 mt-1">2</span>
            <div>
              <strong className="text-white text-lg block">Zweitkanal-Verifikation (Out-of-Band)</strong>
              <p className="text-slate-400 mt-1">Wenn Sie einen Anruf mit einer kritischen Forderung erhalten: Legen Sie auf. Rufen Sie die Person über eine Ihnen bekannte, interne Nummer zurück.</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 h-8 w-8 rounded-full bg-sky-500 flex items-center justify-center text-white font-bold mr-4 mt-1">3</span>
            <div>
              <strong className="text-white text-lg block">Codewörter nutzen</strong>
              <p className="text-slate-400 mt-1">Vereinbaren Sie innerhalb von Abteilungen ein Codewort. Wenn der "CEO" anruft, fragen Sie nach dem Codewort.</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 h-8 w-8 rounded-full bg-sky-500 flex items-center justify-center text-white font-bold mr-4 mt-1">4</span>
            <div>
              <strong className="text-white text-lg block">Prozesse einhalten (Zero Trust)</strong>
              <p className="text-slate-400 mt-1">Keine Ausnahme für den Chef. Prozesse dürfen nicht durch einen bloßen Zuruf am Telefon umgangen werden.</p>
            </div>
          </li>
          <li className="flex items-start">
            <span className="flex-shrink-0 h-8 w-8 rounded-full bg-sky-500 flex items-center justify-center text-white font-bold mr-4 mt-1">5</span>
            <div>
              <strong className="text-white text-lg block">Verdachtsmomente melden</strong>
              <p className="text-slate-400 mt-1">Melden Sie verdächtige Anrufe sofort dem IT-Security-Team. Ein Angreifer, der bei Ihnen scheitert, ruft sonst direkt den Kollegen an.</p>
            </div>
          </li>
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
        <p className="text-slate-300 mb-8">Bewerten Sie die folgenden Beispiele. Trainieren Sie Ihr Auge und Ohr auf untypische Merkmale, aber denken Sie daran: Perfekte Deepfakes sind technisch nicht mehr von echten Medien zu unterscheiden.</p>
        
        <div className="space-y-6">
          {data.quiz.map((q, i) => {
            const answered = quizAnswered[q.id];
            return (
              <div key={q.id} className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                <div className="flex justify-between items-start mb-4">
                    <h3 className="text-xl font-bold text-white">Fall {i + 1}: {q.title}</h3>
                    <span className="bg-slate-700 text-slate-300 text-xs px-2 py-1 rounded uppercase tracking-wider">{q.type}</span>
                </div>
                <p className="text-slate-300 mb-6">{q.description}</p>
                <div className={`flex gap-4 mb-4 ${answered ? 'opacity-50 pointer-events-none' : ''}`}>
                  <button onClick={() => handleAnswer(q.id, true, q.isReal, q.explanation)} className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 font-medium text-white rounded transition-colors">Echt</button>
                  <button onClick={() => handleAnswer(q.id, false, q.isReal, q.explanation)} className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 font-medium text-white rounded transition-colors">Fake</button>
                </div>
                {answered && (
                  <div className={`p-4 rounded-lg border mt-4 ${answered.correct ? 'bg-emerald-900/30 border-emerald-500/50 text-emerald-200' : 'bg-rose-900/30 border-rose-500/50 text-rose-200'}`}>
                    <strong className="block text-lg mb-1">{answered.correct ? 'Korrekt analysiert!' : 'Falsche Einschätzung.'}</strong> 
                    <p className="text-sm">{answered.explanation}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const ScenariosView = () => {
    const handleOptionSelect = (sId, index) => {
      if (scenarioAnswered[sId] !== undefined) return;
      setScenarioAnswered(prev => ({ ...prev, [sId]: index }));
    };

    return (
      <div className="fade-in">
        <h2 className="text-3xl font-bold text-white mb-8 border-b border-slate-700 pb-4">Interaktive Szenarien</h2>
        <p className="text-slate-300 mb-8">Wie reagieren Sie im Arbeitsalltag unter Druck? Wählen Sie die sicherste Handlungsoption.</p>
        
        <div className="space-y-8">
          {data.scenarios.map((s, i) => {
            const selectedIdx = scenarioAnswered[s.id];
            return (
              <div key={s.id} className="bg-slate-900 p-6 rounded-xl border border-slate-700 shadow-lg">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-8 h-8 rounded bg-sky-900 flex items-center justify-center text-sky-400 font-bold">{i + 1}</div>
                    <h3 className="text-xl font-bold text-white">Szenario</h3>
                </div>
                <p className="text-slate-300 mb-6 bg-slate-800 p-4 rounded border-l-4 border-sky-500">{s.context}</p>
                
                <div className="space-y-3">
                  {s.options.map((opt, optIdx) => (
                    <button
                      key={optIdx}
                      onClick={() => handleOptionSelect(s.id, optIdx)}
                      className={`w-full text-left p-4 rounded border transition-colors
                        ${selectedIdx === undefined ? 'bg-slate-800 hover:bg-slate-700 border-slate-600 text-slate-200' : 
                          selectedIdx === optIdx ? 'bg-slate-700 border-sky-500 ring-2 ring-sky-500 text-white' : 'bg-slate-800/50 border-slate-700 text-slate-500 opacity-50 pointer-events-none'}`}
                    >
                      {opt.text}
                    </button>
                  ))}
                </div>
                {selectedIdx !== undefined && (
                  <div className={`mt-6 p-4 rounded-lg border ${s.options[selectedIdx].risk === 'high' ? 'bg-rose-900/20 border-rose-500/50 text-rose-300' : s.options[selectedIdx].risk === 'medium' ? 'bg-yellow-900/20 border-yellow-500/50 text-yellow-300' : 'bg-emerald-900/20 border-emerald-500/50 text-emerald-300'}`}>
                    <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 text-xs font-bold rounded uppercase text-white ${s.options[selectedIdx].risk === 'high' ? 'bg-rose-500' : s.options[selectedIdx].risk === 'medium' ? 'bg-yellow-500 text-black' : 'bg-emerald-500'}`}>
                            {s.options[selectedIdx].risk === 'high' ? 'Hohes Risiko' : s.options[selectedIdx].risk === 'medium' ? 'Mittleres Risiko' : 'Best Practice'}
                        </span>
                        <strong className="text-white">Auswertung</strong>
                    </div>
                    <p className="text-sm">{s.options[selectedIdx].feedback}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const ScannerView = () => {
    const handleFileSelect = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      setScanState('scanning');
      setScanResult(null);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const response = await fetch('/api/scan', { method: 'POST', body: formData });
        if (response.ok) {
          const result = await response.json();
          setScanResult(result);
          setScanState('result');
        } else {
          throw new Error("API Error");
        }
      } catch (error) {
        // Fallback Simulation for local testing without backend
        setTimeout(() => {
          const isFake = Math.random() > 0.5;
          const isAudio = file.name.match(/\.(mp3|wav|m4a|ogg)$/i);
          
          let artifacts = [];
          let reasoning = "";

          if(isFake) {
              if(isAudio) {
                  artifacts = ["Unnatürliche Frequenzspitzen im Audio-Spektrum erkannt.", "Synthetische Überbetonung von Zischlauten."];
                  reasoning = "Klare Muster synthetischer Sprachgenerierung.";
              } else {
                  artifacts = ["Asymmetrische Lichtreflexionen in den Pupillen.", "Lokale Pixel-Glättung und fehlende Mikroporen."];
                  reasoning = "Visuelle Inkonsistenzen und physikalische Fehler erkannt.";
              }
          } else {
              artifacts = ["Natürliche Strukturen", "Konsistentes Rauschprofil"];
              reasoning = "Keine typischen KI-Artefakte gefunden.";
          }

          setScanResult({
            filename: file.name,
            is_fake: isFake,
            probability: isFake ? Math.floor(Math.random() * 20) + 78 : Math.floor(Math.random() * 20) + 2,
            reasoning: reasoning,
            artifacts: artifacts
          });
          setScanState('result');
        }, 2500);
      }
    };

    return (
      <div className="fade-in">
        <div className="flex items-center gap-3 border-b border-slate-700 pb-4 mb-8">
            <IconScanner />
            <h2 className="text-3xl font-bold text-white">Deepfake KI-Scanner (Demo)</h2>
        </div>
        
        <p className="text-slate-300 mb-6">
            Testen Sie verdächtige Bilder, Sprachnachrichten oder Videos. Unser simulierter KI-Detektor analysiert die Datei auf Mikro-Artefakte, die typischerweise von generativer KI hinterlassen werden.
        </p>

        <div className="bg-emerald-900/20 border border-emerald-500/30 p-4 rounded-lg flex items-start gap-3 mb-8">
            <IconCheck />
            <div>
                <strong className="text-emerald-400 block text-sm">Datenschutz garantiert auf pasgri-cloud.de</strong>
                <p className="text-xs text-emerald-200/70 mt-1">Ihre Datei wird nicht dauerhaft gespeichert. Sie wird lediglich für den Zeitraum der Analyse in den flüchtigen Arbeitsspeicher (RAM) geladen und sofort nach der Prüfung unwiderruflich gelöscht.</p>
            </div>
        </div>

        {scanState === 'idle' && (
          <div onClick={() => fileInputRef.current.click()} className="border-2 border-dashed border-slate-600 hover:border-sky-500 bg-slate-800/50 rounded-xl p-16 text-center cursor-pointer transition-colors group">
            <input type="file" ref={fileInputRef} className="hidden" accept="image/*,video/*,audio/*" onChange={handleFileSelect} />
            <svg className="mx-auto h-12 w-12 text-slate-400 group-hover:text-sky-500 transition-colors mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            <span className="text-white font-semibold block text-lg">Klicken zum Auswählen einer Datei</span>
            <span className="text-slate-400 text-sm mt-2 block">Unterstützt: JPG, PNG, MP4, MP3, WAV (Max. 50MB)</span>
          </div>
        )}

        {scanState === 'scanning' && (
          <div className="border border-sky-500 bg-slate-800/50 rounded-xl p-16 text-center relative overflow-hidden">
             <div className="absolute top-0 left-0 w-full h-1 bg-sky-500 animate-pulse"></div>
             <div className="inline-block animate-spin rounded-full h-12 w-12 border-4 border-sky-500 border-t-transparent mb-4"></div>
             <p className="text-sky-400 font-bold text-lg">KI-Analyse läuft...</p>
             <p className="text-sm text-slate-400 mt-2">Prüfe auf visuelle Inkonsistenzen und Frequenz-Anomalien.</p>
          </div>
        )}

        {scanState === 'result' && scanResult && (
          <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden shadow-2xl">
            <div className="p-6 border-b border-slate-700 flex justify-between items-center bg-slate-800/80">
              <h3 className="text-xl font-bold text-white">Analysebericht</h3>
              <span className={`px-3 py-1 rounded text-sm font-bold uppercase tracking-wider ${scanResult.is_fake ? 'bg-rose-500 text-white' : 'bg-emerald-500 text-white'}`}>
                {scanResult.is_fake ? 'Deepfake Verdacht' : 'Wahrscheinlich Echt'}
              </span>
            </div>
            
            <div className="p-6">
                <p className="text-slate-400 text-sm mb-6">Dateiname: <span className="font-mono text-white ml-2">{scanResult.filename}</span></p>
                
                <div className="mb-8">
                <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-300">Wahrscheinlichkeit für KI-Generierung</span>
                    <span className={`font-bold ${scanResult.is_fake ? 'text-rose-400' : 'text-emerald-400'}`}>{scanResult.probability}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-3">
                    <div className={`h-3 rounded-full transition-all duration-1000 ${scanResult.is_fake ? 'bg-rose-500' : 'bg-emerald-500'}`} style={{ width: `${scanResult.probability}%` }}></div>
                </div>
                </div>

                <div className="bg-slate-900 p-5 rounded-lg border border-slate-700">
                    <h4 className="text-white font-bold mb-3">Ergebnis-Details:</h4>
                    <p className="text-slate-300 italic mb-4 text-sm bg-slate-800 p-3 rounded">{scanResult.reasoning}</p>
                    <h5 className="text-slate-400 text-xs uppercase tracking-wider mb-2 font-bold">Gefundene Artefakte:</h5>
                    <ul className="list-disc list-inside text-slate-300 text-sm space-y-2">
                        {scanResult.artifacts.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                </div>

                <div className="mt-6 p-4 bg-yellow-900/20 border-l-4 border-yellow-500 rounded-r-lg">
                    <p className="text-sm text-yellow-200">
                        <strong>Wichtige Erkenntnis:</strong> Erkennungs-Tools sind ein Katz-und-Maus-Spiel. Verlassen Sie sich bei der Verifikation von Personen niemals rein auf technische Tools, sondern immer auf sichere Prozesse (Rückruf, Codewörter).
                    </p>
                </div>

                <button onClick={() => { setScanState('idle'); if(fileInputRef.current) fileInputRef.current.value = ''; }} className="mt-8 w-full py-3 font-bold bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors">Neue Datei prüfen</button>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-200 flex flex-col font-sans selection:bg-sky-500/30">
      <nav className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between h-16">
          <div className="flex items-center cursor-pointer group" onClick={() => handleNavClick('home')}>
            <div className="group-hover:scale-110 transition-transform"><IconShield /></div>
            <span className="font-bold text-xl text-white tracking-tight">SecAware</span>
          </div>
          <div className="hidden md:flex items-center space-x-1">
            <NavButton target="home" label="Start" />
            <NavButton target="info" label="Bedrohungen" />
            <NavButton target="protection" label="Schutz" />
            <NavButton target="quiz" label="Quiz" />
            <NavButton target="scenarios" label="Szenarien" />
            <NavButton target="scanner" label="KI-Scanner" icon={<IconScanner/>} />
          </div>
          <div className="flex items-center md:hidden">
            <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} className="text-slate-300 hover:text-white p-2">
              <IconMenu />
            </button>
          </div>
        </div>
        {mobileMenuOpen && (
          <div className="md:hidden bg-slate-800 border-b border-slate-700 px-2 pt-2 pb-3 space-y-1 shadow-inner">
             {['home', 'info', 'protection', 'quiz', 'scenarios', 'scanner'].map(v => (
               <button key={v} onClick={() => handleNavClick(v)} className="block w-full text-left px-4 py-3 rounded-md text-white hover:bg-slate-700 capitalize font-medium">
                 {v === 'scanner' ? 'KI-Scanner' : v}
               </button>
             ))}
          </div>
        )}
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
        <p className="font-medium">Ein Universitätsprojekt zur Cybersecurity-Awareness.</p>
        <p className="mt-2">Deployed on <a href="https://pasgri-cloud.de" className="text-sky-400 hover:text-sky-300 hover:underline font-medium transition-colors">pasgri-cloud.de</a></p>
      </footer>
    </div>
  );
}