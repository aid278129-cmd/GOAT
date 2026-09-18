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
        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      <div className="relative bg-white border border-[#E2E8F0] rounded-xl max-w-md w-full shadow-2xl z-10 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8F9FA]">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#1D4ED8]">upload_file</span>
            <h3 className="font-bold text-sm text-[#0F172A]">Multimodal Technical Ingestion</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-[#64748B] hover:text-[#0F172A] p-1 rounded"
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
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer ${
              dragActive
                ? 'border-blue-500 bg-blue-50/50'
                : 'border-[#E2E8F0] bg-[#F8F9FA] hover:bg-slate-50'
            }`}
          >
            <input
              type="file"
              id="file-upload"
              className="hidden"
              onChange={handleChange}
              accept=".step,.stp,.stl,.pdf,.docx,.zip"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <span className="material-symbols-outlined text-3xl text-[#94A3B8] block mb-2">
                drive_folder_upload
              </span>
              <span className="text-xs font-semibold text-[#0F172A] block">
                {selectedFile ? selectedFile.name : 'Select or drop technical files here'}
              </span>
              <span className="text-[11px] text-[#64748B] block mt-1">
                STEP, STL, Gerber, schematic PDFs, and test reports
              </span>
            </label>
          </div>

          <div className="p-3 bg-blue-50/60 rounded border border-blue-100 flex items-start gap-2">
            <span className="material-symbols-outlined text-blue-600 text-sm mt-0.5">info</span>
            <div className="text-[11px] text-blue-900 leading-relaxed">
              Files are processed locally for spatial geometry extraction and statutory clause alignment.
            </div>
          </div>

          <div className="mt-2 flex items-center justify-end gap-2.5">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-xs text-[#64748B] hover:text-[#0F172A]"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={!selectedFile}
              onClick={handleIngest}
              className="px-4 py-2 bg-[#1D4ED8] hover:bg-[#1E40AF] disabled:bg-slate-200 disabled:text-slate-400 text-white rounded text-xs font-semibold transition-colors shadow-sm"
            >
              Ingest &amp; Extract
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
