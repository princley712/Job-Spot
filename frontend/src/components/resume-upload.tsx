'use client';

import { useState, useRef } from 'react';
import { UploadCloud, FileText, Loader2, CheckCircle2, X } from 'lucide-react';

interface ResumeUploadProps {
  onUploadSuccess: () => void;
}

export function ResumeUpload({ onUploadSuccess }: ResumeUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      validateAndSetFile(droppedFile);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    setSuccess(false);
    
    const validTypes = ['application/pdf', 'text/plain'];
    if (!validTypes.includes(selectedFile.type)) {
      setError('Please upload a valid PDF or TXT file.');
      return;
    }
    
    // 5MB limit
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('File size exceeds 5MB limit.');
      return;
    }
    
    setFile(selectedFile);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('jwt_token') : null;
      const headers: HeadersInit = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch('http://localhost:8000/api/v1/resumes/upload', {
        method: 'POST',
        headers,
        body: formData,
      });

      if (res.ok) {
        setSuccess(true);
        setTimeout(() => {
          onUploadSuccess();
        }, 1500);
      } else {
        const data = await res.json();
        setError(data.detail || 'Upload failed. Please try again.');
      }
    } catch (err) {
      setError('Network error. Make sure the backend is running.');
    } finally {
      setIsUploading(false);
    }
  };

  const resetUpload = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      <div 
        className={`relative p-8 rounded-3xl border-2 border-dashed transition-all duration-200 ${
          isDragging 
            ? 'border-indigo-500 bg-indigo-50/50 dark:bg-indigo-500/10' 
            : 'border-slate-200 dark:border-slate-800 bg-white/50 dark:bg-slate-900/20 hover:border-slate-300 dark:hover:border-slate-700'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf,.txt"
          className="hidden"
        />

        {success ? (
          <div className="flex flex-col items-center justify-center text-center animate-in fade-in zoom-in duration-300 py-4">
            <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-500/20 flex items-center justify-center mb-4">
              <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
            </div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">Resume Uploaded!</h3>
            <p className="text-slate-500 dark:text-slate-400">Our AI is now scanning for matching jobs...</p>
          </div>
        ) : file ? (
          <div className="flex flex-col items-center text-center animate-in fade-in duration-200 py-2">
            <div className="w-16 h-16 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center mb-4 relative">
              <FileText className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
              {!isUploading && (
                <button 
                  onClick={resetUpload}
                  className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/50 dark:hover:text-red-400 flex items-center justify-center transition-colors text-slate-500 dark:text-slate-400"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white truncate max-w-xs mb-1">
              {file.name}
            </h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
              {(file.size / (1024 * 1024)).toFixed(2)} MB
            </p>
            
            <button
              onClick={handleUpload}
              disabled={isUploading}
              className="px-8 h-12 rounded-xl bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 font-semibold flex items-center gap-2 hover:shadow-lg hover:shadow-indigo-500/10 hover:-translate-y-0.5 transition-all disabled:opacity-70 disabled:hover:translate-y-0 disabled:cursor-not-allowed"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Analyzing Resume...
                </>
              ) : (
                'Start Matching'
              )}
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center text-center py-4">
            <div className="w-16 h-16 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-8 h-8 text-slate-400 dark:text-slate-500" />
            </div>
            <h3 className="text-xl font-medium text-slate-900 dark:text-white mb-2">Upload your resume</h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-sm mb-6">
              Drag and drop your PDF or TXT file here, or click to browse. We'll extract your skills automatically.
            </p>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-6 h-10 rounded-lg bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium hover:bg-indigo-100 dark:hover:bg-indigo-500/20 transition-colors"
            >
              Select File
            </button>
          </div>
        )}
      </div>
      
      {error && (
        <div className="mt-4 px-4 py-3 rounded-xl bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-600 dark:text-red-400 text-sm font-medium animate-in fade-in duration-200">
          {error}
        </div>
      )}
    </div>
  );
}
