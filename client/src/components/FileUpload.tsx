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
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [currentProgress, setCurrentProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files);
      setFiles(prev => [...prev, ...selectedFiles]);
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
    
    if (e.dataTransfer.files) {
      const droppedFiles = Array.from(e.dataTransfer.files);
      setFiles(prev => [...prev, ...droppedFiles]);
      setError(null);
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const validateFile = (file: File): boolean => {
    const allowedTypes = [
      // Documents
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword',
      'text/plain',
      
      // Images
      'image/jpeg',
      'image/png',
      'image/tiff',
      
      // Data formats
      'application/json',
      'application/ld+json',
      'text/csv',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/tab-separated-values',
      'application/xml',
      'text/xml'
    ];
    
    // Check file extension for common formats where MIME might not be reliable
    const fileName = file.name.toLowerCase();
    const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.txt', '.doc', 
                            '.docx', '.json', '.csv', '.xls', '.xlsx', '.tsv', '.xml'];
    
    const hasValidExtension = validExtensions.some(ext => fileName.endsWith(ext));
    
    const maxSize = 15 * 1024 * 1024; // 15MB
    
    if (!allowedTypes.includes(file.type) && !hasValidExtension) {
      setError("Unsupported file type. Please upload PDF, image, document, or data files (JSON, CSV, etc.).");
      return false;
    }
    
    if (file.size > maxSize) {
      setError("File is too large. Maximum file size is 15MB.");
      return false;
    }
    
    return true;
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      setError("Please select files to upload.");
      return;
    }
    
    setUploading(true);
    
    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        if (!validateFile(file)) {
          continue;
        }
        
        setCurrentFile(file.name);
        setCurrentProgress(0);
        
        // Simulate progress updates for each file
        const progressInterval = setInterval(() => {
          setCurrentProgress((prev) => {
            if (prev >= 90) {
              clearInterval(progressInterval);
              return 90;
            }
            return prev + 10;
          });
        }, 300);
        
        const response = await fileAPI.uploadFile(file);
        
        clearInterval(progressInterval);
        setCurrentProgress(100);
        
        toast({
          title: "Upload successful",
          description: `${file.name} has been successfully processed.`,
        });
      }
      
      // Reset the form
      setFiles([]);
      setCurrentFile("");
      setCurrentProgress(0);
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
    const fileName = file.name.toLowerCase();
    
    // Import additional icons
    const FileJson = () => (
      <div className="h-10 w-10 flex items-center justify-center text-purple-600 relative">
        <FileText className="h-10 w-10 absolute" />
        <span className="z-10 text-xs font-bold mt-1">JSON</span>
      </div>
    );
    
    const FileCsv = () => (
      <div className="h-10 w-10 flex items-center justify-center text-green-600 relative">
        <FileText className="h-10 w-10 absolute" />
        <span className="z-10 text-xs font-bold mt-1">CSV</span>
      </div>
    );
    
    const FileExcel = () => (
      <div className="h-10 w-10 flex items-center justify-center text-green-700 relative">
        <FileText className="h-10 w-10 absolute" />
        <span className="z-10 text-xs font-bold mt-1">XLS</span>
      </div>
    );
    
    const FileXml = () => (
      <div className="h-10 w-10 flex items-center justify-center text-amber-600 relative">
        <FileText className="h-10 w-10 absolute" />
        <span className="z-10 text-xs font-bold mt-1">XML</span>
      </div>
    );
    
    // Check by MIME type first
    if (file.type.includes('pdf')) {
      return <FileText className="h-10 w-10 text-red-500" />;
    } else if (file.type.includes('image')) {
      return <FileImage className="h-10 w-10 text-blue-500" />;
    } else if (file.type.includes('word') || file.type.includes('document')) {
      return <FileText className="h-10 w-10 text-blue-700" />;
    } else if (file.type.includes('json')) {
      return <FileJson />;
    } else if (file.type.includes('csv') || file.type.includes('tab-separated')) {
      return <FileCsv />;
    } else if (file.type.includes('excel') || file.type.includes('spreadsheet')) {
      return <FileExcel />;
    } else if (file.type.includes('xml')) {
      return <FileXml />;
    }
    
    // Fallback to extension check
    if (fileName.endsWith('.pdf')) {
      return <FileText className="h-10 w-10 text-red-500" />;
    } else if (fileName.endsWith('.jpg') || fileName.endsWith('.jpeg') || 
               fileName.endsWith('.png') || fileName.endsWith('.tiff')) {
      return <FileImage className="h-10 w-10 text-blue-500" />;
    } else if (fileName.endsWith('.doc') || fileName.endsWith('.docx') || 
               fileName.endsWith('.txt')) {
      return <FileText className="h-10 w-10 text-blue-700" />;
    } else if (fileName.endsWith('.json') || fileName.endsWith('.jsonl')) {
      return <FileJson />;
    } else if (fileName.endsWith('.csv') || fileName.endsWith('.tsv')) {
      return <FileCsv />;
    } else if (fileName.endsWith('.xls') || fileName.endsWith('.xlsx')) {
      return <FileExcel />;
    } else if (fileName.endsWith('.xml')) {
      return <FileXml />;
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
          Upload PDF, image, text, JSON, CSV, Excel, or XML files to add to your knowledge graph
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div
          className={`border-2 border-dashed rounded-lg p-6 text-center ${
            files.length > 0 ? "border-primary bg-primary/5" : "border-muted-foreground/25"
          }`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {files.length > 0 ? (
            <div className="flex flex-col items-center justify-center space-y-4 w-full">
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between w-full max-w-md bg-background/50 p-2 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getFileIcon(file)}
                    <div>
                      <div className="font-medium">{file.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(2)} MB
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => removeFile(index)}
                    disabled={uploading}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              ))}
              {uploading && (
                <div className="w-full max-w-md space-y-2">
                  <div className="text-sm text-center">{currentFile}</div>
                  <Progress value={currentProgress} className="h-2" />
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center space-y-2">
              <Upload className="h-10 w-10 text-muted-foreground/50" />
              <p className="text-sm font-medium">
                Drag and drop your file here or click to browse
              </p>
              <p className="text-xs text-muted-foreground">
                Supported formats: PDF, JPG, PNG, TXT, DOC, CSV, JSON, XLS, XLSX, XML
              </p>
            </div>
          )}
          <Input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileChange}
            accept=".pdf,.jpg,.jpeg,.png,.tiff,.txt,.doc,.docx,.json,.csv,.xls,.xlsx,.xml,.tsv"
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
            setFiles([]);
            if (fileInputRef.current) {
              fileInputRef.current.value = "";
            }
          }}
          disabled={files.length === 0 || uploading}
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
            onClick={uploadFiles}
            disabled={files.length === 0 || uploading}
          >
            {uploading ? "Processing..." : `Upload ${files.length} File${files.length !== 1 ? 's' : ''}`}
          </Button>
        </div>
      </CardFooter>
    </Card>
  );
}