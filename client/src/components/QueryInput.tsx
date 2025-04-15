import { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { Search, Sparkles, Brain } from "lucide-react";

interface QueryInputProps {
  onSubmit: (query: string) => void;
  loading?: boolean;
  defaultQuery?: string;
}

export default function QueryInput({ onSubmit, loading = false, defaultQuery = "" }: QueryInputProps) {
  const [query, setQuery] = useState(defaultQuery);
  const { toast } = useToast();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim()) {
      toast({
        title: "Query required",
        description: "Please enter a question to search your knowledge graph",
        variant: "destructive"
      });
      return;
    }

    onSubmit(query);
  };

  const exampleQueries = [
    "Who is the CEO of Microsoft?",
    "What companies are located in San Francisco?",
    "What is the relationship between Tesla and SpaceX?",
    "When was the last board meeting?",
    "What are the key points in the quarterly report?"
  ];

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <Card className="glass-panel w-full">
      <CardHeader className="space-y-2">
        <CardTitle className="text-2xl font-bold bg-gradient-to-br from-secondary to-primary bg-clip-text text-transparent">Query Knowledge Graph</CardTitle>
        <CardDescription className="text-base">Ask a question about your uploaded documents</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleSubmit} className="space-y-4">
          <Textarea
            placeholder="What would you like to know about your documents?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="min-h-[80px] resize-none"
          />
          <div className="flex items-center justify-end">
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Sparkles className="mr-2 h-4 w-4 animate-pulse" />
                  Processing...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search Knowledge
                </>
              )}
            </Button>
          </div>
        </form>

        <div className="mt-6">
          <h3 className="text-sm font-medium mb-2">Example questions:</h3>
          <div className="flex flex-wrap gap-2">
            {exampleQueries.map((example) => (
              <Button
                key={example}
                variant="outline"
                size="sm"
                onClick={() => handleExampleClick(example)}
                className="text-xs h-auto py-1"
              >
                {example}
              </Button>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}