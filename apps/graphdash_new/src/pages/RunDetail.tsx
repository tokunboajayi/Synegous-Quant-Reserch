import { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ReactFlow, {
    Background,
    Controls,
    useNodesState,
    useEdgesState,
    Position,
    type Node,
    type Edge
} from 'reactflow';
import 'reactflow/dist/style.css';
import { ArrowLeft, Activity, FileText, BarChart2, Shield, Layers } from 'lucide-react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

// Types
import type { Run } from '../types';

const INITIAL_NODES: Node[] = [
    // MNX Lane (Top)
    { id: 'mnx_ingest', position: { x: 0, y: 0 }, data: { label: 'MNX Ingest' }, type: 'input', sourcePosition: Position.Right },
    { id: 'mnx_features', position: { x: 200, y: 0 }, data: { label: 'Features' }, targetPosition: Position.Left, sourcePosition: Position.Right },
    { id: 'mnx_ranker', position: { x: 400, y: 0 }, data: { label: 'LGBM Ranker' }, targetPosition: Position.Left, sourcePosition: Position.Right },
    { id: 'mnx_neutral', position: { x: 600, y: 0 }, data: { label: 'Neutralize' }, targetPosition: Position.Left, sourcePosition: Position.Right },
    { id: 'mnx_basket', position: { x: 800, y: 0 }, data: { label: 'Rebalance Basket' }, targetPosition: Position.Left, sourcePosition: Position.Right },

    // Bridge
    { id: 'mnx_bridge', position: { x: 900, y: 100 }, data: { label: 'Adapter' }, targetPosition: Position.Top, sourcePosition: Position.Bottom },

    // NMIE Lane (Bottom)
    { id: 'nmie_orders', position: { x: 800, y: 200 }, data: { label: 'Parent Orders' }, targetPosition: Position.Right, sourcePosition: Position.Left },
    { id: 'nmie_sched', position: { x: 600, y: 200 }, data: { label: 'Scheduler' }, targetPosition: Position.Right, sourcePosition: Position.Left },
    { id: 'nmie_sim', position: { x: 400, y: 200 }, data: { label: 'Sim Hard/Soft' }, targetPosition: Position.Right, sourcePosition: Position.Left },
    { id: 'nmie_tca', position: { x: 200, y: 200 }, data: { label: 'TCA & Disagree' }, targetPosition: Position.Right, sourcePosition: Position.Left },
    { id: 'nmie_report', position: { x: 0, y: 200 }, data: { label: 'Gov Gate' }, type: 'output', targetPosition: Position.Right },
];

const INITIAL_EDGES: Edge[] = [
    { id: 'e1-2', source: 'mnx_ingest', target: 'mnx_features', animated: true },
    { id: 'e2-3', source: 'mnx_features', target: 'mnx_ranker', animated: true },
    { id: 'e3-4', source: 'mnx_ranker', target: 'mnx_neutral', animated: true },
    { id: 'e4-5', source: 'mnx_neutral', target: 'mnx_basket', animated: true },
    { id: 'e5-b', source: 'mnx_basket', target: 'mnx_bridge', animated: true, style: { stroke: '#06b6d4' } },
    { id: 'eb-6', source: 'mnx_bridge', target: 'nmie_orders', animated: true, style: { stroke: '#06b6d4' } },
    { id: 'e6-7', source: 'nmie_orders', target: 'nmie_sched', animated: true },
    { id: 'e7-8', source: 'nmie_sched', target: 'nmie_sim', animated: true },
    { id: 'e8-9', source: 'nmie_sim', target: 'nmie_tca', animated: true },
    { id: 'e9-10', source: 'nmie_tca', target: 'nmie_report', animated: true },
];

export const RunDetail = () => {
    const { runId } = useParams();
    const [run, setRun] = useState<Run | null>(null);
    const [nodes, setNodes, onNodesChange] = useNodesState(INITIAL_NODES);
    const [edges, setEdges, onEdgesChange] = useEdgesState(INITIAL_EDGES);
    const [selectedNode, setSelectedNode] = useState<string | null>(null);
    const [artifactContent, setArtifactContent] = useState<any>(null);
    const [loadingArtifact, setLoadingArtifact] = useState(false);

    // Fetch Run & Pipeline Timings
    useEffect(() => {
        if (!runId) return;

        // 1. Get Status
        axios.get(`/control/runs`).then(res => {
            const found = res.data.find((r: Run) => r.run_id === runId);
            if (found) setRun(found);
        });

        // 2. Get Graph Timings
        axios.get(`/graphdash/run/${runId}/pipeline`).then(res => {
            const { timings } = res.data;
            if (timings) {
                setNodes(nds => nds.map(node => {
                    const t = timings[node.id];
                    if (t) {
                        return {
                            ...node,
                            data: {
                                ...node.data,
                                label: `${node.data.label.split('\n')[0]}\n${t.timestamp} (${t.duration})`
                            },
                            style: { borderColor: '#4ade80', borderWidth: 2 } // Green border for completion
                        };
                    }
                    return node;
                }));
            }
        });
    }, [runId]);

    // Handle Node Click
    const onNodeClick = useCallback((event: any, node: Node) => {
        setSelectedNode(node.id);
        fetchArtifactForNode(node.id);
    }, [runId]);

    const fetchArtifactForNode = async (nodeId: string) => {
        if (!runId) return;
        setLoadingArtifact(true);
        setArtifactContent(null);

        try {
            let res;
            // MNX Artifacts
            if (nodeId === 'mnx_ingest') res = { data: { message: "Ingested Daily Bars (Parquet)" } }; // Metadata only usually
            if (nodeId === 'mnx_basket') res = await axios.get(`/artifacts/${runId}/mnx/basket_summary`);
            if (nodeId === 'mnx_neutral') res = await axios.get(`/artifacts/${runId}/mnx/file/mnx_target_weights.json`);

            // NMIE Artifacts
            if (nodeId === 'nmie_tca') res = await axios.get(`/artifacts/${runId}/tca_summary`);
            if (nodeId === 'nmie_report') res = await axios.get(`/artifacts/${runId}/gate_decision.json`);

            if (res) setArtifactContent(res.data);
            else setArtifactContent({ message: "No text view available for this node's artifact." });

        } catch (e) {
            setArtifactContent({ error: "Artifact not found or pending." });
        } finally {
            setLoadingArtifact(false);
        }
    };

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center gap-4 mb-4">
                <Link to="/" className="p-2 hover:bg-slate-800 rounded-full text-slate-400">
                    <ArrowLeft size={20} />
                </Link>
                <div>
                    <h1 className="text-xl font-bold text-slate-200 flex items-center gap-2">
                        Run: <span className="font-mono text-cyan-400">{runId}</span>
                        {run && (
                            <span className={`text-xs px-2 py-1 rounded bg-slate-800 text-slate-400`}>
                                {run.status}
                            </span>
                        )}
                    </h1>
                </div>
            </div>

            {/* Main Content: Graph + Sidebar */}
            <div className="flex-1 flex border border-slate-700 rounded-xl overflow-hidden bg-[#0f1419]">

                {/* ReactFlow Canvas */}
                <div className="flex-1 relative border-r border-slate-700">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onNodeClick={onNodeClick}
                        fitView
                        attributionPosition="bottom-left"
                    >
                        <Background className="bg-[#0f1419]" gap={16} size={1} />
                        <Controls className="bg-slate-800 border-slate-700" />
                    </ReactFlow>

                    {/* Legend / Overlay */}
                    <div className="absolute top-4 left-4 p-4 bg-slate-900/80 backdrop-blur rounded-lg border border-slate-700 pointer-events-none">
                        <div className="flex items-center gap-2 text-xs text-slate-300 mb-1">
                            <div className="w-3 h-3 rounded-full bg-slate-200"></div> MNX Logic
                        </div>
                        <div className="flex items-center gap-2 text-xs text-slate-300">
                            <div className="w-3 h-3 rounded-full bg-slate-200"></div> NMIE Execution
                        </div>
                    </div>
                </div>

                {/* Sidebar Details */}
                <div className="w-96 bg-[#1a1f26] flex flex-col">
                    <div className="p-4 border-b border-slate-700 font-semibold text-slate-300 flex items-center gap-2">
                        <FileText size={18} />
                        Artifact Inspector
                    </div>
                    <div className="flex-1 overflow-auto p-4">
                        {selectedNode ? (
                            <>
                                <h3 className="text-cyan-400 font-bold mb-4">{
                                    INITIAL_NODES.find(n => n.id === selectedNode)?.data.label
                                }</h3>

                                {loadingArtifact ? (
                                    <div className="text-slate-500 animate-pulse">Loading artifact data...</div>
                                ) : (
                                    <div className="text-sm">
                                        {artifactContent ? (
                                            <div className="bg-[#0d1117] rounded p-2 overflow-auto max-h-96">
                                                <SyntaxHighlighter language="json" style={vscDarkPlus} customStyle={{ background: 'transparent', padding: 0 }}>
                                                    {JSON.stringify(artifactContent, null, 2)}
                                                </SyntaxHighlighter>
                                            </div>
                                        ) : (
                                            <div className="text-slate-500 italic">Select a node to view outputs.</div>
                                        )}
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="text-slate-500 text-center mt-10">
                                <Layers size={48} className="mx-auto mb-4 opacity-20" />
                                <p>Select a pipeline node to view detailed artifacts, reports, and decision logic.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
