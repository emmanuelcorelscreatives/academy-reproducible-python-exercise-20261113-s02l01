"""One public, disposable GitHub-hosted Ubuntu course lab. No provider workflow."""
from pathlib import Path
import datetime, hashlib, json, os, re, resource, select, shutil, signal, subprocess, sys, time, uuid

ROOT=Path(__file__).resolve().parent
OUT=Path.cwd()/'lab-out'
OUT.mkdir(exist_ok=True)
(OUT/'captures').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
state={'at':now(),'kind':'ACTUAL_OWNED_STANDARD_GITHUB_TWIN_DOCKER7_LAB','runId':os.environ.get('GITHUB_RUN_ID'),'runAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'headSha':os.environ.get('GITHUB_SHA'),'commands':[],'captures':[],'captureErrors':[],'aiProviderCalls':0,'semanticTestsRun':0,'fullTeamWorkflowExecuted':False,'StudioHostChanges':False,'ephemeralRunnerPackageAndDockerChanges':False,'allRequestedOperationsCompleted':False}
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

TEMP=None; private_env=None; identity_container=None
try:
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    if not(os.environ.get('GITHUB_ACTIONS')=='true' and os.environ.get('RUNNER_ENVIRONMENT')=='github-hosted' and sys.platform=='linux' and os.environ.get('GITHUB_REPOSITORY')=='emmanuelcorelscreatives/academy-reproducible-python-exercise-20261113-s02l01' and os.environ.get('GITHUB_REF')=='refs/heads/academy-twin-docker7-20261113-v1' and os.environ.get('GITHUB_EVENT_NAME')=='push' and os.environ.get('GITHUB_RUN_ATTEMPT')=='1' and event['repository']['private'] is False):raise RuntimeError('Exact owned public standard hosted runner scope differs; never execute locally')
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):raise RuntimeError('No alternate daemon/context binding permitted')
    manifest=json.loads((ROOT/'public-inputs.json').read_text())
    for item in manifest['contextFiles']:
        if sha(ROOT/item['path'])!=item['sha256']:raise RuntimeError('Exact deliberate public input changed')
    state['exactPublicContext']=manifest
    state['preinstalledDockerUsedWithoutInstallOrContextReplay']=True;state['ephemeralRunnerPackageAndDockerChanges']=True
    # Capture tools only; no Docker repository/install/service/context/version work.
    run('capture-tool-index',['sudo','apt-get','update'],90)
    run('capture-tools-only',['sudo','apt-get','install','-y','xvfb','xterm','xdotool','python3-pil','fonts-dejavu-core'],120)
    TEMP=Path(os.environ['RUNNER_TEMP'])/('academy-twin-docker7-'+uuid.uuid4().hex);TEMP.mkdir(mode=0o700)
    context_dir=TEMP/'projects/01-digital-twin';context_dir.parent.mkdir();shutil.copytree(ROOT/'context',context_dir)
    fd_r,fd_w=os.pipe();xlog=(OUT/'xvfb.log').open('wb')
    xp=subprocess.Popen(['Xvfb','-displayfd',str(fd_w),'-screen','0','1920x1080x24','-nolisten','tcp'],pass_fds=(fd_w,),stdout=xlog,stderr=subprocess.STDOUT);owned.append(xp);os.close(fd_w)
    if not select.select([fd_r],[],[],8)[0]:raise RuntimeError('Original owned display unavailable')
    display=':'+os.read(fd_r,32).decode().strip();os.close(fd_r)
    os.chdir(context_dir)
    code,build_log=run('actual-one-exact-course-image-build',['sudo','docker','build','-t','academy-twin','.'],900,False,{'DOCKER_BUILDKIT':'1'})
    buildview=OUT/'actual-build-view.txt'
    lines=['Recorded actual output from THIS GitHub Ubuntu run '+str(state['runId'])+'.','Actual working directory: projects/01-digital-twin','$ sudo docker build -t academy-twin .','Actual build exit code: '+str(code),'']+build_log.read_text(errors='replace').splitlines()[-22:]
    buildview.write_text('\n'.join(lines)+'\n')
    terminal('s05l13-actual-one-docker-build',buildview,manifest['projectId'],'Exact unchanged public project image build command and real outcome; no fabricated logs')
    state['buildObserved']=True;state['buildExitCode']=code
    if code:raise RuntimeError('Original exact build failed; keep actual error, no retry or dependent container run')
    image=json.loads(text('actual-built-public-image-identity',['sudo','docker','image','inspect','academy-twin','--format','{{json .Id}}'],15))
    image_user=text('actual-image-service-user',['sudo','docker','image','inspect','academy-twin','--format','{{.Config.User}}'],15).strip()
    if not re.fullmatch('sha256:[0-9a-f]{64}',image) or image_user!='academy':raise RuntimeError('Actual image identity or nonprivileged service user differs')
    # Observe the REAL academy uid/gid once on this image, never guess ownership.
    identity_container='academy-twin-identity-'+uuid.uuid4().hex[:12]
    ids=json.loads(text('actual-image-academy-uid-gid',['sudo','docker','run','--rm','--name',identity_container,'--network=none','--entrypoint','python',image,'-c','import os,json;print(json.dumps({"uid":os.getuid(),"gid":os.getgid()}))'],15))
    if ids['uid']==0:raise RuntimeError('Image service user is privileged')
    data=TEMP/'private-data';data.mkdir(mode=0o700)
    run('prepare-exact-private-data-owner',['sudo','chown',str(ids['uid'])+':'+str(ids['gid']),str(data)],10)
    # Fresh fictional deployment authentication belongs only to this ephemeral run.
    # Never print values, pass them on argv, inspect raw Config.Env or export them.
    import secrets
    private_env=TEMP/'private-runtime.env'
    values={'TWIN_DATABASE':'/data/twin.sqlite','TWIN_PUBLIC_BIND':'true','TWIN_AUTH_USERNAME':'academy-'+secrets.token_hex(8),'TWIN_AUTH_PASSWORD':secrets.token_urlsafe(32),'TWIN_LIVE_MODEL_ENABLED':'false','TWIN_NOTIFICATION_MODE':'local_outbox','TWIN_RETENTION_DAYS':'30','TWIN_RATE_LIMIT':'30','GRADIO_ANALYTICS_ENABLED':'False','GRADIO_SERVER_PORT':'7860','PYTHONDONTWRITEBYTECODE':'1'}
    fd=os.open(private_env,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w')as f:f.write('\n'.join(k+'='+v for k,v in values.items())+'\n')
    container='academy-twin-'+uuid.uuid4().hex[:16]
    run('actual-one-owned-loopback-private-data-run',['sudo','docker','run','--detach','--name',container,'--label','academy.course.owner='+container,'--memory=2g','--cpus=2','--pids-limit=256','-p','127.0.0.1:7860:7860','--mount','type=bind,source='+str(data)+',target=/data','--env-file',str(private_env),'academy-twin'],30)
    time.sleep(12)
    # Only this allowlisted projection is retained. Raw inspect contains secrets.
    raw=subprocess.check_output(['sudo','docker','container','inspect',container],text=True,timeout=15);actual=json.loads(raw)[0]
    envdict=dict(x.split('=',1)for x in actual['Config']['Env']if'='in x)
    details={'Name':actual['Name'],'Id':actual['Id'],'Image':actual['Image'],'Running':actual['State']['Running'],'ExitCode':actual['State']['ExitCode'],'User':actual['Config']['User'],'WorkingDir':actual['Config']['WorkingDir'],'OwnerLabel':actual['Config']['Labels'].get('academy.course.owner'),'Mounts':[{k:m[k]for k in ['Type','Source','Destination','RW']}for m in actual['Mounts']],'PortBindings':actual['HostConfig']['PortBindings'],'TWIN_DATABASE':envdict.get('TWIN_DATABASE'),'TWIN_PUBLIC_BIND':envdict.get('TWIN_PUBLIC_BIND'),'TWIN_LIVE_MODEL_ENABLED':envdict.get('TWIN_LIVE_MODEL_ENABLED'),'TWIN_NOTIFICATION_MODE':envdict.get('TWIN_NOTIFICATION_MODE'),'authUsernameConfigured':bool(envdict.get('TWIN_AUTH_USERNAME')),'authPasswordAtLeast16':len(envdict.get('TWIN_AUTH_PASSWORD',''))>=16,'authValues':'REDACTED; actual owned private runtime file only','privateEnvironmentFileMode':oct(private_env.stat().st_mode&0o777),'imageServiceUid':ids['uid'],'imageServiceGid':ids['gid'],'publicHTTPSDeployment':False,'providerCalls':0}
    del raw,actual,envdict,values
    save('actual-owned-runtime-redacted.json',details)
    if not(details['Running'] and details['Image']==image and details['User']=='academy' and details['TWIN_DATABASE']=='/data/twin.sqlite' and details['TWIN_PUBLIC_BIND']=='true' and details['authUsernameConfigured'] and details['authPasswordAtLeast16'] and details['TWIN_LIVE_MODEL_ENABLED']=='false'):raise RuntimeError('Actual owned service/runtime configuration differs')
    if details['PortBindings']!={'7860/tcp':[{'HostIp':'127.0.0.1','HostPort':'7860'}]}:raise RuntimeError('Actual host mapping is not exact loopback-only')
    mount=next(m for m in details['Mounts']if m['Destination']=='/data')
    if not mount['RW'] or mount['Source']!=str(data):raise RuntimeError('Actual private mount differs')
    probe='import os,json,pathlib; p=pathlib.Path("/data/.academy-write-check"); p.write_text("fictional isolated course writability check\\n"); ok=p.read_text().startswith("fictional isolated course"); p.unlink(); print(json.dumps({"actualUid":os.getuid(),"actualGid":os.getgid(),"privateMountWritable":ok,"probeRemoved":not p.exists()}))'
    write=json.loads(text('actual-same-container-academy-writability',['sudo','docker','exec',container,'python','-c',probe],15));save('actual-private-mount-writability.json',write)
    if write['actualUid']!=ids['uid'] or not write['privateMountWritable'] or not write['probeRemoved']:raise RuntimeError('Actual service-user mount is not writable')
    view=OUT/'actual-runtime-redacted-view.txt'
    lines=['Recorded actual Docker configuration from THIS isolated Ubuntu run '+str(state['runId'])+'.','ONE image build; ONE app container; no public HTTPS deployment or provider call.','Actual image ID: '+image,'Actual container: '+details['Name'],'Running: '+str(details['Running'])+' | User: '+details['User']+' | uid/gid: '+str(ids['uid'])+'/'+str(ids['gid']),'Working directory: '+details['WorkingDir'],'Actual host mapping: -p 127.0.0.1:7860:7860','Actual private bind: '+str(data)+' -> /data | RW: True','TWIN_DATABASE=/data/twin.sqlite','TWIN_PUBLIC_BIND=true (container listener only; host mapping remains loopback)','TWIN_LIVE_MODEL_ENABLED=false | TWIN_NOTIFICATION_MODE=local_outbox','TWIN_AUTH_USERNAME=[REDACTED] | actually configured: True','TWIN_AUTH_PASSWORD=[REDACTED] | actual length >=16: True','Private runtime file mode: '+details['privateEnvironmentFileMode'],'Actual academy write probe: '+json.dumps(write,separators=(',',':')),'No contacts, stored records or auth values displayed.','Ten HTTPS visitor/session targets remain held; this is local container configuration.']
    view.write_text('\n'.join(lines)+'\n')
    terminal('s05l13-actual-private-mount-and-loopback-run',view,manifest['projectId'],'Actual same-image run, explicit private authentication presence, loopback mapping and academy writable private data')
    state['runtimeSevenObserved']=True;state['allRequestedOperationsCompleted']=True
except Exception as error:
    state['error']=str(error);state['errorAt']=now();state['allRequestedOperationsCompleted']=False
finally:
    cleanup=[]
    try:
        if container:
            r=subprocess.run(['sudo','docker','rm','-f',container],capture_output=True,timeout=25)
            c=subprocess.run(['sudo','docker','container','inspect',container],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=10)
            absent=c.returncode==1 and b'No such'in c.stderr;cleanup.append({'exactOwnedContainer':container,'removeExit':r.returncode,'absenceConfirmed':absent})
            if not absent:state['allRequestedOperationsCompleted']=False
        if identity_container:
            check=subprocess.run(['sudo','docker','container','inspect',identity_container],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=10)
            if check.returncode==0:subprocess.run(['sudo','docker','rm','-f',identity_container],capture_output=True,timeout=15)
            cleanup.append({'exactOwnedIdentityHelper':identity_container,'returnedAndAutoRemoved':check.returncode==1 and b'No such'in check.stderr})
        if private_env and private_env.exists():private_env.unlink();cleanup.append({'privateRuntimeFileRemoved':True})
        for p in reversed(owned):
            if p.poll()is None:
                p.terminate()
                try:p.wait(timeout=5)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    except Exception as error:cleanup.append({'cleanupError':str(error)});state['allRequestedOperationsCompleted']=False
    state['cleanup']=cleanup;state['finishedAt']=now();state['elapsedSeconds']=round(time.monotonic()-START,3);state['independentVisualPASSClaimed']=False
    save('job-state.json',state)
    files=[{'path':str(p.relative_to(OUT)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='output-manifest.json']
    save('output-manifest.json',{'at':now(),'runId':state['runId'],'headSha':state['headSha'],'files':files,'allRequestedOperationsCompleted':state['allRequestedOperationsCompleted'],'independentVisualPASSClaimed':False})
    print(json.dumps({'runId':state['runId'],'allRequestedOperationsCompleted':state['allRequestedOperationsCompleted'],'captures':len(state['captures']),'error':state.get('error'),'noAutomaticRerun':True}))
sys.exit(0 if state['allRequestedOperationsCompleted']else 1)
