import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { QueryResponse } from "@/types";
import GraphVisualization from "@/components/GraphVisualization";

interface ResponseDisplayProps {
  response: QueryResponse;
}

export default function ResponseDisplay({ response }: ResponseDisplayProps) {
  // Format the response for better readability
  const formatResponse = (text: string) => {
    // Replace markdown-style headers with styled text
    let formatted = text.replace(/^# (.*$)/gm, '<h3 class="text-lg font-bold mt-4 mb-2">$1</h3>');
    formatted = formatted.replace(/^## (.*$)/gm, '<h4 class="text-md font-bold mt-3 mb-1">$1</h4>');
    
    // Replace markdown-style lists
    formatted = formatted.replace(/^\* (.*$)/gm, '<li class="ml-4 list-disc">$1</li>');
    
    // Replace markdown-style bold
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<span class="font-bold">$1</span>');
    
    // Replace markdown-style italic
    formatted = formatted.replace(/\*(.*?)\*/g, '<span class="italic">$1</span>');
    
    // Replace markdown-style code
    formatted = formatted.replace(/`(.*?)`/g, '<code class="px-1 py-0.5 bg-muted rounded text-sm">$1</code>');
    
    // Replace new lines with paragraph breaks
    formatted = formatted.replace(/\n\n/g, '</p><p class="my-2">');
    
    return `<p class="my-2">${formatted}</p>`;
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Response</CardTitle>
        <CardDescription>
          Query: {response.query}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="text">
          <TabsList className="grid w-full grid-cols-2 mb-4">
            <TabsTrigger value="text">Text Response</TabsTrigger>
            <TabsTrigger value="graph">Graph Visualization</TabsTrigger>
          </TabsList>
          
          <TabsContent value="text" className="min-h-[200px]">
            <div
              className="prose prose-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: formatResponse(response.response) }}
            />
          </TabsContent>
          
          <TabsContent value="graph" className="min-h-[400px]">
            <GraphVisualization data={response.graphData} />
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
