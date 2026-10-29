import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from scripts.comfyui_local_preflight import validate_local_config

class FakeResponse:
    def __init__(self, body): self.body=body
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def read(self,limit=-1): return self.body[:limit]

class ComfyUILocalPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.workflow=Path(self.temp.name)/"workflow.json"
        self.workflow.write_text(json.dumps({"6":{"class_type":"CLIPTextEncode","inputs":{"text":"synthetic"}},
                                              "9":{"class_type":"SaveImage","inputs":{"images":["6",0]}}}),encoding="utf-8")
    def test_rejects_nonlocal_url_without_network(self):
        self.assertTrue(any("local HTTP" in e for e in validate_local_config("https://example.com",self.workflow,"6")))
    def test_rejects_missing_prompt_input_without_network(self):
        self.assertTrue(any("prompt input key" in e for e in validate_local_config("http://127.0.0.1:8188",self.workflow,"6","missing")))
    @patch("scripts.comfyui_local_preflight.urlopen")
    def test_passes_when_node_classes_registered(self,mock_urlopen):
        mock_urlopen.return_value=FakeResponse(json.dumps({"CLIPTextEncode":{},"SaveImage":{}}).encode())
        self.assertEqual(validate_local_config("http://127.0.0.1:8188",self.workflow,"6"),[])
        self.assertIn("/object_info",mock_urlopen.call_args.args[0].full_url)
    @patch("scripts.comfyui_local_preflight.urlopen")
    def test_fails_for_unregistered_node_class(self,mock_urlopen):
        mock_urlopen.return_value=FakeResponse(json.dumps({"CLIPTextEncode":{}}).encode())
        self.assertTrue(any("unregistered class 'SaveImage'" in e for e in validate_local_config("http://127.0.0.1:8188",self.workflow,"6")))

if __name__=="__main__": unittest.main()
