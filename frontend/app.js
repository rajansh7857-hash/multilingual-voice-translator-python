// ==========================================================================
// VoiceBridge - Real-Time Multilingual Group Voice Translator Client
// ==========================================================================

const State = {
    user: {
        id: 'usr_' + Math.random().toString(36).substring(2, 9),
        name: '',
        language: 'hi', // Default to Hindi or English
    },
    room: {
        id: '',
        participants: []
    },
    ws: null,
    speechRecognition: null,
    isListening: false,
    isPTTActive: false,
    autoTTS: true,
    ttsRate: 1.0,
    ttsPitch: 1.0,
    selectedVoiceURI: '',
    languages: [],
    voices: []
};

// --- Web Audio Synthesizer for UI sound effects (Zero external files needed) ---
const SoundFX = {
    ctx: null,
    init() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (AudioCtx) this.ctx = new AudioCtx();
        }
    },
    playTone(freq, type, duration) {
        try {
            this.init();
            if (!this.ctx) return;
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();
            osc.type = type;
            osc.frequency.setValueAtTime(freq, this.ctx.currentTime);
            gain.gain.setValueAtTime(0.08, this.ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + duration);
            osc.connect(gain);
            gain.connect(this.ctx.destination);
            osc.start();
            osc.stop(this.ctx.currentTime + duration);
        } catch (e) {
            // Ignore audio ctx autoplay restrictions
        }
    },
    micOn() { this.playTone(587.33, 'sine', 0.15); },   // D5 chime
    micOff() { this.playTone(440.00, 'sine', 0.12); },  // A4 chime
    messageIn() { this.playTone(880.00, 'triangle', 0.2); } // High ding
};

// --- DOM Elements ---
const DOM = {
    // Nav & Status
    headerRoomInfo: document.getElementById('header-room-info'),
    displayRoomId: document.getElementById('display-room-id'),
    userLangBadge: document.getElementById('user-language-badge'),
    btnCopyRoom: document.getElementById('btn-copy-room'),
    btnLeaveRoom: document.getElementById('btn-leave-room'),
    btnOpenSettings: document.getElementById('btn-open-settings'),
    connectionStatus: document.getElementById('connection-status'),
    connectionText: document.getElementById('connection-text'),

    // Screens
    lobbyScreen: document.getElementById('lobby-screen'),
    roomScreen: document.getElementById('room-screen'),

    // Lobby Form
    joinForm: document.getElementById('join-form'),
    inputName: document.getElementById('input-name'),
    selectLanguage: document.getElementById('select-language'),
    inputRoom: document.getElementById('input-room'),
    btnGenerateRoom: document.getElementById('btn-generate-room'),

    // Room elements
    participantCount: document.getElementById('participant-count'),
    participantsContainer: document.getElementById('participants-container'),
    messagesFeed: document.getElementById('messages-feed'),
    activeSpeakerBanner: document.getElementById('active-speaker-banner'),
    activeSpeakerText: document.getElementById('active-speaker-text'),
    interimSpeechBox: document.getElementById('interim-speech-box'),
    interimTranscript: document.getElementById('interim-transcript'),

    // Controls
    btnToggleMic: document.getElementById('btn-toggle-mic'),
    micIcon: document.getElementById('mic-icon'),
    micBtnLabel: document.getElementById('mic-btn-label'),
    micIndicatorDot: document.getElementById('mic-indicator-dot'),
    btnPTT: document.getElementById('btn-ptt'),
    toggleAutoTTS: document.getElementById('toggle-autotts'),
    btnTestTTS: document.getElementById('btn-test-tts'),
    textChatForm: document.getElementById('text-chat-form'),
    inputChatText: document.getElementById('input-chat-text'),

    // Settings Modal
    settingsModal: document.getElementById('settings-modal'),
    btnCloseSettings: document.getElementById('btn-close-settings'),
    btnSaveSettings: document.getElementById('btn-save-settings'),
    modalSelectLanguage: document.getElementById('modal-select-language'),
    selectVoice: document.getElementById('select-voice'),
    sliderRate: document.getElementById('slider-rate'),
    rateVal: document.getElementById('rate-val'),
    sliderPitch: document.getElementById('slider-pitch'),
    pitchVal: document.getElementById('pitch-val')
};

