import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'

// Global Error Handler
window.onerror = function (message, source, lineno, colno, error) {
  const root = document.getElementById('root');
  if (root) {
    root.innerHTML = `
      <div style="color: red; padding: 20px; font-family: monospace;">
        <h1>Runtime Error</h1>
        <h3>${message}</h3>
        <p>${source}:${lineno}:${colno}</p>
        <pre>${error?.stack}</pre>
      </div>
    `;
  }
};

window.onunhandledrejection = function (event) {
  const root = document.getElementById('root');
  if (root) {
    root.innerHTML = `
        <div style="color: red; padding: 20px; font-family: monospace;">
            <h1>Unhandled Promise Rejection</h1>
            <pre>${event.reason}</pre>
        </div>
        `;
  }
};

try {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
} catch (e) {
  console.error("Mount Error", e);
  const root = document.getElementById('root');
  if (root && e instanceof Error) {
    root.innerHTML = `<h1 style="color:red">Mount Error: ${e.message}</h1><pre>${e.stack}</pre>`;
  }
}
