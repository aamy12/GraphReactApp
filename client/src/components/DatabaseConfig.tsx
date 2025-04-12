import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Database, ServerOff, RefreshCw } from "lucide-react";
import axios from "axios";

export default function DatabaseConfig() {
  const [useInMemory, setUseInMemory] = useState(true);
  const [loading, setLoading] = useState(false);
  const [neo4jURI, setNeo4jURI] = useState("");
  const [neo4jUser, setNeo4jUser] = useState("");
  const [neo4jPassword, setNeo4jPassword] = useState("");
  const [connected, setConnected] = useState(false);
  const { toast } = useToast();

  const handleSaveConfig = async () => {
    setLoading(true);
    try {
      // Update environment variables (only in-memory for now)
      await axios.post("/api/db-config", {
        useInMemory
      });

      toast({
        title: "Database configuration updated",
        description: `Using ${useInMemory ? "in-memory" : "Neo4j"} database`,
      });

      // Check connection status
      const healthResponse = await axios.get("/api/health");
      setConnected(healthResponse.data.neo4j === "connected");
    } catch (error) {
      console.error("Error updating database config:", error);
      toast({
        title: "Configuration error",
        description: "Failed to update database configuration",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Database className="mr-2 h-5 w-5" />
          Database Configuration
        </CardTitle>
        <CardDescription>
          Configure how the application stores and processes graph data
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between border p-4 rounded-md">
          <div className="space-y-0.5">
            <Label htmlFor="use-memory">Use In-Memory Database</Label>
            <p className="text-sm text-muted-foreground">
              {useInMemory
                ? "Using built-in memory database (no persistence between restarts)"
                : "Using Neo4j database (requires connection details)"
              }
            </p>
          </div>
          <Switch
            id="use-memory"
            checked={useInMemory}
            onCheckedChange={setUseInMemory}
          />
        </div>

        {/* Neo4j connection details - disabled for now */}
        <div className={useInMemory ? "opacity-50 pointer-events-none" : ""}>
          <div className="space-y-1 mb-2">
            <Label htmlFor="neo4j-uri">Neo4j URI</Label>
            <Input
              id="neo4j-uri"
              placeholder="bolt://localhost:7687"
              value={neo4jURI}
              onChange={(e) => setNeo4jURI(e.target.value)}
              disabled={useInMemory}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label htmlFor="neo4j-user">Username</Label>
              <Input
                id="neo4j-user"
                placeholder="neo4j"
                value={neo4jUser}
                onChange={(e) => setNeo4jUser(e.target.value)}
                disabled={useInMemory}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="neo4j-password">Password</Label>
              <Input
                id="neo4j-password"
                type="password"
                placeholder="••••••••"
                value={neo4jPassword}
                onChange={(e) => setNeo4jPassword(e.target.value)}
                disabled={useInMemory}
              />
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="flex items-center text-sm">
          {connected ? (
            <div className="text-green-500 flex items-center">
              <span className="h-2 w-2 rounded-full bg-green-500 mr-2"></span>
              Connected
            </div>
          ) : (
            <div className="text-amber-500 flex items-center">
              <ServerOff className="h-4 w-4 mr-1" />
              Not connected
            </div>
          )}
        </div>
        <Button onClick={handleSaveConfig} disabled={loading}>
          {loading ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Saving...
            </>
          ) : (
            "Save Configuration"
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}