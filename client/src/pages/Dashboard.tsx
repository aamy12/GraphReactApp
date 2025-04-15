import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { UploadCloud, Info, Database, AlertTriangle, History, BarChart, Search } from "lucide-react";
import { graphAPI, QueryResponse, systemAPI } from "@/lib/api";
import FileUpload from "@/components/FileUpload";
import QueryInput from "@/components/QueryInput";
import ResponseDisplay from "@/components/ResponseDisplay";
import GraphVisualization from "@/components/GraphVisualization";
import { GraphData, GraphOverview } from "@/types/graph";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("query");
  const [loading, setLoading] = useState(false);
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);
  const [graphOverview, setGraphOverview] = useState<GraphOverview | null>(null);
  const [healthStatus, setHealthStatus] = useState<{ neo4j: string; llm: string } | null>(null);
  const { toast } = useToast();

  // Load graph overview on mount
  useEffect(() => {
    loadGraphOverview();
    checkHealth();
  }, []);

  const loadGraphOverview = async () => {
    try {
      const response = await graphAPI.getOverview();
      
      // Ensure we have a valid structure even if the API returns incomplete data
      const safeOverview = {
        graphData: {
          nodes: [],
          links: [],
          ...(response.data?.graphData || {})
        },
        stats: {
          nodeCount: 0,
          relationshipCount: 0,
          ...(response.data?.stats || {})
        }
      };
      
      setGraphOverview(safeOverview);
    } catch (error) {
      console.error("Error loading graph overview:", error);
      
      // Set a default empty structure on error
      setGraphOverview({
        graphData: { nodes: [], links: [] },
        stats: { nodeCount: 0, relationshipCount: 0 }
      });
      
      toast({
        title: "Failed to load graph overview",
        description: "There was an error loading your knowledge graph data.",
        variant: "destructive",
      });
    }
  };

  const checkHealth = async () => {
    try {
      const response = await systemAPI.health();
      setHealthStatus({
        neo4j: response.data.neo4j,
        llm: response.data.llm,
      });
    } catch (error) {
      console.error("Health check failed:", error);
    }
  };

  const handleQuery = async (query: string) => {
    setLoading(true);
    
    try {
      const response = await graphAPI.query(query);
      setQueryResponse(response.data);
      
      // Refresh graph overview after query
      loadGraphOverview();
    } catch (error) {
      console.error("Query error:", error);
      toast({
        title: "Query Error",
        description: "There was an error processing your query. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUploadComplete = () => {
    // Refresh graph overview when upload completes
    loadGraphOverview();
    
    // Show success message
    toast({
      title: "Upload complete",
      description: "Your document has been processed and added to the knowledge graph.",
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-8 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Graph Dashboard</h1>
          <p className="text-muted-foreground mt-1">Explore and analyze your knowledge graph</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="text-xs">
            <History className="h-3 w-3 mr-1" />
            View History
          </Button>
          <Button variant="outline" size="sm" className="text-xs">
            <BarChart className="h-3 w-3 mr-1" />
            Analytics
          </Button>
        </div>
      </div>
      
      {/* System status alerts */}
      {healthStatus && (
        <div className="space-y-2">
          {healthStatus.neo4j !== "connected" && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Database Status</AlertTitle>
              <AlertDescription>
                The graph database is not connected. Using in-memory storage instead.
                Go to Settings to configure your database connection.
              </AlertDescription>
            </Alert>
          )}
          
          {healthStatus.llm !== "available" && (
            <Alert variant="warning">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>LLM Service Status</AlertTitle>
              <AlertDescription>
                The language model service is not available. Advanced natural language processing
                features will be limited. Go to Settings to configure your API key.
              </AlertDescription>
            </Alert>
          )}
        </div>
      )}
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left sidebar with graph overview */}
        <div className="lg:col-span-1 space-y-6">
          <div className="rounded-lg glass-panel p-6">
            <div className="flex items-center gap-2 mb-4">
              <Database className="h-5 w-5" />
              <h2 className="font-semibold">Knowledge Graph Overview</h2>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Entities</span>
                <span className="font-medium">{graphOverview?.stats?.nodeCount || 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Relationships</span>
                <span className="font-medium">{graphOverview?.stats?.relationshipCount || 0}</span>
              </div>
            </div>
            
            {/* Graph preview */}
            {graphOverview?.graphData?.nodes && graphOverview.graphData.nodes.length > 0 ? (
              <div className="mt-4 h-[300px] border rounded-md overflow-hidden">
                <GraphVisualization 
                  data={graphOverview.graphData}
                  height={300}
                  title=""
                  description=""
                />
              </div>
            ) : (
              <div className="mt-4 h-[300px] bg-muted/40 rounded-md flex items-center justify-center p-4 text-center text-muted-foreground">
                <div>
                  <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">
                    Your knowledge graph is empty. Upload documents to populate it.
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>
        
        {/* Main content area */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs 
            value={activeTab} 
            onValueChange={setActiveTab} 
            className="w-full"
          >
            <TabsList className="inline-flex h-12 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground w-full">
              <TabsTrigger value="query" className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-6 py-3 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm">
                <Search className="h-4 w-4 mr-2" />
                Query Knowledge
              </TabsTrigger>
              <TabsTrigger value="upload" className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-6 py-3 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm">
                <UploadCloud className="h-4 w-4 mr-2" />
                Upload Document
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="query" className="space-y-6 mt-6">
              <QueryInput 
                onSubmit={handleQuery}
                loading={loading}
              />
              
              {queryResponse && (
                <ResponseDisplay response={queryResponse} />
              )}
            </TabsContent>
            
            <TabsContent value="upload" className="mt-6">
              <FileUpload onComplete={handleUploadComplete} />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}