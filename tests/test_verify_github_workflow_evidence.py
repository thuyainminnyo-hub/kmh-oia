import io
import json
import unittest

from scripts.verify_github_workflow_evidence import verify_bundle


REPO = "thuyainminnyo-hub/kmh-oia"
SHA = "a" * 40
SOURCE_SHA = "b" * 40
RUN_ID = "12345"
RUN_URL = f"https://github.com/{REPO}/actions/runs/{RUN_ID}"


def response(data):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps(data).encode("utf-8")
    return FakeResponse()


def fixture_bundle():
    names = [
        ("KMH OIA Tests", "tests"),
        ("KMH OIA Performance Evidence", "performance-evidence"),
        ("KMH OIA Repository Validation", "repository-validation"),
    ]
    return {
        "bundle_commit_sha": SHA,
        "source_head_sha": SOURCE_SHA,
        "gates": [{
            "gate": "repository_ci_for_bundle_commit",
            "evidence": [
                {
                    "name": display_name,
                    "url": RUN_URL,
                    "head_sha": SHA,
                    "conclusion": "success",
                    "is_required_check": True,
                }
                for display_name, _ in names
            ],
        }],
    }


def fake_opener_for(job_conclusion="success", run_sha=SOURCE_SHA):
    run_data = {
        "head_sha": run_sha,
        "html_url": RUN_URL,
        "repository": {"full_name": REPO},
    }
    jobs_data = {
        "jobs": [
            {"id": job_id, "name": job_id, "status": "completed",
             "conclusion": job_conclusion, "head_sha": run_sha}
            for job_id in ("tests", "performance-evidence", "repository-validation")
        ]
    }
    def opener(request, timeout=15):
        url = request.full_url
        if url.endswith(f"/actions/runs/{RUN_ID}"):
            return response(run_data)
        if url.endswith(f"/actions/runs/{RUN_ID}/jobs?per_page=100"):
            return response(jobs_data)
        raise AssertionError(f"Unexpected URL: {url}")
    return opener


class VerifyGitHubWorkflowEvidenceTests(unittest.TestCase):
    def test_accepts_run_and_job_evidence_matching_github_api(self):
        self.assertEqual(
            verify_bundle(fixture_bundle(), REPO, opener=fake_opener_for()),
            [],
        )

    def test_rejects_run_sha_mismatch(self):
        errors = verify_bundle(
            fixture_bundle(), REPO, opener=fake_opener_for(run_sha="c" * 40)
        )
        self.assertTrue(any("run 12345 head_sha" in error for error in errors))

    def test_rejects_required_job_failure(self):
        errors = verify_bundle(
            fixture_bundle(), REPO, opener=fake_opener_for(job_conclusion="failure")
        )
        self.assertTrue(any("did not succeed" in error for error in errors))
        self.assertTrue(any("conclusion does not match evidence" in error for error in errors))

    def test_rejects_noncanonical_or_wrong_repository_url(self):
        bundle = fixture_bundle()
        bundle["gates"][0]["evidence"][0]["url"] = "https://evil.example/actions/runs/12345"
        errors = verify_bundle(bundle, REPO, opener=fake_opener_for())
        self.assertTrue(any("canonical GitHub Actions run URL" in error for error in errors))

    def test_rejects_unknown_job_name(self):
        bundle = fixture_bundle()
        bundle["gates"][0]["evidence"][0]["name"] = "Made Up Check"
        errors = verify_bundle(bundle, REPO, opener=fake_opener_for())
        self.assertTrue(any("unknown job name" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
