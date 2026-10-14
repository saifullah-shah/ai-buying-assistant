import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="shell page">
      <div className="state" style={{ marginTop: "var(--space-12)" }}>
        <span className="state__icon" aria-hidden="true">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6" />
            <path d="M9.5 9.5a2.6 2.6 0 1 1 3.4 2.5c-.6.2-.9.8-.9 1.4v.4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            <path d="M12 17h.01" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
          </svg>
        </span>
        <h1 style={{ fontSize: "var(--text-xl)" }}>That page does not exist</h1>
        <p className="state__body">
          The link may be out of date, or the product may not be part of the demonstration
          catalogue.
        </p>
        <div className="cluster" style={{ justifyContent: "center" }}>
          <Link to="/" className="btn btn--secondary btn--sm">
            Home
          </Link>
          <Link to="/discover" className="btn btn--primary btn--sm">
            Find a laptop
          </Link>
        </div>
      </div>
    </div>
  );
}