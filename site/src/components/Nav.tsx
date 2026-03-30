import { Link, useLocation } from "react-router-dom";

export default function Nav() {
  const location = useLocation();
  const isActive = (path: string) => location.pathname === path ? "active" : "";

  return (
    <nav className="nav">
      <div className="nav-inner">
        <Link to="/" className="nav-logo">DODAR</Link>
        <div className="nav-links">
          <Link to="/framework" className={isActive("/framework")}>Framework</Link>
          <Link to="/research" className={isActive("/research")}>Research</Link>
          <Link to="/study" className={isActive("/study")}>Study</Link>
          <Link to="/about" className={isActive("/about")}>About</Link>
          <a href="https://github.com/afieldofdreams/dodar" target="_blank" rel="noopener noreferrer" className="github-link">GitHub</a>
        </div>
      </div>
    </nav>
  );
}
