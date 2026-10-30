# frozen_string_literal: true

require "minitest/autorun"
require "tmpdir"
require "fileutils"
require_relative "../scripts/check_reusable_workflow_shas"

class ReusableWorkflowShaGateTest < Minitest::Test
  def with_workflow(yaml)
    Dir.mktmpdir do |dir|
      path = File.join(dir, "workflow.yml")
      File.write(path, yaml)
      yield path
    end
  end

  def test_rejects_tag_reference
    with_workflow(<<~YAML) do |path|
      jobs:
        call:
          uses: octo-org/shared/.github/workflows/build.yml@v2
    YAML
      failures = validate_workflow(path)
      assert_equal 1, failures.length
      assert_match(/full 40-character commit SHA/, failures.first)
    end
  end

  def test_accepts_full_commit_sha
    sha = "0123456789abcdef0123456789abcdef01234567"
    with_workflow(<<~YAML) do |path|
      jobs:
        call:
          uses: octo-org/shared/.github/workflows/build.yml@#{sha}
    YAML
      assert_empty validate_workflow(path)
    end
  end

  def test_ignores_step_level_actions
    with_workflow(<<~YAML) do |path|
      jobs:
        build:
          steps:
            - uses: actions/checkout@v4
    YAML
      assert_empty validate_workflow(path)
    end
  end

  def test_ignores_same_repository_reference
    with_workflow(<<~YAML) do |path|
      jobs:
        call:
          uses: $/.github/workflows/build.yml
    YAML
      assert_empty validate_workflow(path)
    end
  end
end
