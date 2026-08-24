import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { ZoomIn, ZoomOut, RotateCcw, Copy, Check, Download, Layers } from 'lucide-react';

mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'Inter, system-ui, sans-serif',
  er: {
    useMaxWidth: true,
    fontSize: 12
  }
});

const MermaidViewer = ({ code }) => {
  const containerRef = useRef(null);
  const [svgContent, setSvgContent] = useState('');
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!code) return;

    let isMounted = true;
    const renderDiagram = async () => {
      try {
        const id = `mermaid-svg-${Math.random().toString(36).substring(2, 9)}`;
        const cleanCode = code.replace(/```mermaid/g, '').replace(/```/g, '').trim();
        const { svg } = await mermaid.render(id, cleanCode);
        if (isMounted) {
          setSvgContent(svg);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Mermaid Render Error:", err);
          setError(err.message || "Failed to render Mermaid diagram.");
        }
      }
    };

    renderDiagram();
    return () => { isMounted = false; };
  }, [code]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadSVG = () => {
    if (!svgContent) return;
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `schema_erd_${Date.now()}.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="mermaid-viewer-error">
        <p>Could not render ER Diagram cleanly.</p>
        <pre><code>{code}</code></pre>
      </div>
    );
  }

  return (
    <div className="mermaid-viewer-card">
      <div className="mermaid-toolbar">
        <div className="mermaid-title">
          <Layers size={14} />
          <span>Interactive ER Diagram</span>
        </div>
        <div className="mermaid-actions">
          <button className="m-btn" onClick={() => setZoom(prev => Math.min(prev + 0.2, 2.0))} title="Zoom In">
            <ZoomIn size={13} />
          </button>
          <button className="m-btn" onClick={() => setZoom(prev => Math.max(prev - 0.2, 0.6))} title="Zoom Out">
            <ZoomOut size={13} />
          </button>
          <button className="m-btn" onClick={() => setZoom(1.0)} title="Reset Zoom">
            <RotateCcw size={13} />
          </button>
          <button className="m-btn" onClick={handleDownloadSVG} title="Download SVG">
            <Download size={13} /> SVG
          </button>
          <button className="m-btn" onClick={handleCopy} title="Copy Code">
            {copied ? <Check size={13} /> : <Copy size={13} />}
          </button>
        </div>
      </div>

      <div className="mermaid-canvas-wrap">
        <div
          ref={containerRef}
          className="mermaid-canvas"
          style={{ transform: `scale(${zoom})`, transformOrigin: 'top center', transition: 'transform 0.2s ease' }}
          dangerouslySetInnerHTML={{ __html: svgContent }}
        />
      </div>
    </div>
  );
};

export default MermaidViewer;
