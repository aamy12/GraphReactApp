import { users, type User, type InsertUser } from "@shared/schema";

// modify the interface with any CRUD methods
// you might need

export interface IStorage {
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private nodes: Map<string, any>;
  private relationships: Map<string, any>;
  currentId: number;

  constructor() {
    this.users = new Map();
    this.nodes = new Map();
    this.relationships = new Map();
    this.currentId = 1;
  }

  // Add methods for graph operations
  addNode(node: any): void {
    this.nodes.set(node.id, node);
  }

  addRelationship(rel: any): void {
    this.relationships.set(rel.id, rel);
  }

  getNodes(): any[] {
    return Array.from(this.nodes.values());
  }

  getRelationships(): any[] {
    return Array.from(this.relationships.values());
  }

  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }
}

export const storage = new MemStorage();
