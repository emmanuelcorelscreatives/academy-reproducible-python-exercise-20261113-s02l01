"""One public, disposable GitHub-hosted Ubuntu course lab. No provider workflow."""
from pathlib import Path
import datetime, hashlib, json, os, re, resource, select, shutil, signal, subprocess, sys, time, uuid

ROOT=Path(__file__).resolve().parent
OUT=Path.cwd()/'lab-out'
OUT.mkdir(exist_ok=True)
(OUT/'captures').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
state={'at':now(),'kind':'ACTUAL_OWNED_STANDARD_GITHUB_RESEARCH_DOCKER3_LAB','runId':os.environ.get('GITHUB_RUN_ID'),'runAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'headSha':os.environ.get('GITHUB_SHA'),'commands':[],'captures':[],'captureErrors':[],'aiProviderCalls':0,'semanticTestsRun':0,'fullTeamWorkflowExecuted':False,'StudioHostChanges':False,'ephemeralRunnerPackageAndDockerChanges':False,'allRequestedOperationsCompleted':False}
owned=[]; display=None; container=None; mailbox=None; extract_container=None; hello=None
START=time.monotonic(); LIMIT=int(os.environ.get('ACADEMY_JOB_LIMIT_SECONDS','1800'))

def save(name,value):
    path=OUT/name
    path.write_text(json.dumps(value,indent=2)+'\n')
    return {'path':name,'sha256':sha(path)}

def run(name,args,seconds=120,check=True,extra=None):
    remaining=int(LIMIT-(time.monotonic()-START))
    if remaining<10:raise RuntimeError('Original finite job budget exhausted; no automatic rerun')
    path=OUT/(name+'.log')
    record={'name':name,'argv':args,'startedAt':now(),'deadlineSeconds':min(seconds,remaining),'path':path.name}
    state['commands'].append(record);save('job-state.json',state)
    proc=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env={**os.environ,**(extra or {})},start_new_session=True)
    stop_at=time.monotonic()+min(seconds,remaining);written=0
    try:
        with path.open('xb') as log:
            while True:
                if time.monotonic()>stop_at:raise TimeoutError('Original command timeout; outcome UNKNOWN, no replay')
                if select.select([proc.stdout],[],[],.2)[0]:
                    chunk=os.read(proc.stdout.fileno(),65536)
                    if not chunk:break
                    if written+len(chunk)>8*1024*1024:
                        log.write(chunk[:8*1024*1024-written]);raise RuntimeError('Original command output limit; preserve bounded partial log, no replay')
                    log.write(chunk);written+=len(chunk)
            code=proc.wait(timeout=5)
        record.update(exitCode=code,finishedAt=now(),sha256=sha(path))
    except Exception:
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait(timeout=5)
        record.update(exitCode=proc.returncode,outcome='BOUNDED_STOP_UNKNOWN_NO_REPLAY',finishedAt=now(),sha256=sha(path));save('job-state.json',state);raise
    save('job-state.json',state)
    if check and code:raise RuntimeError(name+' failed; retain the original outcome, no automatic rerun')
    return code,path

def text(name,args,seconds=30):
    _,path=run(name,args,seconds)
    return path.read_text()

def summary(name,command_names,extra=''):
    path=OUT/(name+'.txt')
    lines=['Recorded actual output from THIS disposable GitHub Ubuntu lab.', 'Run '+str(state['runId'])+'; commands below were executed once, not replayed for this view.','']
    for key in command_names:
        r=next(x for x in state['commands'] if x['name']==key)
        lines+=['$ '+' '.join(r['argv']), 'actual exit code: '+str(r.get('exitCode'))]
        raw=(OUT/r['path']).read_text(errors='replace').splitlines()
        lines+=raw[-20:]+['']
    if extra:lines+=extra.splitlines()
    path.write_text('\n'.join(lines)+'\n')
    return path

def app_window(pid=None,klass=None):
    args=['xdotool','search','--onlyvisible']
    args+=['--pid',str(pid)] if pid else ['--class',klass]
    deadline=time.monotonic()+12
    while time.monotonic()<deadline:
        r=subprocess.run(args,capture_output=True,text=True,env={**os.environ,'DISPLAY':display})
        ids=r.stdout.split()
        if ids:return ids[-1]
        time.sleep(.25)
    raise RuntimeError('Original owned capture window unavailable')

