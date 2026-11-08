CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    adapter_json TEXT NOT NULL DEFAULT '{}',
    ownership_state TEXT NOT NULL DEFAULT 'managed_new',
    ownership_reason TEXT,
    paused INTEGER NOT NULL DEFAULT 0,
    last_dispatch_seq INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS goals (
    project_id TEXT NOT NULL,
    goal_id TEXT NOT NULL,
    title TEXT NOT NULL,
    revision INTEGER NOT NULL,
    approved INTEGER NOT NULL,
    allowed_write_roots_json TEXT NOT NULL,
    acceptance_json TEXT NOT NULL,
    prohibited_json TEXT NOT NULL,
    max_tasks INTEGER NOT NULL,
    hold INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, goal_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE IF NOT EXISTS work_orders (
    project_id TEXT NOT NULL,
    work_order_id TEXT NOT NULL,
    goal_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    state TEXT NOT NULL,
    revision INTEGER NOT NULL,
    source_hash TEXT NOT NULL,
    write_scope_json TEXT NOT NULL,
    acceptance_json TEXT NOT NULL,
    idle_reason TEXT,
    reservation TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, work_order_id),
    FOREIGN KEY (project_id, goal_id) REFERENCES goals(project_id, goal_id)
);

CREATE TABLE IF NOT EXISTS stages (
    project_id TEXT NOT NULL,
    work_order_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    goal_id TEXT NOT NULL DEFAULT '',
    goal_revision INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    dependencies_json TEXT NOT NULL DEFAULT '[]',
    write_scope_json TEXT NOT NULL DEFAULT '[]',
    acceptance_json TEXT NOT NULL DEFAULT '[]',
    task_contract_json TEXT NOT NULL DEFAULT '{}',
    reservation TEXT,
    reserved_at REAL,
    reservation_owner_pid INTEGER,
    reservation_owner_identity TEXT,
    repair_count INTEGER NOT NULL DEFAULT 0,
    max_repairs INTEGER NOT NULL DEFAULT 2,
    created_seq INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, work_order_id, stage_id),
    FOREIGN KEY (project_id, work_order_id)
      REFERENCES work_orders(project_id, work_order_id)
);

CREATE TABLE IF NOT EXISTS runs (
    project_id TEXT NOT NULL,
    work_order_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    goal_id TEXT NOT NULL DEFAULT '',
    goal_revision INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    cwd TEXT NOT NULL,
    allowed_write_roots_json TEXT NOT NULL,
    evidence_dir TEXT NOT NULL,
    reservation TEXT NOT NULL,
    created_at REAL NOT NULL DEFAULT 0,
    pid INTEGER,
    process_identity TEXT,
    exit_code INTEGER,
    started_at REAL,
    finished_at REAL,
    receipt_status TEXT,
    receipt_evidence_json TEXT NOT NULL DEFAULT '[]',
    review_findings_json TEXT NOT NULL DEFAULT '[]',
    delivery_source_hash TEXT,
    acceptance_result_json TEXT NOT NULL DEFAULT '{}',
    transport_facts_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (project_id, work_order_id, stage_id, run_id),
    FOREIGN KEY (project_id, work_order_id, stage_id)
      REFERENCES stages(project_id, work_order_id, stage_id)
);
