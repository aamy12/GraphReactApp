import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { UploadCloud, Info, Database, AlertTriangle, History, BarChart, Search } from "lucide-react";
import { graphAPI, QueryResponse, systemAPI } from "@/lib/api";
import FileUpload from "@/components/FileUpload";
import QueryInput from "@/components/QueryInput";
import ResponseDisplay from "@/components/ResponseDisplay";
import GraphVisualization from "@/components/GraphVisualization";
import { GraphData, GraphOverview } from "@/types/graph";
import { Card, CardContent } from "@/components/ui/card";


export default function Dashboard() {
  const [graphOverview, setGraphOverview] = useState<GraphOverview | null>(null);
  const [healthStatus, setHealthStatus] = useState<{ neo4j: string; llm: string } | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    loadGraphOverview();
    checkHealth();
  }, []);

  const loadGraphOverview = async () => {
    try {
      const response = await graphAPI.getOverview();
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

  return (
    <div className="container mx-auto p-6 space-y-8 min-h-screen">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Knowledge Graph Dashboard</h1>
          <p className="text-muted-foreground mt-1">Overview of your knowledge base</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="text-xs">
            <BarChart className="h-3 w-3 mr-1" />
            Analytics
          </Button>
        </div>
      </div>

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

      <Card className="glass-panel">
        <CardContent className="p-6 space-y-6">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            <h2 className="font-semibold">Knowledge Graph Overview</h2>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded-lg bg-muted/20">
              <div className="text-2xl font-bold">{graphOverview?.stats?.nodeCount || 0}</div>
              <div className="text-sm text-muted-foreground">Total Entities</div>
            </div>
            <div className="p-4 rounded-lg bg-muted/20">
              <div className="text-2xl font-bold">{graphOverview?.stats?.relationshipCount || 0}</div>
              <div className="text-sm text-muted-foreground">Total Relationships</div>
            </div>
          </div>

          {graphOverview?.graphData?.nodes && graphOverview.graphData.nodes.length > 0 ? (
            <div className="h-[400px] border rounded-md overflow-hidden">
              <GraphVisualization
                data={graphOverview.graphData}
                height={400}
                title=""
                description=""
              />
            </div>
          ) : (
            <div className="h-[400px] bg-muted/40 rounded-md flex items-center justify-center p-4 text-center">
              <div>
                <Info className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-muted-foreground">
                  Your knowledge graph is empty. Start by uploading documents.
                </p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}