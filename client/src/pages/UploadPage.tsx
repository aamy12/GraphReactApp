
import { useState } from "react";
import FileUpload from "@/components/FileUpload";
import { useToast } from "@/hooks/use-toast";

export default function UploadPage() {
  const { toast } = useToast();

  const handleUploadComplete = () => {
    toast({
      title: "Upload complete",
      description: "Your document has been processed and added to the knowledge graph.",
    });
  };

  return (
    <div className="container mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold">Upload Documents</h1>
        <p className="text-muted-foreground mt-1">Add documents to your knowledge graph</p>
      </div>

      <div className="max-w-3xl">
        <FileUpload onComplete={handleUploadComplete} />
      </div>
    </div>
  );
}
