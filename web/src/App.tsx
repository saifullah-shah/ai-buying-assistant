import { useEffect } from "react";
import { Route, Routes, useLocation } from "react-router-dom";
import { Footer, Header } from "./components/Layout";
import { LiveRegion } from "./components/LiveRegion";
import Home from "./routes/Home";
import Discover from "./routes/Discover";
import ProductDetail from "./routes/ProductDetail";
import Compare from "./routes/Compare";
import Saved from "./routes/Saved";
import NotFound from "./routes/NotFound";

/** Reset scroll and move focus to the main region on navigation (SPA a11y). */
function RouteChangeEffects() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
    const main = document.getElementById("main");
    // Give the new view a tick to render before moving focus.
    window.setTimeout(() => main?.focus({ preventScroll: true }), 0);
  }, [pathname]);
  return null;
}

export default function App() {
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to main content
      </a>
      <RouteChangeEffects />
      <LiveRegion />
      <Header />
      <main id="main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/discover" element={<Discover />} />
          <Route path="/product/:id" element={<ProductDetail />} />
          <Route path="/compare" element={<Compare />} />
          <Route path="/saved" element={<Saved />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
}