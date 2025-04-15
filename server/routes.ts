import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";

export async function registerRoutes(app: Express): Promise<Server> {
  // put application routes here
  // prefix all routes with /api

  // use storage to perform CRUD operations on the storage interface
  // e.g. storage.insertUser(user) or storage.getUserByUsername(username)

  app.post('/api/db-config', async (req, res) => {
    try {
      const { useInMemory } = req.body;
      // Switch storage implementation based on configuration
      if (useInMemory) {
        const memStorage = new MemStorage();
        global.storage = memStorage;
      }
      res.json({ 
        message: "Database configuration updated",
        config: { useInMemory, connected: true } 
      });
    } catch (error) {
      res.status(500).json({ error: "Failed to update database configuration" });
    }
  });

  const httpServer = createServer(app);

  return httpServer;
}
