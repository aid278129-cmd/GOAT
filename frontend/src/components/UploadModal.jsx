import React, { useState } from 'react';

export function UploadModal({ isOpen, onClose, onFileIngested }) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  if (!isOpen) return null;

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
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleIngest = () => {
    if (selectedFile && onFileIngested) {
      onFileIngested(selectedFile);
    }
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-[#0d121f] border border-slate-800 rounded-2xl max-w-md w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-cyan-950/60 border border-cyan-800/60 flex items-center justify-center text-cyan-400">
              <span className="material-symbols-outlined text-[16px]">upload_file</span>
            </div>
            <h3 className="font-bold text-sm text-slate-100 font-['Space_Grotesk']">Multimodal Technical Ingestion</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <span className="material-symbols-outlined text-base">close</span>
          </button>
        </div>

        <div className="p-6 flex flex-col gap-4">
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
              id="file-upload"
              className="hidden"
              onChange={handleChange}
              accept=".step,.stp,.stl,.pdf,.docx,.zip"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <span className="material-symbols-outlined text-3xl text-cyan-400 block mb-2">
                drive_folder_upload
              </span>
              <span className="text-xs font-semibold text-slate-200 block font-['Space_Grotesk']">
                {selectedFile ? selectedFile.name : 'Select or drop technical files here'}
              </span>
              <span className="text-[11px] text-slate-400 block mt-1 font-mono">
                STEP, STL, Gerber, schematic PDFs, and test reports
              </span>
            </label>
          </div>

          <div className="p-3 bg-cyan-950/40 rounded-lg border border-cyan-800/50 flex items-start gap-2">
            <span className="material-symbols-outlined text-cyan-400 text-sm mt-0.5">info</span>
            <div className="text-[11px] text-cyan-200 leading-relaxed">
              Files are processed locally for spatial geometry extraction and statutory clause alignment.
            </div>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleIngest}
              disabled={!selectedFile}
              className="px-4 py-2 bg-gradient-to-r from-cyan-400 to-sky-400 hover:from-cyan-300 hover:to-sky-300 disabled:opacity-40 text-slate-950 rounded-lg text-xs font-semibold transition-all shadow-md shadow-cyan-500/20 cursor-pointer"
            >
              Ingest &amp; Process
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
