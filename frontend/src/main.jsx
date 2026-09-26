import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Zyntrix React Application Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-sans">
          <div className="max-w-lg w-full bg-white border border-slate-200 rounded-2xl p-8 shadow-xl text-center space-y-4">
            <div className="w-12 h-12 rounded-xl bg-red-50 border border-red-200 text-red-600 flex items-center justify-center mx-auto">
              <span className="material-symbols-outlined text-2xl">error_outline</span>
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Application Render Notice</h2>
              <p className="text-xs text-slate-500 mt-1">
                A client-side initialization state caused an error:
              </p>
            </div>
            <pre className="text-left text-[11px] bg-slate-900 text-emerald-400 p-3 rounded-lg overflow-x-auto font-mono max-h-48 whitespace-pre-wrap">
              {this.state.error?.toString()}
            </pre>
            <div className="flex items-center justify-center gap-2 pt-2">
              <button
                type="button"
                onClick={() => {
                  localStorage.removeItem('zyntrix_active_tab');
                  localStorage.removeItem('zyntrix_active_assessment_id');
                  window.location.reload();
                }}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition cursor-pointer"
              >
                Reset Session &amp; Reload
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);
