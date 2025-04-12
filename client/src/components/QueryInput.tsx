import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { Search, Book, Lightbulb } from "lucide-react";

interface QueryInputProps {
  onSubmit: (query: string) => void;
}

export default function QueryInput({ onSubmit }: QueryInputProps) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async () => {
    if (!query.trim()) {
      toast({
        title: "Empty query",
        description: "Please enter a question to search your knowledge graph",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      await onSubmit(query);
      // Don't reset the query text after submission
    } catch (error) {
      toast({
        title: "Query failed",
        description: "An error occurred while processing your query",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const exampleQueries = [
    "What are the main concepts in my knowledge graph?",
    "How are entities related to each other?",
    "What information do I have about [specific entity]?",
  ];

  const handleExampleClick = (example: string) => {
    setQuery(example);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ask a Question</CardTitle>
        <CardDescription>
          Query your knowledge graph using natural language
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Textarea
            placeholder="Enter your question here..."
            className="min-h-[100px] resize-none"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) {
                handleSubmit();
              }
            }}
          />
          
          <div>
            <p className="text-sm text-muted-foreground mb-2 flex items-center">
              <Lightbulb className="h-3 w-3 mr-1" />
              Example queries:
            </p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((example, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => handleExampleClick(example)}
                  className="text-xs"
                >
                  {example}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
      <CardFooter className="justify-between">
        <p className="text-xs text-muted-foreground">
          <Book className="h-3 w-3 inline mr-1" />
          Tip: Press Ctrl+Enter to submit
        </p>
        <Button onClick={handleSubmit} disabled={isLoading}>
          {isLoading ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent"></div>
              Processing...
            </>
          ) : (
            <>
              <Search className="mr-2 h-4 w-4" />
              Search
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  );
}
