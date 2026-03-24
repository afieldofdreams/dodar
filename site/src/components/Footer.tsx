export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-left">
          <strong>DODAR</strong> — Structured reasoning for AI agents.
          Created by <a href="mailto:adam@crox.io">Adam Field</a>.
          <div className="powered-by">
            Powered by <a href="https://crox.io" target="_blank" rel="noopener noreferrer">Crox</a>
          </div>
        </div>
        <div className="footer-links">
          <a href="https://github.com/afieldofdreams/dodar" target="_blank" rel="noopener noreferrer">GitHub</a>
          <a href="https://www.linkedin.com/in/afieldio" target="_blank" rel="noopener noreferrer">LinkedIn</a>
          <a href="mailto:adam@crox.io">Contact</a>
        </div>
      </div>
    </footer>
  );
}
