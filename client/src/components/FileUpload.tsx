import { useState, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { useToast } from "@/hooks/use-toast";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { fileAPI } from "@/lib/api";
import { FileUploadResponse } from "@/types";
import { Upload, FileText, Check, X } from "lucide-react";
import GraphVisualization from "@/components/GraphVisualization";

interface FileUploadProps {
  onComplete: () => void;
}

export default function FileUpload({ onComplete }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<FileUploadResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  // File upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => {
      setUploading(true);
      // Simulate progress since XMLHttpRequest is not being used
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(progressInterval);
            return 95;
          }
          return prev + 5;
        });
      }, 100);
      
      return fileAPI.uploadFile(file)
        .then(response => {
          clearInterval(progressInterval);
          setUploadProgress(100);
          return response.data;
        })
        .finally(() => {
          setUploading(false);
        });
    },
    onSuccess: (data) => {
      setUploadResult(data);
      toast({
        title: "File uploaded successfully",
        description: `${data.file.name} has been processed.`,
      });
      onComplete();
    },
    onError: (error: any) => {
      toast({
        title: "Upload failed",
        description: error.response?.data?.message || "An error occurred during upload",
        variant: "destructive",
      });
    },
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadResult(null); // Clear previous results
    }
  };

  const handleUpload = () => {
    if (file) {
      setUploadProgress(0);
      uploadMutation.mutate(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setUploadResult(null); // Clear previous results
    }
  };

  const resetUpload = () => {
    setFile(null);
    setUploadResult(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Upload Data</CardTitle>
          <CardDescription>
            Upload files to build your knowledge graph
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center ${
              file ? "border-primary bg-primary/5" : "border-input"
            }`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            {!file ? (
              <div className="py-8">
                <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-2" />
                <p className="text-lg font-medium">Drag & drop file here</p>
                <p className="text-muted-foreground mb-4">
                  or click to browse files
                </p>
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                >
                  Browse Files
                </Button>
                <input
                  type="file"
                  ref={fileInputRef}
                  className="hidden"
                  onChange={handleFileChange}
                  accept=".txt,.json,.md"
                />
                <p className="text-xs text-muted-foreground mt-4">
                  Supported files: TXT, JSON, MD
                </p>
              </div>
            ) : (
              <div className="py-4">
                <div className="flex items-center justify-center gap-2 mb-4">
                  <FileText className="h-8 w-8 text-primary" />
                  <div className="text-left">
                    <p className="font-medium">{file.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                
                {uploading && (
                  <div className="space-y-2">
                    <Progress value={uploadProgress} />
                    <p className="text-sm text-muted-foreground">
                      {uploadProgress === 100 ? "Processing..." : "Uploading..."}
                    </p>
                  </div>
                )}
                
                {!uploading && !uploadResult && (
                  <div className="flex gap-2 justify-center">
                    <Button onClick={handleUpload}>Upload File</Button>
                    <Button variant="outline" onClick={resetUpload}>
                      Cancel
                    </Button>
                  </div>
                )}
                
                {uploadResult && (
                  <div className="flex gap-2 justify-center">
                    <Button variant="outline" onClick={resetUpload}>
                      Upload Another File
                    </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
      
      {/* Display upload results */}
      {uploadResult && (
        <Card>
          <CardHeader>
            <CardTitle>Upload Results</CardTitle>
            <CardDescription>
              The following knowledge was extracted from your file
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4 p-4 rounded-md bg-muted">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Entities Created:</span>
                <span className="text-sm bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                  {uploadResult.graph.nodesCreated}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Relationships Created:</span>
                <span className="text-sm bg-primary/20 text-primary px-2 py-0.5 rounded-full">
                  {uploadResult.graph.relationshipsCreated}
                </span>
              </div>
            </div>
            
            {/* Graph visualization */}
            <div className="h-[400px]">
              <GraphVisualization data={uploadResult.graph.graphData} />
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
