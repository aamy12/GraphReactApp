import { useState } from "react";
import { useToast } from "@/hooks/use-toast";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Check, Key, RefreshCw, Settings as SettingsIcon } from "lucide-react";
import DatabaseConfig from "@/components/DatabaseConfig";
import axios from "axios";

export default function Settings() {
  const [activeTab, setActiveTab] = useState("database");
  const [apiKey, setApiKey] = useState("");
  const [savingKey, setSavingKey] = useState(false);
  const { toast } = useToast();

  // This is a stub - in a real app, we would actually set the API key
  const handleSaveApiKey = async () => {
    if (!apiKey) {
      toast({
        title: "API Key Required",
        description: "Please enter an OpenAI API key",
        variant: "destructive",
      });
      return;
    }

    setSavingKey(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real app, we would send the API key to the server
      // await axios.post("/api/settings/openai-key", { apiKey });
      
      toast({
        title: "API Key Saved",
        description: "Your OpenAI API key has been saved",
      });
    } catch (error) {
      console.error("Error saving API key:", error);
      toast({
        title: "Error Saving API Key",
        description: "There was an error saving your API key",
        variant: "destructive",
      });
    } finally {
      setSavingKey(false);
    }
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <h1 className="text-2xl font-bold flex items-center mb-6">
        <SettingsIcon className="mr-2 h-6 w-6" />
        Settings
      </h1>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2 mb-6">
          <TabsTrigger value="database">Database</TabsTrigger>
          <TabsTrigger value="api-keys">API Keys</TabsTrigger>
        </TabsList>
        
        <TabsContent value="database" className="space-y-4">
          <DatabaseConfig />
        </TabsContent>
        
        <TabsContent value="api-keys" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Key className="mr-2 h-5 w-5" />
                API Keys
              </CardTitle>
              <CardDescription>
                Manage API keys for external services
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="openai-key">OpenAI API Key</Label>
                <Input
                  id="openai-key"
                  type="password"
                  placeholder="sk-..."
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
                <p className="text-sm text-muted-foreground">
                  Required for advanced natural language processing features
                </p>
              </div>
            </CardContent>
            <CardFooter className="flex justify-end">
              <Button onClick={handleSaveApiKey} disabled={savingKey}>
                {savingKey ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Check className="mr-2 h-4 w-4" />
                    Save Key
                  </>
                )}
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}