// --- Initialization & Language Catalog ---
async function initApp() {
    setupDefaultValues();
    await loadSupportedLanguages();
    loadAvailableVoices();
    setupEventListeners();
    checkUrlHashForRoom();
}

function setupDefaultValues() {
    const randomNames = ['Aarav', 'Priya', 'Rahul', 'Ananya', 'Rohan', 'Sneha', 'Vikram', 'Neha', 'Arjun', 'Pooja', 'Alex', 'Elena'];
    DOM.inputName.value = randomNames[Math.floor(Math.random() * randomNames.length)];
    DOM.inputRoom.value = 'bharat-sync';
}

function checkUrlHashForRoom() {
    const hash = window.location.hash.replace('#', '').trim();
    if (hash) {
        DOM.inputRoom.value = hash;
    }
}

async function loadSupportedLanguages() {
    try {
        const res = await fetch('/api/languages');
        const data = await res.json();
        State.languages = data.languages || [];
        
        populateLanguageSelects();
    } catch (e) {
        console.error('Failed to load language list:', e);
    }
}

function populateLanguageSelects() {
    DOM.selectLanguage.innerHTML = '';
    DOM.modalSelectLanguage.innerHTML = '';

    // Group languages by category: Indian Languages vs Global Languages
    const groups = {};
    State.languages.forEach(lang => {
        const cat = lang.category || 'Other Languages';
        if (!groups[cat]) groups[cat] = [];
        groups[cat].push(lang);
    });

    for (const [categoryName, langs] of Object.entries(groups)) {
        const optgroup1 = document.createElement('optgroup');
        optgroup1.label = categoryName;

        const optgroup2 = document.createElement('optgroup');
        optgroup2.label = categoryName;

        langs.forEach(lang => {
            const opt1 = document.createElement('option');
            opt1.value = lang.code;
            opt1.textContent = `${lang.flag} ${lang.name}`;
            optgroup1.appendChild(opt1);

            const opt2 = document.createElement('option');
            opt2.value = lang.code;
            opt2.textContent = `${lang.flag} ${lang.name}`;
            optgroup2.appendChild(opt2);
        });

        DOM.selectLanguage.appendChild(optgroup1);
        DOM.modalSelectLanguage.appendChild(optgroup2);
    }

    DOM.selectLanguage.value = 'hi';
    DOM.modalSelectLanguage.value = 'hi';
}

function loadAvailableVoices() {
    if (!('speechSynthesis' in window)) return;
    
    function populate() {
        State.voices = window.speechSynthesis.getVoices();
        DOM.selectVoice.innerHTML = '<option value="">Auto-Detect Best Voice for Language</option>';
        State.voices.forEach(voice => {
            const opt = document.createElement('option');
            opt.value = voice.voiceURI;
            opt.textContent = `${voice.name} (${voice.lang})`;
            DOM.selectVoice.appendChild(opt);
        });
    }

    populate();
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = populate;
    }
}

