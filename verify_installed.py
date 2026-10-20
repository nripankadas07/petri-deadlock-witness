import hashlib,json,pathlib,subprocess,sys,tempfile
ROOT=pathlib.Path(__file__).absolute().parent
REPO=ROOT.name
PY=pathlib.Path(sys.argv[1]).absolute()
CMD=PY.parent/REPO
def check(path,expected,cwd):
 r=subprocess.run([str(CMD),str(path)],cwd=cwd,text=True,capture_output=True,timeout=20)
 if r.returncode!=expected:raise AssertionError((expected,r.returncode,r.stdout,r.stderr))
 if expected==2 and (not r.stderr or r.stdout):raise AssertionError('malformed input must have stderr and no partial report')
 return json.loads(r.stdout) if r.stdout else None
with tempfile.TemporaryDirectory(prefix='installed-example-') as tmp:
 t=pathlib.Path(tmp);p=t/'input.json';p.write_bytes((ROOT/'example.json').read_bytes());raw=p.read_bytes()
 expected=1 if REPO in ('dfa-inclusion-witness','petri-deadlock-witness') else 0
 out=check(p,expected,t)
 bad=json.loads(raw)
 if REPO=='sql-null-witness':
  assert out['kept_rows']==[2] and out['rows'][0]['result']=='UNKNOWN'
  bad['rows'][0]['score']='3'
 elif REPO=='activity-slack-report':
  assert out['minimum_finish']==10 and out['longest_chain']==['buy','build','review']
  bad['links'].append({'from':'review','to':'buy','lag':0})
 elif REPO=='turn-route-witness':
  assert out['route']['edges']==['ad','db','bc'] and out['extra_cost']==2
  bad['forbidden']=[['ab','db']]
 elif REPO=='dfa-inclusion-witness':
  assert out['counterexample_tokens']==['a','b'] and out['trace'][-1]['right'] is None
  bad['left']['transitions']*=2
 else:
  assert out['shortest_deadlock']['transitions']==['acquire'] and out['complete']
  bad['transitions'][0]['produce']['missing']=1
 f=t/'unsupported.json';f.write_text(json.dumps(bad));check(f,2,t)
 check(t/'missing.json',2,t)
 assert p.read_bytes()==raw
 print(json.dumps({'installed_console':True,'outside_checkout':True,'expected_results':True,'meaningful_failure_case':True,'source_unchanged':True,'input_sha256':hashlib.sha256(raw).hexdigest()}))
