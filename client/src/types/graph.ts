// Graph data models
export interface Node {
  id: string;
  label: string;
  name: string;
  properties: Record<string, any>;
}

export interface Relationship {
  id: string;
  source: string;
  target: string;
  type: string;
  properties: Record<string, any>;
}

export interface GraphData {
  nodes: Node[];
  links: Relationship[];
}

export interface GraphStats {
  nodeCount: number;
  relationshipCount: number;
}

export interface GraphOverview {
  graphData: GraphData;
  stats: GraphStats;
}