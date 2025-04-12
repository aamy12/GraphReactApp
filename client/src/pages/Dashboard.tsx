import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
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

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("query");
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  
  // Fetch graph overview
  const { data: graphOverview, isLoading: isGraphLoading, error: graphError } = useQuery({
    queryKey: ['/api/graph/overview'],
    staleTime: 30000, // 30 seconds
  });
  
  // Health check query
  const { data: healthStatus } = useQuery<HealthStatus>({
    queryKey: ['/api/health'],
    staleTime: 60000, // 1 minute
  });

  // Handle file upload completion
  const handleFileUploadComplete = () => {
    // Invalidate the graph overview query to refresh the data
    queryClient.invalidateQueries({ queryKey: ['/api/graph/overview'] });
  };

  // Handle query submission
  const handleQuerySubmit = async (query: string) => {
    try {
      const response = await graphAPI.query(query);
      setQueryResponse(response.data);
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
