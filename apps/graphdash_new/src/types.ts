export interface JobParams {
    tickers: string[];
    start_date: string;
    end_date: string;
    bar_size: string;
    strategies: string[];
    participation_cap: number;
    n_orders: number;
    model_params?: any;
}

export type JobType =
    | "INGEST" | "VALIDATE_DATA" | "BUILD_FEATURES"
    | "GENERATE_PARENT_ORDERS" | "BACKTEST_STRATEGIES"
    | "TCA_PIPELINE" | "RESEARCH_PIPELINE" | "GENERATE_REPORTS"
    | "FULL_RUN";

export interface Job {
    job_id: string;
    run_id: string;
    type: JobType;
    status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCELLED";
    created_at: string;
    finished_at?: string;
    error_msg?: string;
}

export interface Run {
    run_id: string;
    status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
    params: JobParams;
    created_at: string;
    jobs: string[];
    gate_decision?: string;
    gate_reason?: string;
    sensitivity_warning?: boolean;
}

export interface PipelineNode {
    id: string;
    label: string;
    description?: string;
}

export interface PipelineData {
    nodes: PipelineNode[];
    edges: { source: string, target: string }[];
    node_statuses: Record<string, string>;
}
