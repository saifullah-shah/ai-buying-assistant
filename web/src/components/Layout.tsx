import { useEffect, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";
import { useSession } from "../state/SessionContext";
import { ToastRegion } from "./Overlays";

function Mark() {
  return (
    <span className="brand__mark" aria-hidden="true">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
        <path
          d="M4 7.5 12 3l8 4.5v9L12 21l-8-4.5v-9Z"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinejoin="round"
        />
        <path d="M12 12v9M4 7.5l8 4.5 8-4.5" stroke="currentColor" strokeWidth="1.6" />
      </svg>
    </span>
  );
}

export function Header() {
  const { compare, saved } = useSession();
  const [open, setOpen] = useState(false);
  const location = useLocation();

  // Close the mobile menu whenever the route changes.
  useEffect(() => setOpen(false), [location.pathname, location.search]);

  const link = ({ isActive }: { isActive: boolean }) =>
    isActive ? "site-nav__link" : "site-nav__link";

  return (
    <header className="site-header">
      <div className="shell site-header__inner">
        <Link to="/" className="brand">
          <Mark />
          <span className="brand__text">
            <span className="brand__name">The Buying Studio</span>
            <span className="brand__tag">Decision assistant</span>
          </span>
        </Link>

        <button
          type="button"
          className="nav-toggle"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
          aria-controls="primary-nav"
          aria-label={open ? "Close main menu" : "Open main menu"}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            {open ? (
              <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            ) : (
              <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            )}
          </svg>
        </button>

        <nav id="primary-nav" className="site-nav" data-open={open} aria-label="Main">
          <NavLink to="/" end className={link}>
            Home
          </NavLink>
          <NavLink to="/discover" className={link}>
            Find a laptop
          </NavLink>
          <NavLink to="/compare" className={link}>
            Compare
            {compare.length > 0 ? (
              <span className="site-nav__count" aria-hidden="true">
                {compare.length}
              </span>
            ) : null}
            {compare.length > 0 ? <span className="sr-only"> items selected</span> : null}
          </NavLink>
          <NavLink to="/saved" className={link}>
            Saved
            {saved.length > 0 ? (
              <span className="site-nav__count" aria-hidden="true">
                {saved.length}
              </span>
            ) : null}
            {saved.length > 0 ? <span className="sr-only"> items saved</span> : null}
          </NavLink>
        </nav>
      </div>
      <ToastRegion />
    </header>
  );
}

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="shell site-footer__grid">
        <div>
          <p className="eyebrow">The Buying Studio</p>
          <p className="small muted" style={{ maxWidth: "42ch" }}>
            A buying decision assistant that filters against your real budget first, then
            explains what each remaining option gives up. Built on deterministic constraint
            checks with traceable evidence.
          </p>
          <p className="xsmall muted" style={{ marginTop: "var(--space-4)" }}>
            Demonstration build — every product, price and seller shown is synthetic.
          </p>
        </div>

        <div>
          <h3>Explore</h3>
          <ul>
            <li><Link to="/discover">Find a laptop</Link></li>
            <li><Link to="/compare">Comparison studio</Link></li>
            <li><Link to="/saved">Saved items</Link></li>
          </ul>
        </div>

        <div>
          <h3>How it works</h3>
          <ul>
            <li><Link to="/discover">Hard constraints first</Link></li>
            <li><Link to="/discover">Deterministic scoring</Link></li>
            <li><Link to="/discover">Grounded explanations</Link></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}

export function DemoNotice({ notice }: { notice?: string }) {
  return (
    <div className="demo-notice" role="note">
      <span className="demo-notice__icon" aria-hidden="true">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.7" />
          <path d="M12 8v5M12 16h.01" stroke="currentColor" strokeWidth="1.9" strokeLinecap="round" />
        </svg>
      </span>
      <span>
        <strong>Demonstration data.</strong>{" "}
        {notice ??
          "Every product, specification, price and seller below is synthetic and illustrative. None is a real listing, verified market price or live stock status."}
      </span>
    </div>
  );
}