def capture_window(label,xid,project,operation):
    from PIL import ImageGrab
    env={**os.environ,'DISPLAY':display}
    def geometry():
        r=subprocess.run(['xdotool','getwindowgeometry','--shell',xid],capture_output=True,text=True,check=True,env=env)
        return dict(line.split('=',1)for line in r.stdout.splitlines()if '=' in line)
    before=geometry();pid=subprocess.check_output(['xdotool','getwindowpid',xid],env=env,text=True).strip()
    x,y,w,h=(int(before[k])for k in ['X','Y','WIDTH','HEIGHT'])
    if x<0 or y<0 or w<100 or h<100 or x+w>1920 or y+h>1080:raise RuntimeError('Owned native window exceeds actual display')
    path=OUT/'captures'/(label+'.png')
    ImageGrab.grab(bbox=(x,y,x+w,y+h),xdisplay=display).save(path)
    after=geometry()
    if before!=after:raise RuntimeError('Owned native window geometry changed during capture')
    state['captures'].append({'path':str(path.relative_to(OUT)),'sha256':sha(path),'projectId':project,'operation':operation,'captureMethod':'PIL ImageGrab actual owned Xvfb application window','xid':xid,'pid':pid,'geometry':{'x':x,'y':y,'width':w,'height':h},'actualPlatform':'Ubuntu 24.04 GitHub-hosted standard VM','newModelPass':False})
    save('capture-records.json',{'at':now(),'runId':state['runId'],'headSha':state['headSha'],'captures':state['captures'],'independentReviewClaimed':False})

