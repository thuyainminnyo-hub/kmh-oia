CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS areas_of_interest (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  geom geometry(MultiPolygon, 4326) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT aoi_geom_valid CHECK (ST_IsValid(geom)),
  CONSTRAINT aoi_geom_nonempty CHECK (NOT ST_IsEmpty(geom))
);
CREATE INDEX IF NOT EXISTS idx_aoi_geom ON areas_of_interest USING GIST (geom);

CREATE TABLE IF NOT EXISTS satellite_scenes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider TEXT NOT NULL,
  collection TEXT NOT NULL,
  item_id TEXT NOT NULL,
  acquired_at TIMESTAMPTZ NOT NULL,
  cloud_cover DOUBLE PRECISION,
  footprint geometry(MultiPolygon, 4326),
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  asset_manifest JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(provider, collection, item_id)
);
CREATE INDEX IF NOT EXISTS idx_scenes_acquired_at ON satellite_scenes(acquired_at);
CREATE INDEX IF NOT EXISTS idx_scenes_footprint ON satellite_scenes USING GIST (footprint);

CREATE TABLE IF NOT EXISTS analysis_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  aoi_id UUID NOT NULL REFERENCES areas_of_interest(id),
  baseline_scene_id UUID REFERENCES satellite_scenes(id),
  comparison_scene_id UUID REFERENCES satellite_scenes(id),
  status TEXT NOT NULL DEFAULT 'queued'
    CHECK (status IN ('queued','discovering','processing','qa_pending','needs_review','verified','rejected','failed')),
  parameters_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_runs_aoi_created ON analysis_runs(aoi_id, created_at DESC);

CREATE TABLE IF NOT EXISTS artifacts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
  artifact_type TEXT NOT NULL,
  object_uri TEXT NOT NULL,
  checksum_sha256 TEXT NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS qa_checks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
  check_name TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pass','fail','warning','not_run')),
  measured_value JSONB,
  threshold JSONB,
  details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS review_decisions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID NOT NULL REFERENCES analysis_runs(id) ON DELETE CASCADE,
  reviewer TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('approve','reject','request_reprocess')),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS audit_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  run_id UUID REFERENCES analysis_runs(id) ON DELETE SET NULL,
  event_type TEXT NOT NULL,
  actor TEXT NOT NULL,
  payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_run_created ON audit_events(run_id, created_at);
