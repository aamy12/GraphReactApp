import { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { systemAPI, HealthCheckResponse } from "@/lib/api";
import { Database, Key, CheckCircle, AlertCircle, Settings as SettingsIcon } from "lucide-react";

export default function Settings() {
  const [activeTab, setActiveTab] = useState("database");
  const [useInMemory, setUseInMemory] = useState(true);
  const [openAiKey, setOpenAiKey] = useState("");
  const [dbConfigLoading, setDbConfigLoading] = useState(false);
  const [apiKeyLoading, setApiKeyLoading] = useState(false);
  const [healthStatus, setHealthStatus] = useState<HealthCheckResponse | null>(null);
  const { toast } = useToast();

  // Load health status and current settings on mount
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await systemAPI.health();
      setHealthStatus(response.data);
      
      // Update UI based on current settings
      // Check if we're using in-memory database based on db_type
      setUseInMemory(response.data.db_type === "in-memory");
    } catch (error) {
      console.error("Health check failed:", error);
      toast({
        title: "Error",
        description: "Failed to load system status information",
        variant: "destructive",
      });
    }
  };

  const updateDatabaseConfig = async () => {
    setDbConfigLoading(true);
    
    try {
      const response = await systemAPI.setDbConfig(useInMemory);
      
      if (response.data.config) {
        // Update local state to match server state
        setUseInMemory(response.data.config.useInMemory);
        
        toast({
          title: "Settings Updated",
          description: `Database mode set to ${response.data.config.useInMemory ? "in-memory" : "Neo4j"}.`,
        });
        
        // Update health status
        await checkHealth();
      } else {
        toast({
          title: "Error",
          description: "Failed to connect to database",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error("Failed to update database config:", error);
      toast({
        title: "Error",
        description: "Failed to update database configuration",
        variant: "destructive",
      });
    } finally {
      setDbConfigLoading(false);
    }
  };

  const saveApiKey = async () => {
    if (!openAiKey.trim()) {
      toast({
        title: "Error",
        description: "Please enter a valid API key",
        variant: "destructive",
      });
      return;
    }
    
    setApiKeyLoading(true);
    
    try {
      // Save the API key using the new endpoint
      const response = await systemAPI.setApiKey(openAiKey);
      
      toast({
        title: "API Key Updated",
        description: "Your OpenAI API key has been updated successfully.",
      });
      
      // Refresh health status
      await checkHealth();
    } catch (error) {
      console.error("Failed to save API key:", error);
      toast({
        title: "Error",
        description: "Failed to update API key",
        variant: "destructive",
      });
    } finally {
      setApiKeyLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2">
        <SettingsIcon className="h-6 w-6" />
        System Settings
      </h1>
      
      <Tabs 
        value={activeTab} 
        onValueChange={setActiveTab} 
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="database" className="flex items-center gap-1">
            <Database className="h-4 w-4" />
            <span>Database</span>
          </TabsTrigger>
          <TabsTrigger value="api" className="flex items-center gap-1">
            <Key className="h-4 w-4" />
            <span>API Keys</span>
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="database" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge Graph Database</CardTitle>
              <CardDescription>
                Configure how your knowledge graph data is stored
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center space-x-2">
                <Switch 
                  id="in-memory-mode" 
                  checked={useInMemory}
                  onCheckedChange={setUseInMemory}
                />
                <Label htmlFor="in-memory-mode">Use In-Memory Database</Label>
              </div>
              
              <div className="text-sm text-muted-foreground">
                {useInMemory ? (
                  <p>
                    In-memory mode stores data only for the current session. Your data will not persist
                    if the server restarts. This mode is ideal for testing and development.
                  </p>
                ) : (
                  <p>
                    Neo4j mode uses a persistent graph database. Your knowledge graph data
                    will be saved and available for future sessions.
                  </p>
                )}
              </div>
              
              {healthStatus && (
                <Alert 
                  variant={healthStatus.db_type === "neo4j" && healthStatus.neo4j === "connected" ? "default" : "warning"}
                  className="mt-4"
                >
                  {healthStatus.db_type === "neo4j" && healthStatus.neo4j === "connected" ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertTitle>
                    {healthStatus.db_type === "neo4j" && healthStatus.neo4j === "connected" 
                      ? "Neo4j Connected" 
                      : healthStatus.db_type === "neo4j"
                        ? "Neo4j Connection Failed"
                        : "Using In-Memory Database"}
                  </AlertTitle>
                  <AlertDescription>
                    {healthStatus.db_type === "neo4j" && healthStatus.neo4j === "connected"
                      ? "Your data is being stored in a persistent Neo4j database."
                      : healthStatus.db_type === "neo4j" 
                        ? "You've selected Neo4j database but the connection failed. Check your configuration or switch to in-memory mode."
                        : "Your data is currently stored in memory and will not persist after restart."}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter>
              <Button 
                onClick={updateDatabaseConfig} 
                disabled={dbConfigLoading}
              >
                {dbConfigLoading ? "Updating..." : "Update Database Settings"}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="api" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>API Configuration</CardTitle>
              <CardDescription>
                Configure API keys for external services
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="openai-key">OpenAI API Key</Label>
                <Input
                  id="openai-key"
                  type="password"
                  placeholder="sk-..."
                  value={openAiKey}
                  onChange={(e) => setOpenAiKey(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Your API key is required for advanced natural language processing features.
                  The key is stored securely and never shared.
                </p>
              </div>
              
              {healthStatus && (
                <Alert 
                  variant={healthStatus.openai_configured ? "default" : "warning"}
                  className="mt-4"
                >
                  {healthStatus.openai_configured ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <AlertTitle>
                    {healthStatus.openai_configured 
                      ? "OpenAI API Key Configured" 
                      : "OpenAI API Key Not Configured"}
                  </AlertTitle>
                  <AlertDescription>
                    {healthStatus.openai_configured
                      ? healthStatus.llm === "available"
                        ? "Your application is using enhanced natural language processing."
                        : "API key is set but the LLM service is not working properly."
                      : "Advanced natural language features require an OpenAI API key."}
                  </AlertDescription>
                </Alert>
              )}
            </CardContent>
            <CardFooter>
              <Button 
                onClick={saveApiKey}
                disabled={apiKeyLoading}
              >
                {apiKeyLoading ? "Saving..." : "Save API Key"}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}