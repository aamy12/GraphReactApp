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
import Layout from "@/components/Layout";
import { useState, useEffect } from "react";
import { useLocation } from "wouter";

function Router() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [, setLocation] = useLocation();

  useEffect(() => {
    // Check for token on initial load
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

  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/login">
        <Login setIsAuthenticated={setIsAuthenticated} />
      </Route>
      <Route path="/register">
        <Register setIsAuthenticated={setIsAuthenticated} />
      </Route>
      <Route path="/dashboard">
        {isAuthenticated ? (
          <Layout onLogout={handleLogout}>
            <Dashboard />
          </Layout>
        ) : (
          <Login setIsAuthenticated={setIsAuthenticated} />
        )}
      </Route>
      <Route path="/history">
        {isAuthenticated ? (
          <Layout onLogout={handleLogout}>
            <History />
          </Layout>
        ) : (
          <Login setIsAuthenticated={setIsAuthenticated} />
        )}
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
