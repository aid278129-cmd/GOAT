import React, { useState, useRef, useEffect } from 'react';
import {
  EvidenceCategory,
  EvidenceSubType,
  ProcessingStatus,
  AcceptanceStatus,
  EngineeringAssessmentStatus,
  HumanAttestationStatus,
  BisCertificationStatus,
  ArtifactIntegrityStatus,
} from '../../types/evidenceTypes';
import { computeFileSHA256, formatBytes, formatTimestamp } from '../../utils/evidenceCrypto';
import { MorphingInfinity } from '../loading-ui/morphing-infinity';
import { TextShimmer } from '../loading-ui/text-shimmer';

export function AddEvidenceModal({ isOpen, onClose, onAddEvidence }) {
  const [activeTab, setActiveTab] = useState('universal');
  const [dragActive, setDragActive] = useState(false);

  // Form states
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedSubType, setSelectedSubType] = useState('DATASHEET');
  const [notes, setNotes] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);

  // Audio Recording States
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);

  // Clean up audio object URL on unmount or reset
  useEffect(() => {
    return () => {
      if (audioUrl) URL.revokeObjectURL(audioUrl);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [audioUrl]);

  if (!isOpen) return null;

  // Audio Recording Controls
  const startAudioRecording = async () => {
    try {
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        const url = URL.createObjectURL(blob);
        setAudioUrl(url);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingDuration(0);

      timerIntervalRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.warn('Microphone access error:', err);
      alert('Microphone access denied or unavailable. You can also upload audio files (.wav, .mp3) directly.');
    }
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelected = (file) => {
    setSelectedFile(file);
    // Auto-select sensible subtype based on file extension
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (ext === 'pdf') {
      setSelectedSubType('DATASHEET');
    } else if (['step', 'stp', 'stl'].includes(ext)) {
      setSelectedSubType('STEP_CAD');
    } else if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) {
      setSelectedSubType('PRODUCT_PHOTO');
    } else if (['wav', 'mp3', 'm4a', 'ogg'].includes(ext)) {
      setSelectedSubType('ACOUSTIC_MEASUREMENT');
    } else if (['csv', 'xlsx'].includes(ext)) {
      setSelectedSubType('BOM_TABLE');
    }
  };

  const handleIngestSubmit = async (e) => {
    e.preventDefault();
    const payload = selectedFile || audioBlob;
    if (!payload) return;

    try {
      setIsProcessing(true);

      // Compute client-side SHA-256 for deterministic immutable ledger
      const sha256 = await computeFileSHA256(payload);

      const fileName = selectedFile
        ? selectedFile.name
        : `Inspection_Audio_${new Date().toISOString().replace(/[:.]/g, '-')}.webm`;
      const fileSize = payload.size;
      const mimeType = payload.type || 'application/octet-stream';

      // Find the subtype definition
      const subTypeObj = EvidenceSubType[selectedSubType] || EvidenceSubType.TECHNICAL_FILE;

      // Build specialized category payloads
      const categoryPayload = {};
      if (subTypeObj.category === EvidenceCategory.AUDIO) {
        categoryPayload.audioDurationSeconds = recordingDuration || 0;
        categoryPayload.sampleRateHz = 48000;
        categoryPayload.audioFormat = mimeType.includes('webm') ? 'WEBM' : 'WAV';
      }

      // Complete Statutory Evidence Record adhering strictly to invariant state machine
      const evidenceRecord = {
        id: `EV-${Date.now()}-${Math.random().toString(36).substr(2, 4).toUpperCase()}`,
        name: fileName,
        category: subTypeObj.category,
        subType: selectedSubType,
        sha256,
        sizeBytes: fileSize,
        mimeType,
        uploadedAt: new Date().toISOString(),

        // 6-stage lifecycle invariant guarantees
        processingStatus: ProcessingStatus.COMPLETED,
        acceptanceStatus: AcceptanceStatus.REQUIRES_REVIEW, // NEVER auto-accepted!
        engineeringAssessmentStatus: EngineeringAssessmentStatus.NOT_EVALUATED,
        humanAttestationStatus: HumanAttestationStatus.UNSIGNED,
        bisCertificationStatus: BisCertificationStatus.NOT_SUBMITTED,

        notes: notes || '',
        categoryPayload,
        rawFile: payload,
      };

      if (onAddEvidence) {
        onAddEvidence(evidenceRecord);
      }

      // Reset modal state
      setSelectedFile(null);
      setAudioBlob(null);
      setAudioUrl(null);
      setNotes('');
      setIsProcessing(false);
      onClose();
    } catch (err) {
      console.warn('Error during evidence ingestion:', err);
      setIsProcessing(false);
    }
  };

  const currentCategory =
    activeTab === 'pdf'
      ? EvidenceCategory.PDF
      : activeTab === 'audio'
      ? EvidenceCategory.AUDIO
      : activeTab === 'image'
      ? EvidenceCategory.IMAGE
      : activeTab === 'engineering'
      ? EvidenceCategory.ENGINEERING
      : null;

  const relevantSubTypes = Object.values(EvidenceSubType).filter(
    (st) => !currentCategory || st.category === currentCategory
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-[#0d121f] border border-slate-800 rounded-2xl max-w-2xl w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <span className="w-8 h-8 rounded-lg bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 flex items-center justify-center shadow-sm">
              <span className="material-symbols-outlined text-base">add_circle</span>
            </span>
            <div>
              <h3 className="font-bold text-sm text-slate-100 font-['Space_Grotesk']">Universal Evidence Ingestion</h3>
              <span className="text-[10px] font-mono text-cyan-400 block tracking-widest uppercase font-semibold">
                STATUTORY PROVENANCE // ZERO-HALLUCINATION INGESTION
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        </div>

        {/* Ingestion Mode Tabs */}
        <div className="flex items-center border-b border-slate-800 bg-slate-900/40 px-6 overflow-x-auto no-scrollbar gap-2 py-2.5">
          <button
            type="button"
            onClick={() => setActiveTab('universal')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'universal'
                ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60 shadow-inner'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">upload_file</span>
            Upload File
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('pdf');
              setSelectedSubType('DATASHEET');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'pdf'
                ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60 shadow-inner'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">picture_as_pdf</span>
            PDF Documents
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('audio');
              setSelectedSubType('VOICE_NOTE');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'audio'
                ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60 shadow-inner'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">mic</span>
            Record / Audio
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('image');
              setSelectedSubType('PRODUCT_PHOTO');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'image'
                ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60 shadow-inner'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">image</span>
            Add Image
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('engineering');
              setSelectedSubType('STEP_CAD');
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 cursor-pointer ${
              activeTab === 'engineering'
                ? 'bg-cyan-950/60 text-cyan-300 font-semibold border border-cyan-800/60 shadow-inner'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-sm">view_in_ar</span>
            Engineering File
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleIngestSubmit} className="p-6 flex flex-col gap-4 overflow-y-auto">
          {/* Regulatory Notice */}
          <div className="p-3.5 bg-cyan-950/40 border border-cyan-800/60 rounded-xl flex items-start gap-2.5">
            <span className="material-symbols-outlined text-cyan-400 text-base mt-0.5">gavel</span>
            <div className="text-[11px] text-cyan-200 leading-relaxed">
              <span className="font-bold text-cyan-300">Statutory Integrity Rule:</span> File processing and extraction completion does not constitute evidence acceptance. All ingested artifacts enter <span className="font-semibold underline text-amber-300">Requires Review</span> status pending explicit engineering attestation.
            </div>
          </div>

          {/* Audio Ingestion Specific Panel */}
          {activeTab === 'audio' ? (
            <div className="border border-slate-800 rounded-xl p-5 bg-slate-900/60 flex flex-col items-center gap-4">
              <div className="text-center">
                <span className="font-bold text-xs text-slate-100 block font-['Space_Grotesk']">
                  Acoustic Evidence Recording
                </span>
                <span className="text-[11px] text-slate-400">
                  Record live engineer inspection observations or upload acoustic audio files (.wav, .mp3, .m4a).
                </span>
              </div>

              {/* Live Recording Controls */}
              <div className="flex items-center gap-3">
                {!isRecording ? (
                  <button
                    type="button"
                    onClick={startAudioRecording}
                    className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-md shadow-rose-600/20 transition-all cursor-pointer"
                  >
                    <span className="w-2.5 h-2.5 rounded-full bg-white animate-pulse"></span>
                    Start Live Microphone Recording
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={stopAudioRecording}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-xs font-semibold flex items-center gap-2 shadow-md transition-all cursor-pointer"
                  >
                    <span className="material-symbols-outlined text-sm text-rose-400">stop_circle</span>
                    Stop Recording ({recordingDuration}s)
                  </button>
                )}
              </div>

              {/* Audio Playback Review if Recorded */}
              {audioUrl && (
                <div className="w-full bg-slate-900/90 p-3 rounded-xl border border-slate-800 flex flex-col gap-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-slate-200 font-semibold flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-sm text-emerald-400">graphic_eq</span>
                      Inspection Audio Captured ({recordingDuration}s)
                    </span>
                    <button
                      type="button"
                      onClick={() => {
                        setAudioBlob(null);
                        setAudioUrl(null);
                      }}
                      className="text-rose-400 hover:text-rose-300 text-[11px] cursor-pointer"
                    >
                      Discard
                    </button>
                  </div>
                  <audio src={audioUrl} controls className="w-full h-8" />
                </div>
              )}

              <div className="w-full flex items-center gap-3 my-1">
                <div className="h-px bg-slate-800 flex-1" />
                <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">OR UPLOAD AUDIO FILE</span>
                <div className="h-px bg-slate-800 flex-1" />
              </div>

              <input
                type="file"
                accept="audio/*,.wav,.mp3,.m4a,.ogg"
                id="audio-file-input"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
              />
              <label
                htmlFor="audio-file-input"
                className="cursor-pointer text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-medium"
              >
                <span className="material-symbols-outlined text-sm">upload</span>
                Browse and upload audio recording file
              </label>
            </div>
          ) : (
            /* File Drag & Drop Zone */
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
                dragActive
                  ? 'border-cyan-400 bg-cyan-950/30'
                  : 'border-slate-700 bg-slate-900/50 hover:bg-slate-900/80 hover:border-slate-600'
              }`}
            >
              <input
                type="file"
                id="universal-file-upload"
                className="hidden"
                onChange={(e) => e.target.files?.[0] && handleFileSelected(e.target.files[0])}
                accept={
                  activeTab === 'pdf'
                    ? '.pdf'
                    : activeTab === 'image'
                    ? '.jpg,.jpeg,.png,.webp'
                    : activeTab === 'engineering'
                    ? '.step,.stp,.stl,.csv,.xlsx,.gerber,.gbr'
                    : '*/*'
                }
              />
              <label htmlFor="universal-file-upload" className="cursor-pointer block">
                <div className="w-10 h-10 rounded-xl bg-cyan-950/60 border border-cyan-800/60 text-cyan-400 flex items-center justify-center mx-auto mb-2">
                  <span className="material-symbols-outlined text-xl">
                    {activeTab === 'pdf'
                      ? 'picture_as_pdf'
                      : activeTab === 'image'
                      ? 'image'
                      : activeTab === 'engineering'
                      ? 'view_in_ar'
                      : 'cloud_upload'}
                  </span>
                </div>
                <span className="text-xs font-semibold text-slate-200 block font-['Space_Grotesk']">
                  {selectedFile ? selectedFile.name : 'Select or drop evidence artifact here'}
                </span>
                <span className="text-[11px] text-slate-400 block mt-1 font-mono">
                  {selectedFile
                    ? `${formatBytes(selectedFile.size)} · Ready for cryptographic hashing`
                    : 'PDF, Images (JPG, PNG), Audio (WAV, MP3), CAD (STEP, STP, STL), BOM (CSV, XLSX)'}
                </span>
              </label>
            </div>
          )}

          {/* Subtype Classification Dropdown */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Statutory Evidence Subtype <span className="text-rose-400">*</span>
              </label>
              <select
                value={selectedSubType}
                onChange={(e) => setSelectedSubType(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              >
                {relevantSubTypes.map((st) => (
                  <option key={st.id} value={st.id}>
                    {st.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Source Attribution / Entity
              </label>
              <input
                type="text"
                placeholder="e.g. NABL Accredited Lab / Internal QA"
                className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          {/* Inspection Notes */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Inspection / Ingestion Context Notes
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Primary insulation creepage test certificate conducted at 2500V dielectric test point."
              className="w-full px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 resize-none"
            />
          </div>

          {/* Modal Footer */}
          <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
            <span className="text-[11px] font-mono text-cyan-400">
              SHA-256 Calculated via Web Crypto
            </span>
            <div className="flex items-center gap-2.5">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!selectedFile && !audioBlob}
                className="px-4 py-2 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 disabled:opacity-40 text-slate-950 rounded-lg text-xs font-semibold transition-all shadow-md shadow-cyan-500/20 flex items-center gap-1.5 cursor-pointer"
              >
                {isProcessing ? (
                  <>
                    <MorphingInfinity className="w-3.5 h-3.5 text-slate-950 shrink-0" />
                    <TextShimmer baseColor="#020617" shimmerColor="#0891b2" duration={1.5}>
                      Computing Hash...
                    </TextShimmer>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm font-bold">done</span>
                    Ingest Evidence Record
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
