import copy,itertools,json,pathlib,random,sqlite3,subprocess,sys,tempfile,unittest
from petri_deadlock_witness import analyze
ROOT=pathlib.Path(__file__).absolute().parent
def example():return json.loads((ROOT/'example.json').read_text())
class Contract(unittest.TestCase):
    def test_strict_cli_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)/'bad.json'
            for raw in ('{', '{"x":1,"x":2}', '{"x":NaN}', '{}', ' '*1048577):
                p.write_text(raw);r=subprocess.run([sys.executable,str(ROOT/'petri_deadlock_witness.py'),str(p)],text=True,capture_output=True,timeout=5)
                self.assertEqual(r.returncode,2);self.assertTrue(r.stderr);self.assertFalse(r.stdout)
    def test_input_unchanged(self):
        x=example();saved=copy.deepcopy(x);analyze(x);self.assertEqual(x,saved)

    def test_shortest_deadlock_and_terminal(self):
        d=example();r=analyze(d);self.assertTrue(r['complete']);self.assertEqual(r['shortest_deadlock']['transitions'],['acquire'])
        d['terminal']=[{'idle':0,'held':1}];self.assertEqual(analyze(d)['status'],'no_deadlock')
    def test_unbounded_growth_is_unknown(self):
        d={'initial':{'p':0},'transitions':[{'id':'grow','consume':{},'produce':{'p':1}}],'token_limit':3,'state_limit':20};r=analyze(d);self.assertFalse(r['complete']);self.assertEqual(r['status'],'unknown');self.assertEqual(r['exit_code'],3)
    def test_state_bound_is_unknown(self):
        d=example();d['state_limit']=1;r=analyze(d);self.assertEqual(r['status'],'unknown');self.assertEqual(r['explored_states'],1)
    def test_cycle_complete(self):
        d=example();d['transitions'].append({'id':'release','consume':{'held':1},'produce':{'idle':1}});r=analyze(d);self.assertEqual(r['explored_states'],2);self.assertEqual(r['status'],'no_deadlock')
    def test_weighted_consumption_and_no_transition(self):
        d=example();d['transitions'][0]['consume']['idle']=2;r=analyze(d);self.assertEqual(r['shortest_deadlock']['transitions'],[]);self.assertEqual(r['never_enabled_in_explored_states'],['acquire'])
        d['transitions']=[];self.assertEqual(analyze(d)['status'],'deadlock_found')
    def test_unknown_arc_and_boolean(self):
        d=example();d['transitions'][0]['produce']={'unknown':1}
        with self.assertRaises(ValueError):analyze(d)
        d=example();d['token_limit']=True
        with self.assertRaises(ValueError):analyze(d)

if __name__ == '__main__':unittest.main()
