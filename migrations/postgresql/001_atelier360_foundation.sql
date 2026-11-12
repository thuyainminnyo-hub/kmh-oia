-- KAE-FAS-001 / NM-BLS-001
-- PostgreSQL 16+ compatible foundation. Apply only to a dedicated sandbox database.
-- This migration creates structures; it does not connect to or modify production systems.
BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS atelier360;

CREATE TYPE atelier360.record_status AS ENUM
 ('draft','in_review','approved','held','rejected','released','archived');
CREATE TYPE atelier360.agent_status AS ENUM ('active','suspended','revoked');
CREATE TYPE atelier360.autonomy_mode AS ENUM ('controlled');
CREATE TYPE atelier360.event_outcome AS ENUM ('accepted','denied','failed','held');
CREATE TYPE atelier360.approval_status AS ENUM ('pending','approved','rejected','expired','revoked');
CREATE TYPE atelier360.qa_disposition AS ENUM ('pending','pass','fail','rework','hold');

CREATE TABLE atelier360.organizations (
 organization_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 code text NOT NULL UNIQUE,
 name text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE atelier360.actors (
 actor_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 external_subject text NOT NULL,
 display_name text NOT NULL,
 actor_type text NOT NULL CHECK (actor_type IN ('human','service')),
 active boolean NOT NULL DEFAULT true,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (organization_id, external_subject)
);

CREATE TABLE atelier360.agent_registry (
 agent_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 agent_code text NOT NULL,
 display_name text NOT NULL,
 purpose text NOT NULL,
 status atelier360.agent_status NOT NULL DEFAULT 'active',
 autonomy atelier360.autonomy_mode NOT NULL DEFAULT 'controlled',
 model_provider text,
 model_name text,
 model_version text,
 prompt_version text NOT NULL,
 allowed_tools text[] NOT NULL DEFAULT '{}',
 created_by uuid NOT NULL REFERENCES atelier360.actors,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (organization_id, agent_code)
);

CREATE TABLE atelier360.permissions (
 permission_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 permission_code text NOT NULL UNIQUE,
 resource_type text NOT NULL,
 action text NOT NULL,
 risk_level text NOT NULL CHECK (risk_level IN ('low','medium','high','critical')),
 approval_required boolean NOT NULL DEFAULT true,
 description text NOT NULL
);

CREATE TABLE atelier360.agent_permission_grants (
 grant_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 agent_id uuid NOT NULL REFERENCES atelier360.agent_registry,
 permission_id uuid NOT NULL REFERENCES atelier360.permissions,
 granted_by uuid NOT NULL REFERENCES atelier360.actors,
 valid_from timestamptz NOT NULL DEFAULT now(),
 expires_at timestamptz NOT NULL,
 revoked_at timestamptz,
 CHECK (expires_at > valid_from),
 CHECK (revoked_at IS NULL OR revoked_at >= valid_from)
);
CREATE INDEX agent_grants_active_idx ON atelier360.agent_permission_grants(agent_id, permission_id, expires_at) WHERE revoked_at IS NULL;

CREATE TABLE atelier360.product_models (
 model_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 model_code text NOT NULL,
 brand_code text NOT NULL,
 product_name text NOT NULL,
 design_version text NOT NULL,
 pattern_version text,
 status atelier360.record_status NOT NULL DEFAULT 'draft',
 description text,
 created_by uuid NOT NULL REFERENCES atelier360.actors,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE (organization_id, model_code, design_version)
);

CREATE TABLE atelier360.design_versions (
 design_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 model_id uuid NOT NULL REFERENCES atelier360.product_models,
 version text NOT NULL,
 asset_uri text,
 content_sha256 char(64),
 status atelier360.record_status NOT NULL DEFAULT 'draft',
 approved_by uuid REFERENCES atelier360.actors,
 approved_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(model_id, version),
 CHECK ((status <> 'approved' AND status <> 'released') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE TABLE atelier360.pattern_versions (
 pattern_version_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 model_id uuid NOT NULL REFERENCES atelier360.product_models,
 version text NOT NULL,
 asset_uri text,
 content_sha256 char(64),
 technical_review_by uuid REFERENCES atelier360.actors,
 technical_review_at timestamptz,
 status atelier360.record_status NOT NULL DEFAULT 'draft',
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(model_id, version),
 CHECK (status NOT IN ('approved','released') OR (technical_review_by IS NOT NULL AND technical_review_at IS NOT NULL))
);

CREATE TABLE atelier360.materials (
 material_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 material_code text NOT NULL,
 description text NOT NULL,
 fibre_composition jsonb NOT NULL DEFAULT '{}'::jsonb,
 supplier_reference text,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(organization_id, material_code),
 CHECK (jsonb_typeof(fibre_composition) = 'object')
);

CREATE TABLE atelier360.boms (
 bom_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 model_id uuid NOT NULL REFERENCES atelier360.product_models,
 version text NOT NULL,
 status atelier360.record_status NOT NULL DEFAULT 'draft',
 approved_by uuid REFERENCES atelier360.actors,
 approved_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(model_id, version),
 CHECK (status NOT IN ('approved','released') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE TABLE atelier360.bom_lines (
 bom_line_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 bom_id uuid NOT NULL REFERENCES atelier360.boms ON DELETE RESTRICT,
 material_id uuid NOT NULL REFERENCES atelier360.materials,
 quantity numeric(14,4) NOT NULL CHECK (quantity > 0),
 unit text NOT NULL,
 notes text,
 UNIQUE(bom_id, material_id)
);

CREATE TABLE atelier360.production_batches (
 batch_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 batch_code text NOT NULL,
 model_id uuid NOT NULL REFERENCES atelier360.product_models,
 design_version_id uuid NOT NULL REFERENCES atelier360.design_versions,
 pattern_version_id uuid NOT NULL REFERENCES atelier360.pattern_versions,
 bom_id uuid NOT NULL REFERENCES atelier360.boms,
 planned_quantity integer NOT NULL CHECK (planned_quantity > 0),
 approved_quantity integer CHECK (approved_quantity > 0),
 status atelier360.record_status NOT NULL DEFAULT 'draft',
 work_order_code text UNIQUE,
 approved_by uuid REFERENCES atelier360.actors,
 approved_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(organization_id, batch_code),
 CHECK (approved_quantity IS NULL OR approved_quantity <= planned_quantity),
 CHECK (status NOT IN ('approved','released') OR (approved_quantity IS NOT NULL AND approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE TABLE atelier360.material_lots (
 material_lot_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 material_id uuid NOT NULL REFERENCES atelier360.materials,
 supplier_lot_code text NOT NULL,
 received_quantity numeric(14,4) NOT NULL CHECK (received_quantity >= 0),
 unit text NOT NULL,
 received_at timestamptz,
 evidence_uri text,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(material_id, supplier_lot_code)
);

CREATE TABLE atelier360.batch_material_allocations (
 allocation_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 batch_id uuid NOT NULL REFERENCES atelier360.production_batches,
 material_lot_id uuid NOT NULL REFERENCES atelier360.material_lots,
 allocated_quantity numeric(14,4) NOT NULL CHECK (allocated_quantity > 0),
 unit text NOT NULL,
 UNIQUE(batch_id, material_lot_id)
);

CREATE TABLE atelier360.individual_items (
 item_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 batch_id uuid NOT NULL REFERENCES atelier360.production_batches,
 item_code text NOT NULL UNIQUE,
 serial_number text NOT NULL UNIQUE,
 status atelier360.record_status NOT NULL DEFAULT 'draft',
 qa_disposition atelier360.qa_disposition NOT NULL DEFAULT 'pending',
 created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE atelier360.approvals (
 approval_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 subject_type text NOT NULL,
 subject_id uuid NOT NULL,
 action text NOT NULL,
 status atelier360.approval_status NOT NULL DEFAULT 'pending',
 requested_by_actor_id uuid NOT NULL REFERENCES atelier360.actors,
 decided_by_actor_id uuid REFERENCES atelier360.actors,
 rationale text,
 requested_at timestamptz NOT NULL DEFAULT now(),
 decided_at timestamptz,
 expires_at timestamptz,
 CHECK ((status <> 'approved' AND status <> 'rejected') OR (decided_by_actor_id IS NOT NULL AND decided_at IS NOT NULL)),
 CHECK (decided_at IS NULL OR decided_at >= requested_at)
);
CREATE INDEX approvals_subject_idx ON atelier360.approvals(subject_type, subject_id, requested_at DESC);

CREATE TABLE atelier360.evidence_records (
 evidence_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 evidence_type text NOT NULL,
 subject_type text NOT NULL,
 subject_id uuid NOT NULL,
 storage_uri text NOT NULL,
 media_type text,
 sha256 char(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
 captured_by_actor_id uuid NOT NULL REFERENCES atelier360.actors,
 captured_at timestamptz NOT NULL DEFAULT now(),
 metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
 CHECK (jsonb_typeof(metadata) = 'object')
);
CREATE INDEX evidence_subject_idx ON atelier360.evidence_records(subject_type, subject_id, captured_at DESC);

CREATE TABLE atelier360.production_events (
 event_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 event_code text NOT NULL,
 subject_type text NOT NULL,
 subject_id uuid NOT NULL,
 actor_id uuid REFERENCES atelier360.actors,
 agent_id uuid REFERENCES atelier360.agent_registry,
 outcome atelier360.event_outcome NOT NULL,
 occurred_at timestamptz NOT NULL DEFAULT now(),
 correlation_id uuid NOT NULL,
 idempotency_key text NOT NULL,
 approval_id uuid REFERENCES atelier360.approvals,
 evidence_id uuid REFERENCES atelier360.evidence_records,
 payload jsonb NOT NULL DEFAULT '{}'::jsonb,
 previous_hash char(64),
 event_hash char(64) NOT NULL,
 UNIQUE(organization_id, idempotency_key),
 CHECK (num_nonnulls(actor_id, agent_id) = 1),
 CHECK (jsonb_typeof(payload) = 'object')
);
CREATE INDEX production_events_subject_idx ON atelier360.production_events(subject_type, subject_id, occurred_at);
CREATE INDEX production_events_correlation_idx ON atelier360.production_events(correlation_id);

CREATE TABLE atelier360.qa_inspections (
 inspection_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 item_id uuid NOT NULL REFERENCES atelier360.individual_items,
 inspector_actor_id uuid NOT NULL REFERENCES atelier360.actors,
 disposition atelier360.qa_disposition NOT NULL,
 checklist_version text NOT NULL,
 findings jsonb NOT NULL DEFAULT '[]'::jsonb,
 evidence_id uuid REFERENCES atelier360.evidence_records,
 inspected_at timestamptz NOT NULL DEFAULT now(),
 CHECK (jsonb_typeof(findings) = 'array'),
 CHECK (disposition <> 'pass' OR evidence_id IS NOT NULL)
);

CREATE TABLE atelier360.ip_assets (
 ip_asset_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 organization_id uuid NOT NULL REFERENCES atelier360.organizations,
 asset_code text NOT NULL,
 asset_type text NOT NULL,
 title text NOT NULL,
 asset_uri text,
 content_sha256 char(64),
 rights_status text NOT NULL DEFAULT 'unverified' CHECK (rights_status IN ('unverified','documented','licensed','assigned','disputed')),
 rights_evidence_id uuid REFERENCES atelier360.evidence_records,
 created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(organization_id, asset_code)
);

CREATE TABLE atelier360.dpp_records (
 dpp_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 item_id uuid NOT NULL UNIQUE REFERENCES atelier360.individual_items,
 schema_version text NOT NULL,
 payload jsonb NOT NULL,
 publication_status text NOT NULL DEFAULT 'draft' CHECK (publication_status IN ('draft','review','approved','published','withdrawn')),
 approved_by uuid REFERENCES atelier360.actors,
 approved_at timestamptz,
 published_at timestamptz,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK (jsonb_typeof(payload) = 'object'),
 CHECK (publication_status NOT IN ('approved','published') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)),
 CHECK (publication_status <> 'published' OR published_at IS NOT NULL)
);

-- Default-deny RLS: application roles must receive explicit policies in a later
-- environment-specific deployment migration. Table owners/superusers can bypass RLS.
DO $$
DECLARE t text;
BEGIN
 FOREACH t IN ARRAY ARRAY[
  'organizations','actors','agent_registry','permissions','agent_permission_grants',
  'product_models','design_versions','pattern_versions','materials','boms','bom_lines',
  'production_batches','material_lots','batch_material_allocations','individual_items',
  'approvals','evidence_records','production_events','qa_inspections','ip_assets','dpp_records'
 ] LOOP
  EXECUTE format('ALTER TABLE atelier360.%I ENABLE ROW LEVEL SECURITY', t);
 END LOOP;
END $$;

-- Audit/evidence is append-only for ordinary application roles.
CREATE OR REPLACE FUNCTION atelier360.reject_mutation()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
 RAISE EXCEPTION 'append-only table: % cannot be changed', TG_TABLE_NAME;
END $$;
CREATE TRIGGER evidence_no_update_delete
 BEFORE UPDATE OR DELETE ON atelier360.evidence_records
 FOR EACH ROW EXECUTE FUNCTION atelier360.reject_mutation();
CREATE TRIGGER events_no_update_delete
 BEFORE UPDATE OR DELETE ON atelier360.production_events
 FOR EACH ROW EXECUTE FUNCTION atelier360.reject_mutation();

COMMIT;
