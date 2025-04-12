import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, Network, Clock } from "lucide-react";
import { QueryResponse } from "@/lib/api";
import GraphVisualization from "./GraphVisualization";
import { format } from "date-fns";
import ReactMarkdown from "react-markdown";

interface ResponseDisplayProps {
  response: QueryResponse;
}

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  const [activeTab, setActiveTab] = useState("answer");
  
  // Format the timestamp
  const formattedTimestamp = response.timestamp
    ? format(new Date(response.timestamp), "MMM d, yyyy 'at' h:mm a")
    : "";

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center">
            <MessageSquare className="mr-2 h-5 w-5" />
            Query Results
          </CardTitle>
          {formattedTimestamp && (
            <Badge variant="outline" className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              <span className="text-xs">{formattedTimestamp}</span>
            </Badge>
          )}
        </div>
        <CardDescription>
          <span className="font-medium">Query:</span> {response.query}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="answer">Answer</TabsTrigger>
            <TabsTrigger value="graph">
              <div className="flex items-center">
                <Network className="mr-2 h-4 w-4" />
                Graph Visualization
              </div>
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="answer" className="space-y-4">
            <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown>
                {response.response || "No response available."}
              </ReactMarkdown>
            </div>
          </TabsContent>
          
          <TabsContent value="graph">
            <div className="h-[500px]">
              {response.graphData && response.graphData.nodes.length > 0 ? (
                <GraphVisualization 
                  data={response.graphData} 
                  height={500}
                  title="Knowledge Subgraph"
                  description="Visual representation of entities relevant to your query"
                />
              ) : (
                <div className="h-full flex items-center justify-center text-muted-foreground bg-muted/50 rounded-md">
                  No graph data available for this query
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}