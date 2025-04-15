import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage, MemStorage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // put application routes here
  // prefix all routes with /api

  // use storage to perform CRUD operations on the storage interface
  // e.g. storage.insertUser(user) or storage.getUserByUsername(username)

  app.post('/api/db-config', async (req, res) => {
    try {
      const { useInMemory } = req.body;
      // Switch storage implementation based on configuration
      const memStorage = useInMemory ? new MemStorage() : storage;
      global.storage = memStorage;
      
      res.json({ 
        message: "Database configuration updated",
        config: { useInMemory, connected: true } 
      });
    } catch (error) {
      console.error("Database config error:", error);
      res.status(500).json({ error: error instanceof Error ? error.message : "Failed to update database configuration" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
