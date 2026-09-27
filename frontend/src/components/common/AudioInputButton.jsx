import React, { useState, useEffect, useRef } from 'react';

/**
 * AudioInputButton
 * 
 * Provides audio microphone voice-input support using the Web Speech API
 * (window.SpeechRecognition / window.webkitSpeechRecognition) with live audio
 * amplitude animation, interim transcripts, and multi-language support (EN, HI, TA).
 */
export function AudioInputButton({
  onTranscript,
  language = 'en',
  className = '',
  disabled = false,
}) {
  const [isListening, setIsListening] = useState(false);
  const [interimText, setInterimText] = useState('');
  const [supported, setSupported] = useState(true);
  const [errorMessage, setErrorMessage] = useState(null);
  const recognitionRef = useRef(null);

  // Map app language code to BCP 47 locale
  const getLocale = (lang) => {
    switch (lang) {
      case 'hi':
        return 'hi-IN';
      case 'ta':
        return 'ta-IN';
      default:
        return 'en-IN';
    }
  };

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.lang = getLocale(language);

      recognition.onstart = () => {
        setIsListening(true);
        setErrorMessage(null);
      };

      recognition.onresult = (event) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            final += transcript;
          } else {
            interim += transcript;
          }
        }

        if (interim) {
          setInterimText(interim);
        }

        if (final && onTranscript) {
          onTranscript(final.trim(), true);
          setInterimText('');
        }
      };

      recognition.onerror = (event) => {
        console.warn('Speech recognition event notice:', event.error);
        if (event.error === 'not-allowed') {
          setErrorMessage('Microphone access denied. Please allow microphone permissions.');
        } else if (event.error !== 'no-speech') {
          setErrorMessage(`Audio input notice: ${event.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        setInterimText('');
      };

      recognitionRef.current = recognition;
    } catch (e) {
      console.warn('Speech recognition setup error:', e);
      setSupported(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch { }
      }
    };
  }, [language, onTranscript]);

  const toggleListening = (e) => {
    e?.preventDefault();
    if (disabled) return;

    if (!supported) {
      alert('Voice input is not supported in this browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch { }
      setIsListening(false);
      setInterimText('');
    } else {
      setErrorMessage(null);
      try {
        if (recognitionRef.current) {
          recognitionRef.current.lang = getLocale(language);
          recognitionRef.current.start();
        }
      } catch (err) {
        console.warn('Failed to start speech recognition:', err);
      }
    }
  };

  return (
    <div className="relative inline-flex items-center">
      <button
        type="button"
        onClick={toggleListening}
        disabled={disabled}
        aria-label={isListening ? 'Stop voice recording' : 'Start voice input'}
        title={
          isListening
            ? 'Listening... Click to stop speaking'
            : `Voice Input (${getLocale(language)}) - Click and speak`
        }
        className={`relative p-2.5 rounded-xl transition-all flex items-center justify-center cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${
          isListening
            ? 'bg-rose-500/20 text-rose-400 border border-rose-500/50 shadow-[0_0_15px_rgba(244,63,94,0.4)] animate-pulse'
            : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-cyan-300 border border-slate-700/80 hover:border-cyan-500/40 shadow-xs'
        } ${className}`}
      >
        {isListening ? (
          <div className="flex items-center gap-1.5">
            {/* Animated equalizer waves */}
            <span className="flex items-center gap-0.5 h-4">
              <span className="w-1 bg-rose-400 rounded-full animate-[bounce_0.8s_ease-in-out_infinite_100ms] h-3"></span>
              <span className="w-1 bg-rose-300 rounded-full animate-[bounce_0.8s_ease-in-out_infinite_300ms] h-4"></span>
              <span className="w-1 bg-rose-400 rounded-full animate-[bounce_0.8s_ease-in-out_infinite_200ms] h-2.5"></span>
            </span>
            <span className="text-[11px] font-mono font-bold text-rose-300 pr-1">Listening</span>
          </div>
        ) : (
          <span className="material-symbols-outlined text-[18px]">mic</span>
        )}
      </button>

      {/* Floating active interim text bubble */}
      {isListening && interimText && (
        <div className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 z-50 px-3 py-1.5 rounded-lg bg-slate-900/95 border border-rose-500/40 text-rose-200 text-xs shadow-xl whitespace-nowrap backdrop-blur-md flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
          <span className="italic">"{interimText}"</span>
        </div>
      )}

      {/* Error alert toast */}
      {errorMessage && (
        <div className="absolute bottom-full mb-2 left-0 z-50 px-3 py-1.5 rounded-lg bg-rose-950/90 border border-rose-500/50 text-rose-200 text-[11px] shadow-xl whitespace-nowrap">
          {errorMessage}
        </div>
      )}
    </div>
  );
}

/**
 * TextToSpeechButton
 * 
 * Allows users to listen to the chatbot's answers read aloud with statutory tone.
 */
export function TextToSpeechButton({ text, language = 'en', className = '' }) {
  const [isPlaying, setIsPlaying] = useState(false);

  const handleSpeak = (e) => {
    e?.preventDefault();
    if (!('speechSynthesis' in window)) return;

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language === 'hi' ? 'hi-IN' : language === 'ta' ? 'ta-IN' : 'en-IN';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onstart = () => setIsPlaying(true);
    utterance.onend = () => setIsPlaying(false);
    utterance.onerror = () => setIsPlaying(false);

    window.speechSynthesis.speak(utterance);
  };

  return (
    <button
      type="button"
      onClick={handleSpeak}
      title={isPlaying ? 'Stop listening' : 'Listen to answer'}
      className={`p-1 text-slate-400 hover:text-cyan-300 rounded transition-colors cursor-pointer ${
        isPlaying ? 'text-cyan-400' : ''
      } ${className}`}
    >
      <span className="material-symbols-outlined text-[15px]">
        {isPlaying ? 'volume_off' : 'volume_up'}
      </span>
    </button>
  );
}
