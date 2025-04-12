// User types
export interface User {
  id: number;
  username: string;
  email: string;
}

export interface AuthResponse {
  message: string;
  user: User;
  token: string;
}

// Graph types
export interface Node {
  id: string;
  label: string;
  name: string;
  properties: Record<string, any>;
}

export interface Link {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: Node[];
  links: Link[];
}

export interface GraphStats {
  nodeCount: number;
  relationshipCount: number;
}

export interface GraphOverview {
  graphData: GraphData;
  stats: GraphStats;
}

// Query types
export interface QueryResponse {
  id: number;
  query: string;
  response: string;
  graphData: GraphData;
}

// File types
export interface FileInfo {
  id: number;
  filename: string;
  mimeType: string;
  size: number;
  processed: boolean;
}

export interface FileUploadResponse {
  message: string;
  file: {
    id: number;
    name: string;
    size: number;
  };
  graph: {
    nodesCreated: number;
    relationshipsCreated: number;
    graphData: GraphData;
  };
}

// Health check
export interface HealthStatus {
  status: 'ok' | 'error';
  neo4j: 'connected' | 'disconnected';
  llm: 'available' | 'unavailable';
}
