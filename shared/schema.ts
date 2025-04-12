import { pgTable, text, serial, integer, boolean, timestamp, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// User model
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
  email: text("email").notNull().unique(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Knowledge Graph Nodes
export const nodes = pgTable("nodes", {
  id: serial("id").primaryKey(),
  label: text("label").notNull(),
  properties: jsonb("properties").notNull(),
  userId: integer("user_id").references(() => users.id).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// Knowledge Graph Relationships
export const relationships = pgTable("relationships", {
  id: serial("id").primaryKey(),
  type: text("type").notNull(),
  startNodeId: integer("start_node_id").references(() => nodes.id).notNull(),
  endNodeId: integer("end_node_id").references(() => nodes.id).notNull(),
  properties: jsonb("properties").notNull(),
  userId: integer("user_id").references(() => users.id).notNull(),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

// User Queries
export const queries = pgTable("queries", {
  id: serial("id").primaryKey(),
  text: text("text").notNull(),
  userId: integer("user_id").references(() => users.id).notNull(),
  response: text("response"),
  responseGraph: jsonb("response_graph"),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

// Files uploaded by users
export const files = pgTable("files", {
  id: serial("id").primaryKey(),
  filename: text("filename").notNull(),
  originalName: text("original_name").notNull(),
  mimeType: text("mime_type").notNull(),
  size: integer("size").notNull(),
  userId: integer("user_id").references(() => users.id).notNull(),
  processed: boolean("processed").default(false).notNull(),
  uploadedAt: timestamp("uploaded_at").defaultNow().notNull(),
});

// Create insert schemas
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
  email: true,
});

export const insertNodeSchema = createInsertSchema(nodes).pick({
  label: true,
  properties: true,
  userId: true,
});

export const insertRelationshipSchema = createInsertSchema(relationships).pick({
  type: true,
  startNodeId: true,
  endNodeId: true,
  properties: true,
  userId: true,
});

export const insertQuerySchema = createInsertSchema(queries).pick({
  text: true,
  userId: true,
});

export const insertFileSchema = createInsertSchema(files).pick({
  filename: true,
  originalName: true,
  mimeType: true,
  size: true,
  userId: true,
});

// Define types
export type User = typeof users.$inferSelect;
export type InsertUser = z.infer<typeof insertUserSchema>;

export type Node = typeof nodes.$inferSelect;
export type InsertNode = z.infer<typeof insertNodeSchema>;

export type Relationship = typeof relationships.$inferSelect;
export type InsertRelationship = z.infer<typeof insertRelationshipSchema>;

export type Query = typeof queries.$inferSelect;
export type InsertQuery = z.infer<typeof insertQuerySchema>;

export type File = typeof files.$inferSelect;
export type InsertFile = z.infer<typeof insertFileSchema>;

// Extended schemas for validation
export const loginSchema = z.object({
  username: z.string().min(1, "Username is required"),
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = insertUserSchema.extend({
  password: z.string().min(6, "Password must be at least 6 characters"),
  email: z.string().email("Invalid email address"),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
