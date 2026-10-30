#!/usr/bin/env ruby
# frozen_string_literal: true

require "yaml"

SHA40 = /\A[0-9a-fA-F]{40}\z/

def remote_reusable_workflow?(reference)
  reference.match?(%r{\A[^/\s]+/[^/\s]+/\.github/workflows/[^@\s]+@[^@\s]+\z})
end

def validate_workflow(path)
  document = YAML.load_file(path)
  jobs = document.is_a?(Hash) ? document["jobs"] : nil
  return [] unless jobs.is_a?(Hash)

  failures = []
  jobs.each do |job_id, job|
    next unless job.is_a?(Hash)

    reference = job["uses"]
    next unless reference.is_a?(String) && remote_reusable_workflow?(reference)

    ref = reference.split("@", 2).last
    next if SHA40.match?(ref)

    failures << "#{path}: job '#{job_id}' uses '#{reference}' (remote reusable workflow must be pinned to a full 40-character commit SHA)"
  end
  failures
rescue Psych::Exception => e
  ["#{path}: YAML parse error: #{e.message}"]
end

workflow_files = Dir.glob(".github/workflows/*.{yml,yaml}").sort
if workflow_files.empty?
  warn "No GitHub Actions workflow files found under .github/workflows/"
  exit 1
end

failures = workflow_files.flat_map { |path| validate_workflow(path) }
if failures.empty?
  puts "PASS: all remote reusable workflow references use full 40-character commit SHAs (#{workflow_files.length} workflow files checked)."
  exit 0
end

warn "FAIL: unpinned remote reusable workflow references found:"
failures.each { |failure| warn " - #{failure}" }
exit 1
