import { useState, useRef } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useToast } from "@/hooks/use-toast";
import { fileAPI } from "@/lib/api";
import { Upload, AlertTriangle, FileText, FileImage, FileArchive, Check } from "lucide-react";

interface FileUploadProps {
  onComplete: () => void;
}

export default function FileUpload({ onComplete }: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      setError(null);
    }
  };

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      'application/pdf', 
      'image/jpeg', 
      'image/png', 
      'image/tiff',
      'text/plain',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'
    ];
    
    const maxSize = 15 * 1024 * 1024; // 15MB
    
    if (!allowedTypes.includes(file.type)) {
      setError("Unsupported file type. Please upload PDF, image, or document files.");
      return false;
    }
    
    if (file.size > maxSize) {
      setError("File is too large. Maximum file size is 15MB.");
      return false;
    }
    
    return true;
  };

  const uploadFile = async () => {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }
    
    if (!validateFile(file)) {
      return;
    }
    
    setUploading(true);
    setProgress(10);
    
    try {
      // Simulate progress updates (in a real app, you might use upload progress events)
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 300);
      
      const response = await fileAPI.uploadFile(file);
      
      clearInterval(progressInterval);
      setProgress(100);
      
      toast({
        title: "Upload successful",
        description: `${file.name} has been successfully processed.`,
      });
      
      // Reset the form
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
      
      // Call the completion callback
      onComplete();
    } catch (error) {
      console.error("Upload error:", error);
      setError("An error occurred while uploading the file. Please try again.");
      
      toast({
        title: "Upload failed",
        description: "There was an error processing your document.",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (file: File) => {
    if (file.type.includes('pdf')) {
      return <FileText className="h-10 w-10 text-red-500" />;
    } else if (file.type.includes('image')) {
      return <FileImage className="h-10 w-10 text-blue-500" />;
    } else if (file.type.includes('word')) {
      return <FileText className="h-10 w-10 text-blue-700" />;
    } else {
      return <FileArchive className="h-10 w-10 text-amber-500" />;
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center">
          <Upload className="mr-2 h-5 w-5" />
          Upload Document
        </CardTitle>
        <CardDescription>
          Upload PDF, image, or text files to add to your knowledge graph
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            file ? "border-primary bg-primary/5" : "border-muted-foreground/25"
          }`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {file ? (
            <div className="flex flex-col items-center justify-center space-y-2">
              {getFileIcon(file)}
              <div className="font-medium">{file.name}</div>
              <div className="text-xs text-muted-foreground">
                {(file.size / 1024 / 1024).toFixed(2)} MB
              </div>
              {progress > 0 && progress < 100 ? (
                <div className="w-full max-w-xs">
                  <Progress value={progress} className="h-2" />
                </div>
              ) : uploading && progress === 100 ? (
                <div className="flex items-center text-sm text-primary">
                  <Check className="mr-1 h-4 w-4" />
                  Processing document...
                </div>
              ) : null}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2">
              <Upload className="h-10 w-10 text-muted-foreground/50" />
              <p className="text-sm font-medium">
                Drag and drop your file here or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supported formats: PDF, JPG, PNG, TIFF, TXT, DOC, DOCX
              </p>
            </div>
          )}
          <Input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png,.tiff,.txt,.doc,.docx"
            disabled={uploading}
          />
        </div>
        
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="text-xs text-muted-foreground">
          <p>Your documents will be processed to extract entities and relationships.</p>
          <p>Personal or sensitive information will remain private to your account.</p>
        </div>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={() => {
            setFile(null);
            if (fileInputRef.current) {
              fileInputRef.current.value = "";
            }
          }}
          disabled={!file || uploading}
        >
          Clear
        </Button>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            Select File
          </Button>
          <Button
            onClick={uploadFile}
            disabled={!file || uploading}
          >
            {uploading ? "Processing..." : "Upload"}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}