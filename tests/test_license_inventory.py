import json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.validate_license_inventory import audit

class LicenseInventoryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.s=self.root/'s.json'; self.i=self.root/'i.json'
  self.s.write_text(json.dumps({'packages':[{'name':'actions/checkout','versionInfo':'v7.0.1','licenseDeclared':'NOASSERTION','licenseConcluded':'NOASSERTION'},{'name':'.','versionInfo':None}]}))
  self.i.write_text(json.dumps({'entries':[{'name':'actions/checkout','version':'v7.0.1','license':'MIT','review_status':'VERIFIED','evidence_url':'https://github.com/actions/checkout/blob/v7.0.1/LICENSE'},{'name':'.','version':None,'license':'UNDECLARED','review_status':'OWNER_DECISION_REQUIRED'}]}))
 def tearDown(self): self.tmp.cleanup()
 def test_verified_external_and_owner_hold(self):
  r=audit(self.s,self.i); self.assertEqual(r['status'],'REVIEW_REQUIRED'); self.assertEqual(r['external_packages_verified'],1); self.assertEqual(r['project_license_status'],'OWNER_DECISION_REQUIRED')
 def test_unreviewed_external_holds(self):
  d=json.loads(self.i.read_text()); d['entries'][0]['review_status']='PENDING'; self.i.write_text(json.dumps(d)); self.assertEqual(audit(self.s,self.i)['status'],'HOLD')
 def test_missing_project_entry_holds(self):
  d=json.loads(self.i.read_text()); d['entries']=d['entries'][:1]; self.i.write_text(json.dumps(d)); self.assertEqual(audit(self.s,self.i)['status'],'HOLD')

if __name__=='__main__': unittest.main()
