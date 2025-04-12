import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import NotFound from "@/pages/not-found";
import Home from "@/pages/Home";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import History from "@/pages/History";
import Settings from "@/pages/Settings";
import Layout from "@/components/Layout";
import { useState, useEffect } from "react";
import { useLocation } from "wouter";

function Router() {
  // For demo purposes, we'll bypass authentication
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [, setLocation] = useLocation();

  useEffect(() => {
    // In a real app, we'd check for token validity here
    const token = localStorage.getItem('token');
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setIsAuthenticated(false);
    setLocation('/login');
  };

  // For development, always render the main app
  return (
    <Switch>
      <Route path="/">
        <Layout onLogout={handleLogout}>
          <Dashboard />
        </Layout>
      </Route>
      <Route path="/login">
        <Login setIsAuthenticated={setIsAuthenticated} />
      </Route>
      <Route path="/register">
        <Register setIsAuthenticated={setIsAuthenticated} />
      </Route>
      <Route path="/dashboard">
        <Layout onLogout={handleLogout}>
          <Dashboard />
        </Layout>
      </Route>
      <Route path="/history">
        <Layout onLogout={handleLogout}>
          <History />
        </Layout>
      </Route>
      <Route path="/settings">
        <Layout onLogout={handleLogout}>
          <Settings />
        </Layout>
      </Route>
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