// --- WebSocket Connection ---
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/${State.room.id}/${State.user.id}?name=${encodeURIComponent(State.user.name)}&language=${State.user.language}`;

    updateConnectionStatus('connecting', 'Connecting...');
    State.ws = new WebSocket(wsUrl);

    State.ws.onopen = () => {
        updateConnectionStatus('connected', 'Live');
        console.log('Connected to translation room WebSocket');
        State.pingInterval = setInterval(() => {
            if (State.ws && State.ws.readyState === WebSocket.OPEN) {
                State.ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 25000);
    };

    State.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleIncomingWSMessage(data);
        } catch (e) {
            console.error('Error parsing WS message:', e);
        }
    };

    State.ws.onclose = () => {
        updateConnectionStatus('disconnected', 'Disconnected');
        clearInterval(State.pingInterval);
    };

    State.ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        updateConnectionStatus('disconnected', 'Error');
    };
}

function updateConnectionStatus(status, text) {
    DOM.connectionText.textContent = text;
    DOM.connectionStatus.className = 'flex items-center space-x-2 text-xs ' + 
        (status === 'connected' ? 'text-emerald-400' : status === 'connecting' ? 'text-amber-400' : 'text-rose-400');
    
    const dot = DOM.connectionStatus.querySelector('span:first-child');
    if (dot) {
        dot.className = 'w-2.5 h-2.5 rounded-full ' + 
            (status === 'connected' ? 'bg-emerald-500 animate-pulse' : status === 'connecting' ? 'bg-amber-500 animate-pulse' : 'bg-rose-500');
    }
}

function handleIncomingWSMessage(data) {
    switch (data.type) {
        case 'room_update':
            State.room.participants = data.participants || [];
            renderParticipants(State.room.participants);
            if (data.system_message) {
                appendSystemNotification(data.system_message);
            }
            break;

        case 'speech_message':
            appendSpeechMessage(data);
            SoundFX.messageIn();
            if (State.autoTTS && !data.is_self) {
                speakText(data.translated_text, State.user.language);
            }
            break;

        case 'user_speaking':
            highlightSpeakingUser(data.user_id, data.name, data.is_speaking);
            break;

        case 'pong':
            break;
    }
}

// --- Render Participants ---
function renderParticipants(participants) {
    DOM.participantCount.textContent = participants.length;
    DOM.participantsContainer.innerHTML = '';

    participants.forEach(p => {
        const isMe = p.user_id === State.user.id;
        const card = document.createElement('div');
        card.id = `participant-card-${p.user_id}`;
        card.className = `flex-shrink-0 flex items-center space-x-2 px-3 py-1.5 rounded-xl border transition-all ${
            isMe ? 'bg-indigo-950/50 border-indigo-500/50' : 'bg-slate-900/70 border-slate-700/60'
        }`;

        card.innerHTML = `
            <div class="relative">
                <div class="w-8 h-8 rounded-full flex items-center justify-center font-bold text-white text-xs shadow-md"
                    style="background-color: ${p.avatar_color || '#6366f1'}">
                    ${p.name.substring(0, 2).toUpperCase()}
                </div>
                <span class="speaking-indicator hidden absolute -top-1 -right-1 w-3 h-3 bg-emerald-400 rounded-full border-2 border-slate-900 animate-ping"></span>
            </div>
            <div class="flex flex-col text-left">
                <div class="flex items-center space-x-1.5">
                    <span class="text-xs font-bold text-slate-200 truncate max-w-[90px]">${escapeHtml(p.name)}</span>
                    ${isMe ? '<span class="text-[10px] bg-indigo-500/30 text-indigo-300 font-bold px-1.5 py-0.2 rounded">YOU</span>' : ''}
                </div>
                <div class="text-[11px] text-slate-400 flex items-center space-x-1">
                    <span>${p.flag || '🌐'}</span>
                    <span class="truncate max-w-[110px]">${escapeHtml(p.language_name || p.language)}</span>
                </div>
            </div>
        `;
        DOM.participantsContainer.appendChild(card);
    });
}

function highlightSpeakingUser(userId, userName, isSpeaking) {
    const card = document.getElementById(`participant-card-${userId}`);
    if (card) {
        const indicator = card.querySelector('.speaking-indicator');
        if (isSpeaking) {
            card.classList.add('border-indigo-400', 'speaking-glow');
            if (indicator) indicator.classList.remove('hidden');
        } else {
            card.classList.remove('border-indigo-400', 'speaking-glow');
            if (indicator) indicator.classList.add('hidden');
        }
    }

    if (isSpeaking) {
        DOM.activeSpeakerBanner.classList.remove('hidden');
        DOM.activeSpeakerText.textContent = `${userName} is speaking...`;
    } else {
        DOM.activeSpeakerBanner.classList.add('hidden');
    }
}

// --- Feed & Messages ---
function appendSpeechMessage(msg) {
    const isMe = msg.is_self;
    const msgCard = document.createElement('div');
    msgCard.className = `flex flex-col space-y-1 max-w-2xl ${isMe ? 'ml-auto items-end' : 'mr-auto items-start'} transition-all animate-fadeIn`;

    const langObj = State.languages.find(l => l.code === msg.sender_lang) || { flag: '🌐', name: msg.sender_lang };

    msgCard.innerHTML = `
        <div class="flex items-center space-x-2 text-[11px] text-slate-400 px-1">
            <span class="font-bold text-slate-300">${escapeHtml(msg.sender_name)}</span>
            <span class="px-1.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 flex items-center gap-1">
                <span>${langObj.flag}</span> <span>${langObj.name}</span>
            </span>
            <span>&bull; ${msg.timestamp}</span>
        </div>

        <div class="glass-card p-4 rounded-2xl border ${
            isMe ? 'border-indigo-500/30 bg-indigo-950/30 text-right' : 'border-slate-800 bg-slate-900/60 text-left'
        } shadow-lg space-y-2 max-w-full">
            
            <!-- Translated Text in Receiver's Language -->
            <div class="flex items-start ${isMe ? 'flex-row-reverse' : 'flex-row'} justify-between gap-3">
                <div class="text-sm md:text-base font-semibold text-white leading-relaxed">
                    ${escapeHtml(msg.translated_text)}
                </div>
                
                <button class="btn-speak-msg p-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/40 text-slate-300 hover:text-white transition flex-shrink-0" title="Listen Audio">
                    <i class="fa-solid fa-volume-high text-xs"></i>
                </button>
            </div>

            <!-- Original Subtitle Transcript (if different from receiver lang) -->
            ${msg.sender_lang !== msg.recipient_lang ? `
                <div class="text-xs text-slate-400 pt-1 border-t border-slate-800/60 flex items-center ${isMe ? 'justify-end' : 'justify-start'} gap-1">
                    <i class="fa-solid fa-quote-left text-[10px] text-slate-500"></i>
                    <span class="italic">"${escapeHtml(msg.original_text)}"</span>
                    <span class="text-[10px] text-slate-500">(${langObj.name})</span>
                </div>
            ` : ''}
        </div>
    `;

    // Replay speech listener
    const speakBtn = msgCard.querySelector('.btn-speak-msg');
    if (speakBtn) {
        speakBtn.addEventListener('click', () => {
            speakText(msg.translated_text, State.user.language);
        });
    }

    DOM.messagesFeed.appendChild(msgCard);
    DOM.messagesFeed.scrollTop = DOM.messagesFeed.scrollHeight;
}

function appendSystemNotification(text) {
    const notif = document.createElement('div');
    notif.className = 'text-center my-2';
    notif.innerHTML = `
        <span class="inline-block px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700/60 text-slate-400 text-xs">
            <i class="fa-solid fa-circle-info text-indigo-400 mr-1"></i> ${escapeHtml(text)}
        </span>
    `;
    DOM.messagesFeed.appendChild(notif);
    DOM.messagesFeed.scrollTop = DOM.messagesFeed.scrollHeight;
}

// --- Speech Recognition (STT) Controller ---
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Web Speech Recognition API is not supported in this browser.');
        return false;
    }

    const currentLangMeta = State.languages.find(l => l.code === State.user.language);
    // Primary locale or fallback
    const recognitionLocale = currentLangMeta ? (currentLangMeta.locale || currentLangMeta.tts_fallback || 'hi-IN') : 'hi-IN';

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = recognitionLocale;

    recognition.onstart = () => {
        State.isListening = true;
        updateMicUI(true);
        SoundFX.micOn();
        broadcastSpeakingState(true);
    };

    recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        if (interimTranscript) {
            DOM.interimSpeechBox.classList.remove('hidden');
            DOM.interimTranscript.textContent = interimTranscript;
        } else {
            DOM.interimSpeechBox.classList.add('hidden');
        }

        if (finalTranscript.trim()) {
            sendSpeechMessage(finalTranscript.trim());
            DOM.interimSpeechBox.classList.add('hidden');
        }
    };

    recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
            alert('Microphone access was denied. Please allow microphone permissions in your browser.');
            stopListening();
        } else if (event.error === 'language-not-supported') {
            // If the browser does not support the specific regional subtag, fallback to standard Hindi/English
            console.log('Language locale not supported by browser STT, falling back to general locale');
            if (recognition.lang !== 'hi-IN' && recognition.lang !== 'en-US') {
                recognition.lang = 'hi-IN';
                try { recognition.start(); } catch(e){}
            }
        }
    };

    recognition.onend = () => {
        if (State.isListening && !State.isPTTActive) {
            try {
                recognition.start();
            } catch (e) {
                // Ignore restart error
            }
        } else if (!State.isPTTActive) {
            updateMicUI(false);
            broadcastSpeakingState(false);
            DOM.interimSpeechBox.classList.add('hidden');
        }
    };

    State.speechRecognition = recognition;
    return true;
}

function startListening() {
    if (!State.speechRecognition) {
        if (!initSpeechRecognition()) {
            alert('Speech Recognition is not supported by your browser. Please use Chrome, Edge, or Safari, or use the text input.');
            return;
        }
    }
    try {
        const currentLangMeta = State.languages.find(l => l.code === State.user.language);
        if (currentLangMeta && State.speechRecognition) {
            State.speechRecognition.lang = currentLangMeta.locale || currentLangMeta.tts_fallback || 'hi-IN';
        }
        State.isListening = true;
        State.speechRecognition.start();
    } catch (e) {
        console.warn('Recognition start exception:', e);
    }
}

function stopListening() {
    State.isListening = false;
    if (State.speechRecognition) {
        try {
            State.speechRecognition.stop();
        } catch (e) {}
    }
    updateMicUI(false);
    SoundFX.micOff();
    broadcastSpeakingState(false);
    DOM.interimSpeechBox.classList.add('hidden');
}

function toggleListening() {
    if (State.isListening) {
        stopListening();
    } else {
        startListening();
    }
}

function updateMicUI(isMicActive) {
    if (isMicActive) {
        DOM.btnToggleMic.className = 'relative group px-6 py-3 rounded-2xl bg-rose-600 hover:bg-rose-500 text-white font-bold shadow-lg shadow-rose-600/40 transition-all transform active:scale-95 flex items-center space-x-2 text-sm animate-pulse';
        DOM.micIcon.className = 'fa-solid fa-microphone-lines text-base';
        DOM.micBtnLabel.textContent = 'Mute Microphone';
        DOM.micIndicatorDot.className = 'w-2.5 h-2.5 rounded-full bg-rose-300 animate-ping';
    } else {
        DOM.btnToggleMic.className = 'relative group px-6 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold shadow-lg shadow-indigo-600/30 transition-all transform active:scale-95 flex items-center space-x-2 text-sm';
        DOM.micIcon.className = 'fa-solid fa-microphone text-base';
        DOM.micBtnLabel.textContent = 'Start Speaking';
        DOM.micIndicatorDot.className = 'w-2.5 h-2.5 rounded-full bg-white opacity-80';
    }
}

// --- Text-to-Speech (TTS) Controller ---
function speakText(text, langCode) {
    if (!('speechSynthesis' in window) || !text || !text.trim()) return;

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = State.ttsRate || 1.0;
    utterance.pitch = State.ttsPitch || 1.0;

    const langMeta = State.languages.find(l => l.code === langCode);
    const targetLocale = langMeta ? (langMeta.locale || 'hi-IN') : 'hi-IN';
    const fallbackLocale = langMeta ? (langMeta.tts_fallback || 'hi-IN') : 'hi-IN';
    utterance.lang = targetLocale;

    if (State.selectedVoiceURI) {
        const customVoice = State.voices.find(v => v.voiceURI === State.selectedVoiceURI);
        if (customVoice) utterance.voice = customVoice;
    } else {
        // Find best matching voice: exact match -> prefix match -> fallback locale match -> Indian/Hindi voice for Indic scripts
        let matchingVoice = State.voices.find(v => v.lang === targetLocale || v.lang.replace('_', '-') === targetLocale);
        if (!matchingVoice) {
            matchingVoice = State.voices.find(v => v.lang.startsWith(langCode));
        }
        if (!matchingVoice && fallbackLocale) {
            matchingVoice = State.voices.find(v => v.lang === fallbackLocale || v.lang.startsWith(fallbackLocale.substring(0, 2)));
        }
        if (!matchingVoice && langMeta && langMeta.category === 'Indian Languages') {
            matchingVoice = State.voices.find(v => v.lang.includes('IN') || v.lang.startsWith('hi'));
        }
        if (matchingVoice) utterance.voice = matchingVoice;
    }

    window.speechSynthesis.speak(utterance);
}

// --- Message Sending ---
function sendSpeechMessage(text) {
    if (!text || !State.ws || State.ws.readyState !== WebSocket.OPEN) return;

    State.ws.send(JSON.stringify({
        type: 'speech',
        text: text,
        source_lang: State.user.language
    }));
}

function broadcastSpeakingState(isSpeaking) {
    if (!State.ws || State.ws.readyState !== WebSocket.OPEN) return;
    State.ws.send(JSON.stringify({
        type: 'speaking_state',
        is_speaking: isSpeaking
    }));
}

// --- Event Listeners ---
function setupEventListeners() {
    // Room Generation
    DOM.btnGenerateRoom.addEventListener('click', () => {
        const words = ['bharat', 'sangam', 'setu', 'samvad', 'bridge', 'polyglot'];
        const num = Math.floor(100 + Math.random() * 900);
        DOM.inputRoom.value = `${words[Math.floor(Math.random() * words.length)]}-${num}`;
    });

    // Join Form Submit
    DOM.joinForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = DOM.inputName.value.trim();
        const room = DOM.inputRoom.value.trim().toLowerCase();
        const lang = DOM.selectLanguage.value;

        if (!name || !room) return;

        State.user.name = name;
        State.room.id = room;
        State.user.language = lang;

        enterRoom();
    });

    // Mic Toggle Button
    DOM.btnToggleMic.addEventListener('click', () => {
        toggleListening();
    });

    // Push-to-Talk (Hold to speak)
    DOM.btnPTT.addEventListener('mousedown', () => {
        State.isPTTActive = true;
        startListening();
        DOM.btnPTT.classList.add('bg-indigo-600', 'text-white');
    });

    DOM.btnPTT.addEventListener('mouseup', () => {
        if (State.isPTTActive) {
            State.isPTTActive = false;
            stopListening();
            DOM.btnPTT.classList.remove('bg-indigo-600', 'text-white');
        }
    });

    // Auto-TTS Toggle
    DOM.toggleAutoTTS.addEventListener('change', (e) => {
        State.autoTTS = e.target.checked;
    });

    // Test TTS Button
    DOM.btnTestTTS.addEventListener('click', () => {
        const langMeta = State.languages.find(l => l.code === State.user.language);
        const samplePhrases = {
            'hi': 'नमस्ते! ध्वनि अनुवाद सक्रिय और तैयार है।',
            'bn': 'নমস্কার! ভয়েস অনুবাদ সক্রিয় এবং প্রস্তুত।',
            'te': 'నమస్కారం! వాయిస్ అనువాదం సిద్ధంగా ఉంది.',
            'ta': 'வணக்கம்! குரல் மொழிபெயர்ப்பு தயாராக உள்ளது.',
            'mr': 'नमस्कार! व्हॉइस भाषांतर सक्रिय आणि तयार आहे.',
            'gu': 'નમસ્તે! વૉઇસ ટ્રાન્સલેશન તૈયાર છે.',
            'kn': 'ನಮಸ್ಕಾರ! ಧ್ವನಿ ಅನುವಾದ ಸಿದ್ಧವಾಗಿದೆ.',
            'ml': 'നമസ്കാരം! വോയ്‌സ് വിവർത്തനം തയ്യാറാണ്.',
            'pa': 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਆਵਾਜ਼ ਅਨੁਵਾਦ ਤਿਆਰ ਹੈ।',
            'or': 'ନମସ୍କାର! ଭଏସ୍ ଅନୁବାଦ ପ୍ରସ୍ତୁତ ଅଛି।',
            'as': 'নমস্কাৰ! ভয়েচ অনুবাদ সাজু হৈছে।',
            'sa': 'नमस्ते! ध्वनि अनुवादः सक्रियः अस्ति।',
            'ur': 'السلام علیکم! آواز کا ترجمہ تیار ہے۔',
            'en': 'Hello! Voice translation is active and ready.',
            'es': '¡Hola! La traducción de voz está activa y lista.',
            'fr': 'Bonjour! La traduction vocale est active et prête.',
            'de': 'Hallo! Die Sprachübersetzung ist aktiv und bereit.',
            'ja': 'こんにちは！音声翻訳が準備完了しました。'
        };
        const phrase = samplePhrases[State.user.language] || `Welcome! Translation ready for ${langMeta ? langMeta.name : State.user.language}.`;
        speakText(phrase, State.user.language);
    });

    // Text Fallback Chat Form
    DOM.textChatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const text = DOM.inputChatText.value.trim();
        if (text) {
            sendSpeechMessage(text);
            DOM.inputChatText.value = '';
        }
    });

    // Copy Room Link
    DOM.btnCopyRoom.addEventListener('click', () => {
        const url = `${window.location.origin}/#${State.room.id}`;
        navigator.clipboard.writeText(url).then(() => {
            const originalHtml = DOM.btnCopyRoom.innerHTML;
            DOM.btnCopyRoom.innerHTML = '<i class="fa-solid fa-check text-emerald-400"></i>';
            setTimeout(() => { DOM.btnCopyRoom.innerHTML = originalHtml; }, 2000);
        });
    });

    // Leave Room
    DOM.btnLeaveRoom.addEventListener('click', () => {
        leaveRoom();
    });

    // Settings Modal
    DOM.btnOpenSettings.addEventListener('click', () => {
        DOM.modalSelectLanguage.value = State.user.language;
        DOM.settingsModal.classList.remove('hidden');
    });

    DOM.btnCloseSettings.addEventListener('click', () => {
        DOM.settingsModal.classList.add('hidden');
    });

    DOM.sliderRate.addEventListener('input', (e) => {
        State.ttsRate = parseFloat(e.target.value);
        DOM.rateVal.textContent = `${State.ttsRate}x`;
    });

    DOM.sliderPitch.addEventListener('input', (e) => {
        State.ttsPitch = parseFloat(e.target.value);
        DOM.pitchVal.textContent = State.ttsPitch;
    });

    DOM.btnSaveSettings.addEventListener('click', () => {
        const newLang = DOM.modalSelectLanguage.value;
        const newVoice = DOM.selectVoice.value;
        State.selectedVoiceURI = newVoice;

        if (newLang !== State.user.language) {
            State.user.language = newLang;
            updateHeaderLanguageBadge();
            if (State.isListening) {
                stopListening();
                initSpeechRecognition();
                startListening();
            } else {
                initSpeechRecognition();
            }

            if (State.ws && State.ws.readyState === WebSocket.OPEN) {
                State.ws.send(JSON.stringify({
                    type: 'update_profile',
                    language: newLang,
                    name: State.user.name
                }));
            }
        }
        DOM.settingsModal.classList.add('hidden');
    });
}

function enterRoom() {
    DOM.lobbyScreen.classList.add('hidden');
    DOM.roomScreen.classList.remove('hidden');
    DOM.headerRoomInfo.classList.remove('hidden');

    DOM.displayRoomId.textContent = State.room.id;
    window.location.hash = State.room.id;

    updateHeaderLanguageBadge();
    connectWebSocket();
    initSpeechRecognition();
}

function leaveRoom() {
    stopListening();
    if (State.ws) {
        State.ws.close();
    }
    DOM.roomScreen.classList.add('hidden');
    DOM.headerRoomInfo.classList.add('hidden');
    DOM.lobbyScreen.classList.remove('hidden');
    DOM.messagesFeed.innerHTML = '';
}

function updateHeaderLanguageBadge() {
    const langObj = State.languages.find(l => l.code === State.user.language) || { flag: '🌐', name: State.user.language };
    DOM.userLangBadge.innerHTML = `<span>${langObj.flag}</span> <span>${escapeHtml(langObj.name)}</span>`;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Start application
document.addEventListener('DOMContentLoaded', initApp);