def terminal(label,path,project,operation):
    p=subprocess.Popen(['xterm','-T','Academy actual hosted Ubuntu course lab','-fa','DejaVu Sans Mono','-fs','13','-b','50','-geometry','160x38+0+0','-hold','-e','/usr/bin/cat',str(path)],env={**os.environ,'DISPLAY':display},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    owned.append(p)
    try:
        xid=app_window(pid=p.pid);time.sleep(.8);capture_window(label,xid,project,operation)
    finally:
        if p.poll() is None:p.terminate();p.wait(timeout=5)

try:
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    if not(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted' and sys.platform=='linux' and os.environ.get('GITHUB_REPOSITORY')=='emmanuelcorelscreatives/academy-reproducible-python-exercise-20261113-s02l01' and os.environ.get('GITHUB_REF')=='refs/heads/academy-research-docker3-20261113-v1' and os.environ.get('GITHUB_EVENT_NAME')=='push' and os.environ.get('GITHUB_RUN_ATTEMPT')=='1' and event['repository']['private'] is False):raise RuntimeError('Exact public hosted build-only scope differs; never execute locally')
    if os.environ.get('DOCKER_HOST')or os.environ.get('DOCKER_CONTEXT'):raise RuntimeError('No alternate Docker route permitted')
    manifest=json.loads((ROOT/'public-inputs.json').read_text());state['exactPublicInputs']=manifest
    for item in manifest['contextFiles']:
        if sha(ROOT/item['path'])!=item['sha256']:raise RuntimeError('Exact public source bytes changed')
    state['preinstalledDockerUsedWithoutInstallOrContextReplay']=True
    run('capture-tool-index',['sudo','apt-get','update'],90)
    run('capture-tools-only',['sudo','apt-get','install','-y','xvfb','xterm','xdotool','python3-pil','fonts-dejavu-core'],120)
    state['ephemeralRunnerPackageAndDockerChanges']=True
    TEMP=Path(os.environ['RUNNER_TEMP'])/('academy-research-docker3-'+uuid.uuid4().hex);TEMP.mkdir(mode=0o700)
    context_dir=TEMP/'projects/03-deep-research';context_dir.parent.mkdir();shutil.copytree(ROOT/'context',context_dir)
    fd_r,fd_w=os.pipe();xlog=(OUT/'xvfb.log').open('wb')
    xp=subprocess.Popen(['Xvfb','-displayfd',str(fd_w),'-screen','0','1920x1080x24','-nolisten','tcp'],pass_fds=(fd_w,),stdout=xlog,stderr=subprocess.STDOUT);owned.append(xp);os.close(fd_w)
    if not select.select([fd_r],[],[],8)[0]:raise RuntimeError('Owned native display unavailable')
    display=':'+os.read(fd_r,32).decode().strip();os.close(fd_r)
    os.chdir(context_dir);iid=OUT/'actual-research-v3-image-id.txt'
    argv=['sudo','docker','build','--progress=plain','--file','deployment/research-v3/Dockerfile','--iidfile',str(iid),'.']
    code,build_log=run('actual-one-exact-research-v3-docker-build',argv,900,False,{'DOCKER_BUILDKIT':'1'})
    image=iid.read_text().strip()if iid.is_file()else None
    state['actualBuildExitCode']=code;state['actualImageId']=image
    if code==0:
        if not image or not re.fullmatch('sha256:[0-9a-f]{64}',image):raise RuntimeError('Successful build returned no actual immutable image identity')
        observed=json.loads(text('actual-built-research-v3-image-inspect',['sudo','docker','image','inspect',image,'--format','{{json .}}'],20))
        save('actual-research-v3-image-identity.json',{'Id':observed['Id'],'RepoDigests':observed.get('RepoDigests',[]),'User':observed['Config']['User'],'WorkingDir':observed['Config']['WorkingDir'],'ExposedPorts':observed['Config'].get('ExposedPorts'),'imageBuiltOnly':True,'containerOrProviderStartupPerformed':False})
    for item in manifest['contextFiles']:
        if sha(context_dir/Path(item['path']).relative_to('context'))!=item['sha256']:raise RuntimeError('Original context mutated; never regenerate lock')
    view=OUT/'actual-research-build-readable.txt'
    lines=['Recorded actual output from original GitHub Ubuntu run '+str(state['runId'])+'.','Working directory/context: projects/03-deep-research','$ sudo docker build --progress=plain --file deployment/research-v3/Dockerfile --iidfile <owned-output>/actual-research-v3-image-id.txt .','Actual original build exit code: '+str(code),'Unchanged actual lock SHA256: '+manifest['requirementsLockMustNotRegenerate'],'Actual resulting image identity: '+str(image),'Build-only operation: no application/container start, provider, Brave, live browser or exports.','Raw original terminal log excerpt (full raw output retained separately):','']+build_log.read_text(errors='replace').splitlines()[-9:]
    view.write_text('\n'.join(lines)+'\n')
    terminal('s10l10-actual-exact-locked-docker-build',view,manifest['projectId'],'Actual selected research-v3 Dockerfile build, unchanged hash-lock and real resulting image identity or failure')
    state['requestedBuildOperationObserved']=True;state['allRequestedOperationsCompleted']=code==0
    if code:state['error']='Original exact locked build failed; actual error retained, no automatic retry or version change'
except Exception as error:
    state['error']=str(error);state['errorAt']=now();state['allRequestedOperationsCompleted']=False
finally:
    cleanup=[]
    for p in reversed(owned):
        if p.poll()is None:
            p.terminate()
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    state['cleanup']={'ownedProcessesTerminal':all(p.poll()is not None for p in owned),'noApplicationContainersStarted':True,'hostChanges':False};state['finishedAt']=now();state['elapsedSeconds']=round(time.monotonic()-START,3);state['independentVisualPASSClaimed']=False
    save('job-state.json',state)
    files=[{'path':str(p.relative_to(OUT)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='output-manifest.json']
    save('output-manifest.json',{'at':now(),'runId':state['runId'],'headSha':state['headSha'],'files':files,'allRequestedOperationsCompleted':state['allRequestedOperationsCompleted'],'independentVisualPASSClaimed':False})
    print(json.dumps({'runId':state['runId'],'allRequestedOperationsCompleted':state['allRequestedOperationsCompleted'],'captures':len(state['captures']),'error':state.get('error'),'noAutomaticRerun':True}))
sys.exit(0 if state['allRequestedOperationsCompleted']else 1)
