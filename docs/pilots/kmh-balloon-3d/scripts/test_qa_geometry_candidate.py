#!/usr/bin/env python3
import json, subprocess, sys, tempfile
from pathlib import Path
SCRIPT=Path(__file__).with_name("qa_geometry_candidate.py")
BODY=Path("geometry/KMH_BAL_001_BODY_BLOCKOUT_v1.glb")
SKIRT=Path("geometry/KMH_BAL_001_LOWER_SKIRT_BLOCKOUT_v1.glb")
def run(root,state,out,body=BODY,skirt=SKIRT):
 return subprocess.run([sys.executable,str(SCRIPT),"--body",str(root/body),"--lower-skirt",str(root/skirt),"--state",state,"--output",str(out)],capture_output=True,text=True)
def main():
 root=Path("/mnt/data/KMH_Myanmar_Balloon_3D_Intelligence_Pilot")
 with tempfile.TemporaryDirectory() as td:
  td=Path(td); out=td/"valid.json"
  r=run(root,"BASE-UNLOADED",out); assert r.returncode==0,r.stdout+r.stderr
  d=json.loads(out.read_text()); assert d["body"]["structural_status"]=="PASS"
  assert d["lower_skirt"]["structural_status"]=="PASS" and d["promotion_authorized"] is False
  out=td/"unknown.json"; r=run(root,"UNKNOWN",out); assert r.returncode==1
  assert json.loads(out.read_text())["decision"]=="BLOCKED_HOLD"
  (td/"bad.glb").write_bytes(b"not a glb file")
  out=td/"bad.json"; r=run(td,"BASE-UNLOADED",out,Path("bad.glb"),SKIRT)
  assert r.returncode==1 and json.loads(out.read_text())["body"]["structural_status"]=="FAIL"
 print("3/3 QA pipeline tests passed.")
if __name__=="__main__":main()
