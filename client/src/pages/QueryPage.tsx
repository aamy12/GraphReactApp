
import { useState } from "react";
import QueryInput from "@/components/QueryInput";
import ResponseDisplay from "@/components/ResponseDisplay";
import { QueryResponse } from "@/types";

export default function QueryPage() {
  const [loading, setLoading] = useState(false);
  const [queryResponse, setQueryResponse] = useState<QueryResponse | null>(null);

  const handleQuery = async (query: string) => {
    setLoading(true);
    try {
      const response = await graphAPI.query(query);
      setQueryResponse(response.data);
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

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Query Knowledge Graph</h1>
        <p className="text-muted-foreground mt-1">Ask questions about your knowledge base</p>
      </div>

      <div className="space-y-6">
        <QueryInput 
          onSubmit={handleQuery}
          loading={loading}
        />
        
        {queryResponse && (
          <ResponseDisplay response={queryResponse} />
        )}
      </div>
    </div>
  );
}
