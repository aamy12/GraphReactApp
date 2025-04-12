import { useState } from "react";
import { useQuery, QueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import FileUpload from "@/components/FileUpload";
import GraphVisualization from "@/components/GraphVisualization";
import QueryInput from "@/components/QueryInput";
import ResponseDisplay from "@/components/ResponseDisplay";
import { graphAPI, healthAPI } from "@/lib/api";
import { GraphData, QueryResponse, HealthStatus } from "@/types";

// Mock data for development
const MOCK_GRAPH_DATA: GraphData = {
  nodes: [
    { id: "1", label: "Person", name: "John Smith", properties: { age: 35, occupation: "Software Engineer" } },
    { id: "2", label: "Company", name: "Tech Corp", properties: { founded: 2005, location: "San Francisco" } },
    { id: "3", label: "Project", name: "Knowledge Graph App", properties: { startDate: "2023-01-15", status: "In Progress" } },
    { id: "4", label: "Skill", name: "Graph Databases", properties: { level: "Expert" } },
    { id: "5", label: "Person", name: "Jane Doe", properties: { age: 28, occupation: "Data Scientist" } },
    { id: "6", label: "Technology", name: "Neo4j", properties: { version: "4.4", type: "Graph Database" } }
  ],
  links: [
    { id: "1", source: "1", target: "2", type: "WORKS_AT", properties: { since: 2019, position: "Senior Developer" } },
    { id: "2", source: "1", target: "3", type: "CONTRIBUTES_TO", properties: { role: "Lead Developer" } },
    { id: "3", source: "1", target: "4", type: "HAS_SKILL", properties: { years: 5 } },
    { id: "4", source: "2", target: "3", type: "OWNS", properties: { investment: "$500K" } },
    { id: "5", source: "5", target: "2", type: "WORKS_AT", properties: { since: 2020, position: "Data Engineer" } },
    { id: "6", source: "5", target: "3", type: "CONTRIBUTES_TO", properties: { role: "Data Architect" } },
    { id: "7", source: "3", target: "6", type: "USES", properties: { version: "4.4.0" } }
  ]
};

const MOCK_HEALTH_STATUS: HealthStatus = {
  status: 'ok',
  neo4j: 'connected',
  llm: 'available'
};

const queryClient = new QueryClient();

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("query");
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  
  // Fetch graph overview with mock data
  const { data: graphOverview, isLoading: isGraphLoading, error: graphError } = useQuery({
    queryKey: ['/api/graph/overview'],
    staleTime: 30000, // 30 seconds
    queryFn: () => Promise.resolve({
      graphData: MOCK_GRAPH_DATA,
      stats: {
        nodeCount: MOCK_GRAPH_DATA.nodes.length,
        relationshipCount: MOCK_GRAPH_DATA.links.length
      }
    })
  });
  
  // Health check query with mock data
  const { data: healthStatus } = useQuery<HealthStatus>({
    queryKey: ['/api/health'],
    staleTime: 60000, // 1 minute
    queryFn: () => Promise.resolve(MOCK_HEALTH_STATUS)
  });

  // Handle file upload completion
  const handleFileUploadComplete = () => {
    // Invalidate the graph overview query to refresh the data
    queryClient.invalidateQueries({ queryKey: ['/api/graph/overview'] });
  };

  // Handle query submission with mock data
  const handleQuerySubmit = async (query: string) => {
    try {
      // Create a mock response instead of calling the API
      const mockResponse: QueryResponse = {
        id: 1,
        query: query,
        response: `# Response to "${query}"\n\nBased on the knowledge graph, here's what I found:\n\n* The query is related to ${MOCK_GRAPH_DATA.nodes.length} entities in the knowledge graph.\n* The most relevant connections are between people and projects.\n\n## Key Insights\n\n* John Smith works at Tech Corp and contributes to the Knowledge Graph App.\n* Jane Doe also works at Tech Corp as a Data Engineer.\n* The Knowledge Graph App uses Neo4j technology.\n* Both team members have complementary skills that help with the project development.`,
        graphData: {
          // Include a subset of the mock data to simulate a query-specific result
          nodes: MOCK_GRAPH_DATA.nodes.slice(0, 4),
          links: MOCK_GRAPH_DATA.links.slice(0, 3)
        }
      };
      
      // Set the response and switch tabs
      setQueryResponse(mockResponse);
      
      // Switch to query tab if not already active
      setActiveTab("query");
    } catch (error) {
      console.error("Query error:", error);
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <div className="flex flex-col md:flex-row gap-6">
        {/* Left column - Stats and health */}
        <div className="w-full md:w-1/4 space-y-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>Graph Statistics</CardTitle>
              <CardDescription>Your knowledge graph overview</CardDescription>
            </CardHeader>
            <CardContent>
              {isGraphLoading ? (
                <p>Loading statistics...</p>
              ) : graphError ? (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>
                    Failed to load graph statistics
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Nodes:</span>
                    <span className="font-medium">{graphOverview?.stats.nodeCount || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Relationships:</span>
                    <span className="font-medium">{graphOverview?.stats.relationshipCount || 0}</span>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle>System Status</CardTitle>
              <CardDescription>Connection status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">Database:</span>
                  {healthStatus?.neo4j === "connected" ? (
                    <span className="text-green-500 text-sm font-medium flex items-center">
                      <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
                      Connected
                    </span>
                  ) : (
                    <span className="text-red-500 text-sm font-medium flex items-center">
                      <span className="h-2 w-2 rounded-full bg-red-500 mr-2"></span>
                      Disconnected
                    </span>
                  )}
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">AI Service:</span>
                  {healthStatus?.llm === "available" ? (
                    <span className="text-green-500 text-sm font-medium flex items-center">
                      <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
                      Available
                    </span>
                  ) : (
                    <span className="text-yellow-500 text-sm font-medium flex items-center">
                      <span className="h-2 w-2 rounded-full bg-yellow-500 mr-2"></span>
                      Limited
                    </span>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Right column - Main content */}
        <div className="w-full md:w-3/4">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="query">Query Knowledge</TabsTrigger>
              <TabsTrigger value="upload">Upload Data</TabsTrigger>
            </TabsList>
            
            <TabsContent value="query" className="space-y-4 mt-4">
              <QueryInput onSubmit={handleQuerySubmit} />
              
              {queryResponse && (
                <ResponseDisplay response={queryResponse} />
              )}
              
              {!queryResponse && graphOverview?.graphData && (
                <Card>
                  <CardHeader>
                    <CardTitle>Your Knowledge Graph</CardTitle>
                    <CardDescription>
                      Visualizing your current knowledge graph
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="h-[500px]">
                    <GraphVisualization data={graphOverview.graphData as GraphData} />
                  </CardContent>
                </Card>
              )}
            </TabsContent>
            
            <TabsContent value="upload" className="space-y-4 mt-4">
              <FileUpload onComplete={handleFileUploadComplete} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
