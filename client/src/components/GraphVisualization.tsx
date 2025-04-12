import { useEffect, useRef, useState } from "react";
import * as d3 from "d3";
import { GraphData, Node, Link } from "@/types";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ZoomIn, ZoomOut, Maximize, X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface GraphVisualizationProps {
  data: GraphData;
}

export default function GraphVisualization({ data }: GraphVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [selectedLink, setSelectedLink] = useState<Link | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (!svgRef.current || !data || !data.nodes || !data.links) return;

    // Clear any existing visualization
    d3.select(svgRef.current).selectAll("*").remove();

    const containerWidth = containerRef.current?.clientWidth || 800;
    const containerHeight = containerRef.current?.clientHeight || 500;

    // Create SVG element
    const svg = d3.select(svgRef.current)
      .attr("width", containerWidth)
      .attr("height", containerHeight)
      .attr("viewBox", [0, 0, containerWidth, containerHeight])
      .attr("style", "max-width: 100%; height: auto;");

    // Create a group for zoom/pan behavior
    const g = svg.append("g");

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.25, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    // Define arrow marker for directed edges
    svg.append("defs").append("marker")
      .attr("id", "arrowhead")
      .attr("viewBox", "0 -5 10 10")
      .attr("refX", 20)
      .attr("refY", 0)
      .attr("markerWidth", 6)
      .attr("markerHeight", 6)
      .attr("orient", "auto")
      .append("path")
      .attr("d", "M0,-5L10,0L0,5")
      .attr("fill", "#888");

    // Create links
    const links = g.append("g")
      .selectAll("line")
      .data(data.links)
      .enter()
      .append("line")
      .attr("stroke", "#888")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", 1.5)
      .attr("marker-end", "url(#arrowhead)")
      .on("click", (event, d) => {
        setSelectedNode(null);
        setSelectedLink(d);
        event.stopPropagation();
      });

    // Create link labels
    const linkLabels = g.append("g")
      .selectAll("text")
      .data(data.links)
      .enter()
      .append("text")
      .attr("font-size", 8)
      .attr("text-anchor", "middle")
      .text(d => d.type)
      .attr("fill", "#666")
      .attr("dy", -4);

    // Create nodes
    const nodes = g.append("g")
      .selectAll("circle")
      .data(data.nodes)
      .enter()
      .append("circle")
      .attr("r", 8)
      .attr("fill", d => getNodeColor(d.label))
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .on("click", (event, d) => {
        setSelectedLink(null);
        setSelectedNode(d);
        event.stopPropagation();
      })
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
      .text(d => d.name)
      .attr("font-size", 10)
      .attr("text-anchor", "middle")
      .attr("dy", 20);

    // Clear selections when clicking on the background
    svg.on("click", () => {
      setSelectedNode(null);
      setSelectedLink(null);
    });

    // Create simulation
    const simulation = d3.forceSimulation<Node, Link>(data.nodes)
      .force("link", d3.forceLink<Node, Link>(data.links)
        .id(d => d.id)
        .distance(100))
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(containerWidth / 2, containerHeight / 2))
      .on("tick", ticked);

    // Position updates on simulation tick
    function ticked() {
      links
        .attr("x1", d => (d.source as any).x)
        .attr("y1", d => (d.source as any).y)
        .attr("x2", d => (d.target as any).x)
        .attr("y2", d => (d.target as any).y);

      linkLabels
        .attr("x", d => ((d.source as any).x + (d.target as any).x) / 2)
        .attr("y", d => ((d.source as any).y + (d.target as any).y) / 2);

      nodes
        .attr("cx", d => d.x as number)
        .attr("cy", d => d.y as number);

      nodeLabels
        .attr("x", d => d.x as number)
        .attr("y", d => d.y as number);
    }

    // Drag functions
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

    // Color function for nodes based on label
    function getNodeColor(label: string): string {
      const colors: Record<string, string> = {
        "Person": "#4C9AFF",
        "Organization": "#F78C6C",
        "Location": "#82AAFF",
        "Product": "#C792EA",
        "Event": "#FFCB6B",
        "Concept": "#89DDFF",
        "Entity": "#7986CB",
      };
      
      return colors[label] || "#7986CB"; // Default color
    }

    // Initial zoom to fit all nodes
    const initialScale = 0.8;
    svg.call(
      zoom.transform as any,
      d3.zoomIdentity
        .translate(containerWidth / 2, containerHeight / 2)
        .scale(initialScale)
        .translate(-containerWidth / 2, -containerHeight / 2)
    );

    // Cleanup function
    return () => {
      simulation.stop();
    };
  }, [data]);

  const handleZoomIn = () => {
    d3.select(svgRef.current).transition().call(
      (d3.zoom<SVGSVGElement, unknown>() as any).scaleBy, 1.2
    );
  };

  const handleZoomOut = () => {
    d3.select(svgRef.current).transition().call(
      (d3.zoom<SVGSVGElement, unknown>() as any).scaleBy, 0.8
    );
  };

  const handleReset = () => {
    const containerWidth = containerRef.current?.clientWidth || 800;
    const containerHeight = containerRef.current?.clientHeight || 500;
    
    d3.select(svgRef.current).transition().call(
      (d3.zoom<SVGSVGElement, unknown>() as any).transform,
      d3.zoomIdentity
        .translate(containerWidth / 2, containerHeight / 2)
        .scale(0.8)
        .translate(-containerWidth / 2, -containerHeight / 2)
    );
  };

  return (
    <div className="relative h-full" ref={containerRef}>
      {/* Controls */}
      <div className="absolute top-2 right-2 z-10 bg-background rounded-md border shadow-sm flex flex-col">
        <Button variant="ghost" size="icon" onClick={handleZoomIn} title="Zoom In">
          <ZoomIn className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={handleZoomOut} title="Zoom Out">
          <ZoomOut className="h-4 w-4" />
        </Button>
        <Button variant="ghost" size="icon" onClick={handleReset} title="Reset View">
          <Maximize className="h-4 w-4" />
        </Button>
      </div>
      
      {/* Entity/Relationship details */}
      {(selectedNode || selectedLink) && (
        <div className="absolute bottom-4 left-4 z-10 bg-background/95 backdrop-blur-sm rounded-md border shadow-sm p-4 max-w-xs">
          <div className="flex items-center justify-between mb-2">
            <h3 className="font-semibold">
              {selectedNode ? "Entity Details" : "Relationship Details"}
            </h3>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={() => {
                setSelectedNode(null);
                setSelectedLink(null);
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          
          {selectedNode && (
            <div className="space-y-2">
              <div>
                <span className="text-xs text-muted-foreground">Type:</span>
                <p className="text-sm font-medium">{selectedNode.label}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Name:</span>
                <p className="text-sm font-medium">{selectedNode.name}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Properties:</span>
                <div className="mt-1 space-y-1">
                  {Object.entries(selectedNode.properties)
                    .filter(([key]) => key !== 'user_id')
                    .map(([key, value]) => (
                      <div key={key} className="text-xs">
                        <span className="font-medium">{key}: </span>
                        <span>{String(value)}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
          
          {selectedLink && (
            <div className="space-y-2">
              <div>
                <span className="text-xs text-muted-foreground">Type:</span>
                <p className="text-sm font-medium">{selectedLink.type}</p>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Properties:</span>
                <div className="mt-1 space-y-1">
                  {Object.entries(selectedLink.properties)
                    .filter(([key]) => key !== 'user_id')
                    .map(([key, value]) => (
                      <div key={key} className="text-xs">
                        <span className="font-medium">{key}: </span>
                        <span>{String(value)}</span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
      
      {/* SVG container */}
      <svg
        ref={svgRef}
        className="w-full h-full"
        style={{ 
          backgroundColor: "transparent",
          cursor: "grab",
        }}
      />
      
      {/* Empty state */}
      {(!data || !data.nodes || data.nodes.length === 0) && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Card className="w-64 bg-background/80 backdrop-blur-sm">
            <CardContent className="p-4 text-center">
              <p className="text-muted-foreground">
                No graph data available.
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
