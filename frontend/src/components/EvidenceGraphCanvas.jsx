import React, { useState } from 'react';
import { ReactFlow, Background, Controls } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Layers,
  HelpCircle,
  FileCheck,
  AlertOctagon,
  ArrowRight,
  ShieldAlert,
  Sliders,
} from 'lucide-react';
import { StatusBadge } from './StatusBadge';

export function EvidenceGraphCanvas({ graphData }) {
  const [selectedNode, setSelectedNode] = useState(null);

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-500 shadow-2xs">
        <Layers className="w-8 h-8 mx-auto text-slate-400 mb-2" />
        <p className="text-sm font-semibold text-slate-800">No Evidence Graph Generated Yet</p>
        <p className="text-xs text-slate-500 mt-1">Analyze a product to visualize the compliance evidence trace.</p>
      </div>
    );
  }

  // Node styling mapper
  const styledNodes = graphData.nodes.map((node) => {
    let borderColor = 'border-slate-300';
    let bgColor = 'bg-white';
    let titleColor = 'text-slate-900';
    let title = node.data?.label || node.id;
    let subtitle = node.type;

    if (node.type === 'productNode') {
      borderColor = 'border-blue-300';
      bgColor = 'bg-blue-50/90';
      titleColor = 'text-blue-950';
      title = node.data?.label;
      subtitle = `Product: ${node.data?.category}`;
    } else if (node.type === 'standardNode') {
      borderColor = 'border-amber-300';
      bgColor = 'bg-amber-50/90';
      titleColor = 'text-amber-950';
      title = node.data?.standard_number;
      subtitle = node.data?.title;
    } else if (node.type === 'clauseNode') {
      borderColor = 'border-purple-300';
      bgColor = 'bg-purple-50/90';
      titleColor = 'text-purple-950';
      title = `Clause ${node.data?.clause_number}`;
      subtitle = node.data?.title;
    } else if (node.type === 'requirementNode') {
      borderColor = 'border-indigo-300';
      bgColor = 'bg-indigo-50/90';
      titleColor = 'text-indigo-950';
      title = node.data?.code;
      subtitle = node.data?.type;
    } else if (node.type === 'decisionNode') {
      borderColor = 'border-emerald-300';
      bgColor = 'bg-emerald-50/90';
      titleColor = 'text-emerald-950';
      title = `Status: ${node.data?.status}`;
      subtitle = node.data?.decision_engine;
    } else if (node.type === 'actionNode') {
      borderColor = 'border-rose-300';
      bgColor = 'bg-rose-50/90';
      titleColor = 'text-rose-950';
      title = `Action: ${node.data?.action}`;
      subtitle = 'Recommended Pathway';
    }

    return {
      ...node,
      data: {
        ...node.data,
        label: (
          <div
            onClick={() => setSelectedNode(node)}
            className={`p-3 rounded-lg border text-left shadow-xs cursor-pointer ${borderColor} ${bgColor}`}
            style={{ width: '220px' }}
          >
            <div className="text-[10px] font-mono uppercase tracking-wider text-slate-500 truncate">
              {subtitle}
            </div>
            <div className={`text-xs font-bold truncate mt-0.5 ${titleColor}`}>
              {title}
            </div>
          </div>
        ),
      },
    };
  });

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      {/* React Flow Container */}
      <div className="lg:col-span-3 bg-slate-50 border border-slate-200 rounded-xl overflow-hidden h-[500px] relative shadow-2xs">
        <ReactFlow
          nodes={styledNodes}
          edges={graphData.edges}
          fitView
          attributionPosition="bottom-left"
        >
          <Background color="#cbd5e1" gap={16} />
          <Controls className="bg-white border-slate-200 text-slate-700 fill-slate-700 shadow-xs" />
        </ReactFlow>

        <div className="absolute top-3 left-3 bg-white/95 border border-slate-200 px-3 py-1.5 rounded-lg text-[11px] font-mono text-slate-700 pointer-events-none flex items-center gap-2 shadow-xs">
          <Layers className="w-3.5 h-3.5 text-indigo-600" />
          <span>Evidence Graph: Real Backend IDs (Click any node to inspect provenance)</span>
        </div>
      </div>

      {/* Node Inspector Drawer */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 text-xs space-y-4 shadow-2xs">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <h4 className="font-bold text-slate-900 flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-indigo-600" />
            Node Inspector
          </h4>
          {selectedNode && (
            <span className="text-[10px] font-mono text-indigo-700 px-2 py-0.5 rounded bg-indigo-50 border border-indigo-200 font-semibold">
              {selectedNode.type}
            </span>
          )}
        </div>

        {selectedNode ? (
          <div className="space-y-3">
            <div>
              <span className="text-slate-500 uppercase tracking-wider text-[10px]">Node ID:</span>
              <div className="font-mono text-slate-800">{selectedNode.id}</div>
            </div>

            {selectedNode.type === 'productNode' && (
              <div className="space-y-2">
                <div>
                  <span className="text-slate-500 text-[10px]">Product:</span>
                  <div className="font-bold text-slate-900">{selectedNode.data?.label}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Category:</span>
                  <div className="text-slate-700">{selectedNode.data?.category}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Declared Materials:</span>
                  <div className="text-indigo-700 font-mono">
                    {selectedNode.data?.materials?.join(', ') || 'None'}
                  </div>
                </div>
              </div>
            )}

            {selectedNode.type === 'standardNode' && (
              <div className="space-y-2">
                <div>
                  <span className="text-slate-500 text-[10px]">Standard Number:</span>
                  <div className="font-bold text-amber-700">{selectedNode.data?.standard_number}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Title:</span>
                  <div className="text-slate-700">{selectedNode.data?.title}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Technical Relevance:</span>
                  <div className="text-emerald-700 font-semibold">{selectedNode.data?.technical_relevance}</div>
                </div>
                <div>
                  <span className="text-slate-500 text-[10px]">Regulatory Status:</span>
                  <div className="text-indigo-700 font-semibold">{selectedNode.data?.regulatory_status}</div>
                </div>
              </div>
            )}

            {selectedNode.type === 'decisionNode' && (
              <div className="space-y-2">
                <div>
                  <span className="text-slate-500 text-[10px]">Verdict Status:</span>
                  <div className="mt-1">
                    <StatusBadge status={selectedNode.data?.status} />
                  </div>
                </div>
                {selectedNode.data?.action && (
                  <div>
                    <span className="text-slate-500 text-[10px]">Recommended Action:</span>
                    <div className="font-mono text-rose-700 font-bold mt-0.5">
                      {selectedNode.data?.action}
                    </div>
                  </div>
                )}
                <div>
                  <span className="text-slate-500 text-[10px]">Explanation:</span>
                  <p className="text-slate-700 leading-relaxed mt-0.5">
                    {selectedNode.data?.explanation}
                  </p>
                </div>
                <div className="pt-2 border-t border-slate-100">
                  <span className="text-[10px] text-slate-500">Decision Authority:</span>
                  <div className="text-[11px] font-mono text-emerald-700">
                    {selectedNode.data?.decision_engine} (LLM Authority = 0)
                  </div>
                </div>
              </div>
            )}

            {selectedNode.type === 'actionNode' && (
              <div className="space-y-2">
                <div>
                  <span className="text-slate-500 text-[10px]">Action Required:</span>
                  <div className="font-mono font-bold text-rose-700">{selectedNode.data?.action}</div>
                </div>
                <p className="text-slate-600 text-[11px]">
                  Prescribed operational pathway to resolve evidentiary gap for requirement {selectedNode.data?.target_requirement}.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="text-slate-500 text-center py-8">
            Click on any node in the graph to inspect its attributes, rules, and decision provenance.
          </div>
        )}
      </div>
    </div>
  );
}
