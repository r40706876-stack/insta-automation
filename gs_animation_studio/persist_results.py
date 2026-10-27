"""Persist only verified exports, or diagnostics. Retries never rerender or publish."""
import hashlib,json,os,shutil,subprocess,tempfile,time
from pathlib import Path
repo=Path.cwd()
def git(*args,cwd=repo):return subprocess.run(['git',*args],cwd=cwd,check=True,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
paths=[]
diag=Path(os.environ.get('STUDIO_DIAGNOSTICS','studio_diagnostics'))
if diag.is_dir() and not diag.is_absolute() and '..' not in diag.parts:paths.append(diag)
out=Path(os.environ.get('OUTPUT_PATH','__none__'))
if out.is_dir() and not out.is_absolute() and '..' not in out.parts and out.parts[:2]==('experiments','gs_animation_studio'):
 try:
  receipt=json.loads((out/'build_receipt.json').read_text());checks=json.loads((out/'file_checks.json').read_text());report=json.loads((out/'recovery_report.json').read_text())
  digest=hashlib.sha256((out/'final.mp4').read_bytes()).hexdigest()
  assert report['status']=='passed' and receipt['sha256']==checks['sha256']==report['sha256']==digest
  assert receipt['run_id']==os.environ['GITHUB_RUN_ID'] and receipt['instagram_publish'] is False
  paths.append(out)
 except Exception as e:print('Export not persisted as passing:',type(e).__name__)
if not paths:print('No output or diagnostics exist; earlier setup failure remains visible in Actions.');raise SystemExit(0)
work=Path(tempfile.mkdtemp(prefix='studio-save-'))/'tree'
try:
 git('fetch','origin','main');git('worktree','add','--detach',str(work),'origin/main')
 git('config','user.name','github-actions[bot]',cwd=work);git('config','user.email','github-actions[bot]@users.noreply.github.com',cwd=work)
 for rel in paths:
  target=work/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(repo/rel,target,dirs_exist_ok=True);git('add','--',str(rel),cwd=work)
 if not git('diff','--cached','--name-only',cwd=work).stdout.strip():raise SystemExit(0)
 git('commit','-m','Save Studio verified output and recovery diagnosis [skip ci]',cwd=work)
 for attempt in range(3):
  try:
   git('fetch','origin','main',cwd=work);git('rebase','origin/main',cwd=work);git('push','origin','HEAD:main',cwd=work);break
  except subprocess.CalledProcessError:
   if attempt==2:raise
   time.sleep(3)
finally:
 if work.exists():git('worktree','remove','--force',str(work))
