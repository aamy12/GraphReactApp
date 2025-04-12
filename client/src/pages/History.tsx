import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { historyAPI, fileAPI } from "@/lib/api";
import { QueryResponse, FileInfo } from "@/types";
import ResponseDisplay from "@/components/ResponseDisplay";

export default function History() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedQuery, setSelectedQuery] = useState<QueryResponse | null>(null);
  
  // Fetch query history
  const { data: queries, isLoading: isQueriesLoading } = useQuery({
    queryKey: ['/api/history'],
    staleTime: 30000, // 30 seconds
  });
  
  // Fetch file history
  const { data: files, isLoading: isFilesLoading } = useQuery({
    queryKey: ['/api/files'],
    staleTime: 30000, // 30 seconds
  });
  
  // Filter queries based on search term
  const filteredQueries = queries?.filter((query: QueryResponse) =>
    query.query.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Filter files based on search term
  const filteredFiles = files?.filter((file: FileInfo) =>
    file.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  // Handle query selection
  const handleQuerySelect = (query: QueryResponse) => {
    setSelectedQuery(query);
  };

  return (
    <div className="container mx-auto p-4 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>History</CardTitle>
          <CardDescription>
            View your past queries and uploaded files
          </CardDescription>
          <div className="relative">
            <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search history..."
              className="pl-8"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="queries">
            <TabsList className="grid w-full grid-cols-2 mb-4">
              <TabsTrigger value="queries">Queries</TabsTrigger>
              <TabsTrigger value="files">Files</TabsTrigger>
            </TabsList>
            
            <TabsContent value="queries">
              {isQueriesLoading ? (
                <p className="text-center py-4">Loading queries...</p>
              ) : filteredQueries?.length > 0 ? (
                <div className="space-y-4">
                  {filteredQueries.map((query: QueryResponse) => (
                    <div
                      key={query.id}
                      className={`p-4 rounded-md border cursor-pointer transition-colors ${
                        selectedQuery?.id === query.id
                          ? "border-primary bg-muted"
                          : "hover:bg-muted/50"
                      }`}
                      onClick={() => handleQuerySelect(query)}
                    >
                      <p className="font-medium truncate">{query.query}</p>
                      <p className="text-sm text-muted-foreground mt-1 truncate">
                        {query.response?.substring(0, 100)}...
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  {searchTerm
                    ? "No matching queries found."
                    : "You haven't made any queries yet."}
                </p>
              )}
            </TabsContent>
            
            <TabsContent value="files">
              {isFilesLoading ? (
                <p className="text-center py-4">Loading files...</p>
              ) : filteredFiles?.length > 0 ? (
                <div className="space-y-4">
                  {filteredFiles.map((file: FileInfo) => (
                    <div
                      key={file.id}
                      className="p-4 rounded-md border hover:bg-muted/50 transition-colors"
                    >
                      <div className="flex justify-between items-center">
                        <div>
                          <p className="font-medium truncate">{file.filename}</p>
                          <p className="text-sm text-muted-foreground mt-1">
                            {(file.size / 1024).toFixed(2)} KB
                          </p>
                        </div>
                        <div>
                          <span
                            className={`px-2 py-1 rounded-full text-xs ${
                              file.processed
                                ? "bg-green-100 text-green-800"
                                : "bg-yellow-100 text-yellow-800"
                            }`}
                          >
                            {file.processed ? "Processed" : "Pending"}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-8 text-muted-foreground">
                  {searchTerm
                    ? "No matching files found."
                    : "You haven't uploaded any files yet."}
                </p>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
      
      {/* Display selected query */}
      {selectedQuery && (
        <ResponseDisplay response={selectedQuery} />
      )}
    </div>
  );
}
