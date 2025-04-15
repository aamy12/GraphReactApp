import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { useEffect, useState } from "react";
import { useLocation } from "wouter";

export default function Home() {
  const [, setLocation] = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  
  useEffect(() => {
    // Check if user is already authenticated
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);
  
  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      setLocation('/dashboard');
    }
  }, [isAuthenticated, setLocation]);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="container mx-auto px-4 py-6 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-primary">Knowledge Graph Explorer</h1>
        <div className="space-x-4">
          <Button variant="outline" asChild>
            <Link href="/login">Login</Link>
          </Button>
          <Button asChild>
            <Link href="/register">Register</Link>
          </Button>
        </div>
      </header>

      {/* Hero section */}
      <section className="relative py-32 container mx-auto px-4 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10 -z-10" />
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] -z-10" />
        <div className="flex flex-col md:flex-row gap-12 items-center">
          <div className="md:w-1/2 space-y-8">
            <div className="inline-flex items-center rounded-full border px-4 py-1.5 text-sm font-medium bg-background/30 backdrop-blur-sm">
              <span className="flex h-2 w-2 rounded-full bg-primary mr-2" />
              Knowledge Graph Explorer
            </div>
            <h2 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
              Explore Knowledge with Natural Language
            </h2>
            <p className="text-xl text-muted-foreground leading-relaxed">
              Transform your documents into interactive knowledge graphs. Query your data using natural language and discover insights through AI-powered visualization.
            </p>
            <div className="flex gap-4 pt-4">
              <Button size="lg" className="h-12 px-8 text-base" asChild>
                <Link href="/register">Get Started Free</Link>
              </Button>
              <Button size="lg" variant="outline" className="h-12 px-8 text-base group" asChild>
                <Link href="/login">
                  Sign In
                  <span className="ml-2 transition-transform group-hover:translate-x-1">→</span>
                </Link>
              </Button>
            </div>
          </div>
          <div className="md:w-1/2 flex justify-center">
            <div className="relative w-full h-[500px] rounded-xl border bg-background/50 backdrop-blur-sm shadow-2xl overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-primary/10" />
              <div className="relative w-full h-full flex items-center justify-center p-8">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="w-full h-full max-w-[300px] text-primary/80">
                  <circle cx="12" cy="6" r="4"></circle>
                  <circle cx="6" cy="17" r="3"></circle>
                  <circle cx="18" cy="17" r="3"></circle>
                  <line x1="12" y1="10" x2="6" y2="14"></line>
                  <line x1="12" y1="10" x2="18" y2="14"></line>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features section */}
      <section className="py-16 bg-muted">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Key Features</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="bg-card p-6 rounded-lg shadow-sm">
              <div className="mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2">Document Upload & Processing</h3>
              <p className="text-muted-foreground">Upload documents and automatically extract entities and relationships to build your knowledge graph.</p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm">
              <div className="mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="2" y1="12" x2="22" y2="12"></line>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2">Interactive Visualization</h3>
              <p className="text-muted-foreground">Explore your knowledge graph through interactive visualizations to discover connections and insights.</p>
            </div>
            <div className="bg-card p-6 rounded-lg shadow-sm">
              <div className="mb-4">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-primary">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </div>
              <h3 className="text-xl font-bold mb-2">Natural Language Queries</h3>
              <p className="text-muted-foreground">Ask questions in plain English and get answers with visual evidence from your knowledge graph.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>© 2023 Knowledge Graph Explorer. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
