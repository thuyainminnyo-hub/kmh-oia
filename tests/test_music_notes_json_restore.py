"""Browser JSON restore contract tests, run in Node VM without network access."""
import shutil
import subprocess
import unittest
from pathlib import Path

HTML = Path(__file__).resolve().parents[1] / "apps/music-notes/index.html"

NODE_TEST = r"""
const fs=require("node:fs"),vm=require("node:vm"),assert=require("node:assert/strict");
const html=fs.readFileSync(process.argv[1],"utf8");
const match=html.match(/<script>\s*([\s\S]*?)<\/script>/);
assert.ok(match,"inline script must exist");
const elements=new Map();
const doc={getElementById(id){
 if(!elements.has(id))elements.set(id,{addEventListener(){},files:[],disabled:false,textContent:"",innerHTML:"",value:""});
 return elements.get(id);
}};
const ctx={document:doc,indexedDB:{open(){return {}}},navigator:{},crypto:{},URL:{},Blob,TextEncoder,Uint8Array,DataView,Map,Set,Number,JSON,Array,Promise,Error,Date,
 window:{confirm(){return false}},console};
vm.createContext(ctx);
vm.runInContext(match[1],ctx,{filename:"apps/music-notes/index.html"});
const sample=()=>({
 schema_version:1,song_id:"candidate-1",title:"Sample",
 source_name:"sample.mid",source_sha256:"a".repeat(64),tonic:"C",mode:"major",
 status:"candidate",review_note:"",format_type:0,ticks_per_quarter:480,track_count:1,
 tempo_events:[[0,500000]],
 notes:[{track:0,channel:0,midi_pitch:60,velocity:64,start_tick:0,end_tick:480,
 start_seconds:0,end_seconds:0.5,pitch_name:"C4",octave:4,western_number:"1",sargam:"Sa"}]
});
const payload=()=>({schema_version:1,library_type:"kmh_music_intelligence_browser_candidates",songs:[sample()]});
const check = obj=>vm.runInContext("validateRestoreBackup("+JSON.stringify(obj)+")",ctx);
assert.equal(check(payload()).length,1);
const malformed=payload();malformed.schema_version=2;
assert.throws(()=>check(malformed),/backup schema/i);
const duplicate=payload();duplicate.songs.push(sample());
assert.throws(()=>check(duplicate),/duplicate candidate/i);
const polluted=payload();polluted.songs[0].notes[0]["__proto__bad"]="x";
assert.throws(()=>check(polluted),/invalid MIDI note/i);
const unsafe=payload();unsafe.songs[0].notes[0]["constructor"]="bad";
assert.throws(()=>check(unsafe),/unsafe key/i);
const tampered=payload();tampered.songs[0].notes[0].midi_pitch=129;
assert.throws(()=>check(tampered),/invalid MIDI note/i);
const invalidDigest=payload();invalidDigest.songs[0].source_sha256="not-a-digest";
assert.throws(()=>check(invalidDigest),/invalid candidate/i);
const invalidTempo=payload();invalidTempo.songs[0].tempo_events=[[0,0]];
assert.throws(()=>check(invalidTempo),/invalid tempo/i);
const extra=payload();extra.extra="unexpected";
assert.throws(()=>check(extra),/unexpected|schema/i);
const tooMany=payload();tooMany.songs[0].notes=Array(100001).fill(sample().notes[0]);
assert.throws(()=>check(tooMany),/too many notes/i);
assert.ok(html.includes('type="file" accept=".json,application/json"'));
assert.ok(html.includes('RESTORE_MAX_BYTES=5*1024*1024'));
assert.ok(html.includes('tx.oncomplete='));
assert.ok(html.includes('store.add(record)'));
assert.ok(html.includes('No existing candidate will be overwritten'));
process.stdout.write("VIS-DATA-001 Node VM validation and negative tests passed\n");
"""

class MusicNotesJsonRestoreTests(unittest.TestCase):
    def test_restore_validation_and_ui_contract(self):
        node = shutil.which("node")
        if node is None:
            self.skipTest("Node.js not available; browser JS behavioral test cannot run")
        result = subprocess.run(
            [node, "-e", NODE_TEST, str(HTML)], check=False,
            capture_output=True, text=True, timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)

if __name__ == "__main__":
    unittest.main()
