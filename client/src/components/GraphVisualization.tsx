import { useRef, useEffect, useState } from "react";
import * as d3 from "d3";
import { GraphData, Node, Relationship } from "@/types/graph";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, RotateCcw } from "lucide-react";

interface GraphVisualizationProps {
  data: GraphData;
  height?: number;
  title?: string;
  description?: string;
}

export default function GraphVisualization({ 
  data, 
  height = 500,
  title = "Knowledge Graph",
  description = "Interactive visualization of entities and their relationships"
}: GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  
  // Force simulation references
  const simulationRef = useRef<d3.Simulation<d3.SimulationNodeDatum, undefined> | null>(null);
  
  // Zoom state
  const [zoomTransform, setZoomTransform] = useState<d3.ZoomTransform | null>(null);
  
  useEffect(() => {
    if (!svgRef.current || !data.nodes.length) return;
    
    // Clear any existing visualization
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    
    // Define dimensions
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;
    
    // Define colors by node type
    const nodeColorScale = d3.scaleOrdinal<string>()
      .domain(["Person", "Organization", "Location", "Document", "Concept", "Chunk", "Metadata", "Entity", "Node"])
      .range(["#4f46e5", "#0ea5e9", "#10b981", "#f97316", "#8b5cf6", "#ec4899", "#6b7280", "#ef4444", "#a16207"]);
    
    // Create container group with zoom behavior
    const g = svg.append("g");
    
    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.25, 5])
      .on("zoom", (event) => {
        g.attr("transform", event.transform.toString());
        setZoomTransform(event.transform);
      });
    
    svg.call(zoom as any);
    
    // Initialize with a slight zoom out if we have many nodes
    if (data.nodes.length > 10) {
      const initialZoom = d3.zoomIdentity.scale(0.7);
      svg.call(zoom.transform as any, initialZoom);
    }
    
    // Create links before nodes so they appear underneath
    const links = g.append("g")
      .attr("stroke", "#999")
      .attr("stroke-opacity", 0.6)
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke-width", 1.5);
    
    // Add link labels
    const linkLabels = g.append("g")
      .selectAll("text")
      .data(data.links)
      .enter()
      .append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "-5")
      .attr("font-size", "8px")
      .attr("font-family", "sans-serif")
      .attr("pointer-events", "none")
      .attr("fill", "#6b7280")
      .text(d => d.type);
    
    // Create nodes
    const nodes = g.append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("r", d => calculateNodeRadius(d))
      .attr("fill", d => getNodeColor(d.label))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .on("click", (event, d) => handleNodeClick(d))
      .on("mouseover", (event, d) => handleMouseOver(event, d))
      .on("mouseout", handleMouseOut)
      .call(d3.drag<SVGCircleElement, Node>()
        .on("start", dragStarted)
        .on("drag", dragged)
        .on("end", dragEnded) as any);
    
    // Add node labels
    const nodeLabels = g.append("g")
      .selectAll("text")
      .data(data.nodes)
      .enter()
      .append("text")
      .attr("dy", d => -calculateNodeRadius(d) - 5)
      .attr("text-anchor", "middle")
      .attr("font-size", "10px")
      .attr("font-family", "sans-serif")
      .attr("pointer-events", "none")
      .attr("fill", "#374151")
      .text(d => d.name || d.label);
    
    // Create force simulation
    const simulation = d3.forceSimulation<Node>(data.nodes as Node[])
      .force("link", d3.forceLink<Node, d3.SimulationLinkDatum<Node>>(data.links as d3.SimulationLinkDatum<Node>[])
        .id(d => (d as Node).id)
        .distance(100))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collide", d3.forceCollide().radius(d => calculateNodeRadius(d as Node) + 10));
    
    // Save simulation reference
    simulationRef.current = simulation;
    
    // Handle tick events
    simulation.on("tick", () => {
      // Update links
      links
        .attr("x1", d => (d.source as Node).x!)
        .attr("y1", d => (d.source as Node).y!)
        .attr("x2", d => (d.target as Node).x!)
        .attr("y2", d => (d.target as Node).y!);
      
      // Update link labels
      linkLabels
        .attr("x", d => {
          const sourceX = (d.source as Node).x!;
          const targetX = (d.target as Node).x!;
          return sourceX + (targetX - sourceX) / 2;
        })
        .attr("y", d => {
          const sourceY = (d.source as Node).y!;
          const targetY = (d.target as Node).y!;
          return sourceY + (targetY - sourceY) / 2;
        });
      
      // Update nodes
      nodes
        .attr("cx", d => d.x!)
        .attr("cy", d => d.y!);
      
      // Update node labels
      nodeLabels
        .attr("x", d => d.x!)
        .attr("y", d => d.y!);
    });
    
    // Helper functions
    function dragStarted(event: d3.D3DragEvent<SVGCircleElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }
    
    function dragged(event: d3.D3DragEvent<SVGCircleElement, Node, Node>) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }
    
    function dragEnded(event: d3.D3DragEvent<SVGCircleElement, Node, Node>) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }
    
    // Clean up
    return () => {
      simulation.stop();
    };
  }, [data]);
  
  // Helper functions
  function calculateNodeRadius(node: Node): number {
    // Base size on node type and properties
    const baseSize = 7;
    
    // Increase size for important node types
    if (node.label === "Document") return baseSize + 5;
    if (node.label === "Person") return baseSize + 3;
    if (node.label === "Organization") return baseSize + 2;
    
    // Size could also depend on number of connections (calculated outside this function)
    return baseSize;
  }
  
  function getNodeColor(label: string): string {
    // Define colors for different entity types
    const colors: Record<string, string> = {
      "Person": "#4f46e5", // indigo
      "Organization": "#0ea5e9", // sky blue
      "Location": "#10b981", // emerald
      "Document": "#f97316", // orange
      "Concept": "#8b5cf6", // violet
      "Chunk": "#ec4899", // pink
      "Metadata": "#6b7280", // gray
      "Entity": "#ef4444", // red
    };
    
    return colors[label] || "#a16207"; // amber as default
  }
  
  function handleNodeClick(node: Node) {
    setSelectedNode(node === selectedNode ? null : node);
  }
  
  function handleMouseOver(event: any, node: Node) {
    d3.select(event.currentTarget)
      .attr("stroke", "#000")
      .attr("stroke-width", 2);
  }
  
  function handleMouseOut() {
    d3.select(d3.event?.currentTarget)
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5);
  }
  
  function handleZoomIn() {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.25, 5]);
    
    const currentTransform = zoomTransform || d3.zoomIdentity;
    const newTransform = currentTransform.scale(currentTransform.k * 1.3);
    
    svg.transition().duration(300).call(zoom.transform as any, newTransform);
  }
  
  function handleZoomOut() {
    if (!svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.25, 5]);
    
    const currentTransform = zoomTransform || d3.zoomIdentity;
    const newTransform = currentTransform.scale(currentTransform.k / 1.3);
    
    svg.transition().duration(300).call(zoom.transform as any, newTransform);
  }
  
  function handleReset() {
    if (!svgRef.current || !simulationRef.current) return;
    
    const svg = d3.select(svgRef.current);
    const zoom = d3.zoom<SVGSVGElement, unknown>().scaleExtent([0.25, 5]);
    
    // Reset zoom
    svg.transition().duration(300).call(zoom.transform as any, d3.zoomIdentity);
    
    // Reset node positions and restart simulation
    simulationRef.current.alpha(1).restart();
    data.nodes.forEach(node => {
      node.fx = null;
      node.fy = null;
    });
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col h-full">
          <div className="flex justify-end gap-2 mb-2">
            <Button variant="outline" size="icon" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" onClick={handleReset}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="relative border rounded-md" style={{ height: `${height}px` }}>
            {data.nodes.length === 0 ? (
              <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
                No data to visualize
              </div>
            ) : (
              <svg 
                ref={svgRef} 
                className="w-full h-full text-foreground"
              />
            )}
          </div>
          
          {selectedNode && (
            <div className="mt-4 p-4 border rounded-md bg-muted">
              <h3 className="font-medium">{selectedNode.name || selectedNode.label}</h3>
              <p className="text-sm text-muted-foreground mb-2">Type: {selectedNode.label}</p>
              
              {Object.entries(selectedNode.properties).length > 0 && (
                <div className="mt-2">
                  <h4 className="text-sm font-medium mb-1">Properties:</h4>
                  <div className="text-xs space-y-1">
                    {Object.entries(selectedNode.properties)
                      .filter(([key]) => !['created_by', 'created_at'].includes(key))
                      .map(([key, value]) => (
                        <div key={key} className="flex">
                          <span className="font-medium min-w-[100px]">{key}:</span>
                          <span className="truncate">{typeof value === 'object' ? JSON.stringify(value) : String(value)}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}