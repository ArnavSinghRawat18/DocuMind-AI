import Header from '../components/Header';
import Hero from '../components/Hero';
import Features from '../components/Features';
import HowItWorks from '../components/HowItWorks';
import DemoPanel from '../components/DemoPanel';
import Footer from '../components/Footer';

/**
 * Landing page - Main entry point for DocuMind AI
 * Renders all sections in semantic structure
 */
export default function Landing() {
  const handleDemoStarted = (jobId) => {
    // Navigate to dashboard or show status
    console.log('[Landing] Demo started with jobId:', jobId);
  };

  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900 transition-colors duration-300">
      <Header />
      
      <main className="flex-1">
        <section id="hero" aria-label="Hero section">
          <Hero />
        </section>

        <section id="features" aria-label="Features section">
          <Features />
        </section>

        <section id="how-it-works" aria-label="How it works section">
          <HowItWorks />
        </section>

        <section id="demo" aria-label="Demo section">
          <DemoPanel onStarted={handleDemoStarted} />
        </section>
      </main>

      <Footer />
    </div>
  );
}
