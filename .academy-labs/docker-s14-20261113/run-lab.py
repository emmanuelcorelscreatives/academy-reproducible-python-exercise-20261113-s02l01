"""One public, disposable GitHub-hosted Ubuntu course lab. No provider workflow."""
from pathlib import Path
import datetime, hashlib, json, os, re, resource, select, shutil, signal, subprocess, sys, time, uuid

ROOT=Path(__file__).resolve().parent
OUT=Path.cwd()/'lab-out'
OUT.mkdir(exist_ok=True)
(OUT/'captures').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.datetime.now(datetime.timezone.utc).isoformat()
state={'at':now(),'kind':'ACTUAL_OWNED_STANDARD_GITHUB_UBUNTU_COURSE_LAB','runId':os.environ.get('GITHUB_RUN_ID'),'runAttempt':os.environ.get('GITHUB_RUN_ATTEMPT'),'headSha':os.environ.get('GITHUB_SHA'),'commands':[],'captures':[],'captureErrors':[],'aiProviderCalls':0,'semanticTestsRun':0,'fullTeamWorkflowExecuted':False,'StudioHostChanges':False,'ephemeralRunnerPackageAndDockerChanges':False,'allRequestedOperationsCompleted':False}
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

def browser_views():
    binary=shutil.which('google-chrome') or shutil.which('chromium')
    if not binary:raise RuntimeError('Hosted image has no existing Chrome/Chromium; no browser result fabricated')
    state['browserVersion']=subprocess.check_output([binary,'--version'],text=True).strip()
    profile=TEMP/'browser-profile'
    p=subprocess.Popen([binary,'--user-data-dir='+str(profile),'--no-first-run','--disable-default-apps','--disable-background-networking','--disable-dev-shm-usage','--window-size=1920,1080','--window-position=0,0','--class=AcademyDockerLabBrowser','https://docs.docker.com/engine/install/ubuntu/#os-requirements'],env={**os.environ,'DISPLAY':display},stdout=subprocess.DEVNULL,stderr=(OUT/'browser.log').open('wb'))
    owned.append(p)
    try:
        xid=app_window(klass='AcademyDockerLabBrowser');time.sleep(8)
        capture_window('s14l03-official-ubuntu-prerequisites',xid,'cmwf8utho004h5c8cz7kzy983','Actual official Docker Ubuntu prerequisite page; requested URL recorded, page judged from genuine pixels')
        env={**os.environ,'DISPLAY':display}
        subprocess.run(['xdotool','windowfocus','--sync',xid],env=env,check=True)
        subprocess.run(['xdotool','key','--window',xid,'ctrl+l'],env=env,check=True)
        subprocess.run(['xdotool','type','--window',xid,'--clearmodifiers','--delay','1','https://docs.docker.com/engine/install/ubuntu/#install-using-the-apt-repository'],env=env,check=True)
        subprocess.run(['xdotool','key','--window',xid,'Return'],env=env,check=True);time.sleep(6)
        capture_window('s14l03-official-ubuntu-apt-repository',xid,'cmwf8utho004h5c8cz7kzy983','Actual official Docker apt-repository page; no generated web UI')
    finally:
        if p.poll() is None:p.terminate();p.wait(timeout=10)

try:
    # These checks precede every package/service operation. Never execute locally.
    event=json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted' or os.environ.get('RUNNER_OS')!='Linux' or os.environ.get('GITHUB_RUN_ATTEMPT')!='1' or event.get('repository',{}).get('private') is not False:raise RuntimeError('Dedicated standard public hosted-runner scope required')
    if os.environ.get('GITHUB_REPOSITORY')!='emmanuelcorelscreatives/academy-reproducible-python-exercise-20261113-s02l01' or os.environ.get('GITHUB_REF')!='refs/heads/academy-ubuntu-docker-s14-20261113-v1':raise RuntimeError('Exact public course branch changed')
    if os.environ.get('DOCKER_HOST') or os.environ.get('DOCKER_CONTEXT'):raise RuntimeError('Unexpected Docker endpoint override; do not switch endpoints')
    release=dict(line.split('=',1)for line in Path('/etc/os-release').read_text().splitlines()if '=' in line)
    if release.get('ID')!='ubuntu' or release.get('VERSION_ID','').strip('"')!='24.04':raise RuntimeError('Expected actual Ubuntu 24.04 standard VM')
    TEMP=Path(os.environ['RUNNER_TEMP'])/('academy-s14-'+uuid.uuid4().hex);TEMP.mkdir(mode=0o700)
    manifest=json.loads((ROOT/'public-inputs.json').read_text())
    for item in manifest['contextFiles']:
        if sha(ROOT/item['path'])!=item['sha256']:raise RuntimeError('Exact registered public course bytes changed')
    state['inputs']=manifest;state['actualPlatform']={k:v.strip('"')for k,v in release.items()if k in ['ID','VERSION_ID','VERSION_CODENAME','PRETTY_NAME']};state['architecture']=text('actual-architecture',['dpkg','--print-architecture']).strip()
    state['spaceBefore']=text('actual-initial-disk',['df','-B1',str(TEMP)])
    names=['docker-ce','docker-ce-cli','docker-ce-rootless-extras','containerd.io','docker-buildx-plugin','docker-compose-plugin','docker.io','docker-compose','docker-compose-v2','docker-doc','docker-buildx','podman-docker','containerd','runc']
    present=[]
    for package in names:
        r=subprocess.run(['dpkg-query','-W','-f=${db:Status-Abbrev}',package],capture_output=True,text=True)
        if r.returncode==0 and r.stdout.startswith('ii'):present.append(package)
    save('actual-preinstalled-docker-packages.json',{'packages':present,'scope':'pre-existing packages on this disposable hosted VM, NOT fresh installation proof'})
    run('capture-tools-and-docker-prerequisites',['sudo','apt-get','update'],150)
    run('install-public-capture-tools',['sudo','apt-get','install','-y','ca-certificates','curl','xvfb','xterm','xdotool','python3-pil','fonts-dejavu-core'],180)
    if present:
        run('remove-preinstalled-docker-only',['sudo','apt-get','purge','-y',*present],180)
    state['ephemeralRunnerPackageAndDockerChanges']=True
    removed=[]
    for path in Path('/etc/apt/sources.list.d').iterdir():
        if path.is_file() and path.suffix in ['.list','.sources']:
            body=path.read_text()
            if 'download.docker.com/linux/ubuntu' in body:
                removed.append({'name':path.name,'sha256':sha(path)})
                run('remove-preexisting-docker-source-'+str(len(removed)),['sudo','rm','--',str(path)],10)
    save('actual-replaced-docker-source-files.json',{'files':removed,'scope':'only Docker URI source files inside this disposable hosted VM'})
    run('official-apt-prerequisites-refresh',['sudo','apt-get','update'],150)
    run('official-keyring-directory',['sudo','install','-m','0755','-d','/etc/apt/keyrings'],10)
    run('official-docker-signing-key',['sudo','curl','--fail','--silent','--show-error','--location','--max-time','40','https://download.docker.com/linux/ubuntu/gpg','-o','/etc/apt/keyrings/docker.asc'],50)
    run('official-key-readable',['sudo','chmod','a+r','/etc/apt/keyrings/docker.asc'],10)
    arch=state['architecture'];codename=state['actualPlatform']['VERSION_CODENAME']
    source='Types: deb\nURIs: https://download.docker.com/linux/ubuntu\nSuites: '+codename+'\nComponents: stable\nArchitectures: '+arch+'\nSigned-By: /etc/apt/keyrings/docker.asc\n'
    public_source=TEMP/'docker.sources';public_source.write_text(source)
    run('official-docker-source-install',['sudo','install','-m','0644',str(public_source),'/etc/apt/sources.list.d/docker.sources'],10)
    run('official-source-readback',['cat','/etc/apt/sources.list.d/docker.sources'],10)
    run('official-docker-index-refresh',['sudo','apt-get','update'],150)
    run('official-docker-package-install',['sudo','apt-get','install','-y','docker-ce','docker-ce-cli','containerd.io','docker-buildx-plugin','docker-compose-plugin'],240)
    run('actual-installed-package-record',['dpkg-query','-W','-f=${binary:Package} ${Version}\n','docker-ce','docker-ce-cli','containerd.io','docker-buildx-plugin','docker-compose-plugin'],15)
    code,_=run('actual-service-first-status',['sudo','systemctl','status','docker','--no-pager','--lines=7'],15,False)
    if code:
        active=subprocess.run(['sudo','systemctl','is-active','--quiet','docker']).returncode
        if active:
            run('conditional-installed-service-start',['sudo','systemctl','start','docker'],30)
            run('actual-service-after-conditional-start',['sudo','systemctl','status','docker','--no-pager','--lines=7'],15)
    context=text('actual-context-show',['sudo','docker','context','show'],15).strip()
    endpoint=text('actual-context-public-endpoint',['sudo','docker','context','inspect',context,'--format','{{.Endpoints.docker.Host}}'],15).strip()
    if endpoint!='unix:///var/run/docker.sock':raise RuntimeError('Actual selected context is not this intended disposable VM socket; no context switching')
    state['actualContext']={'name':context,'publicEndpoint':endpoint}
    hello='academy-s14-hello-'+uuid.uuid4().hex[:12]
    run('actual-optional-hello-world',['sudo','docker','run','--rm','--name',hello,'hello-world'],90,False)
    fd_r,fd_w=os.pipe();xlog=(OUT/'xvfb.log').open('wb')
    xp=subprocess.Popen(['Xvfb','-displayfd',str(fd_w),'-screen','0','1920x1080x24','-nolisten','tcp'],pass_fds=(fd_w,),stdout=xlog,stderr=subprocess.STDOUT);owned.append(xp);os.close(fd_w)
    if not select.select([fd_r],[],[],8)[0]:raise RuntimeError('Original owned display did not start')
    display=':'+os.read(fd_r,32).decode().strip();os.close(fd_r)
    try:browser_views()
    except Exception as error:state['captureErrors'].append({'operation':'official-browser','error':str(error)})
    terminal('s14l03-actual-platform-and-repository',summary('platform-and-repository',['actual-architecture','official-source-readback','official-docker-index-refresh'],json.dumps(state['actualPlatform'])+'\nPreinstalled Docker packages were inspected and removed only in this disposable VM: '+', '.join(present)),'cmwf8utho004h5c8cz7kzy983','Actual official apt-repository preparation, not retained private extraction')
    terminal('s14l03-actual-install-and-service',summary('install-and-service',['official-docker-package-install','actual-installed-package-record','actual-service-first-status']+(['actual-service-after-conditional-start']if code else [])),'cmwf8utho004h5c8cz7kzy983','Actual fresh package installation and observed service state; no Docker version replay')
    terminal('s14l03-actual-optional-connectivity',summary('optional-connectivity',['actual-optional-hello-world']),'cmwf8utho004h5c8cz7kzy983','Genuine optional hello-world outcome, success or failure preserved')
    terminal('s14l03-actual-selected-context',summary('selected-context',['actual-context-show','actual-context-public-endpoint']),'cmwf8utho004h5c8cz7kzy983','Actual context show and only public intended endpoint; no context switching')
    state['s14l03MissingNineOperationsObserved']=not state['captureErrors'] and len(state['captures'])==6;save('job-state.json',state)
    # Exact frozen registered materials; no team/provider execution or semantic tests.
    context_dir=TEMP/'registered-image-context';shutil.copytree(ROOT/'context',context_dir)
    if shutil.disk_usage(TEMP).free<8*1024**3:raise RuntimeError('Insufficient actual standard-runner disk for bounded image preparation')
    python_image=manifest['pythonImage'];uv_image=manifest['uvImage']
    for tag,value in [('python',python_image),('uv',uv_image)]:
        run('pull-exact-public-'+tag+'-digest',['sudo','docker','pull',value],120)
        text('inspect-exact-public-'+tag+'-image',['sudo','docker','image','inspect',value,'--format','{{json .}}'],20)
    extract_container='academy-s14-uv-extract-'+uuid.uuid4().hex[:12]
    run('create-uv-extraction-only',['sudo','docker','create','--name',extract_container,uv_image],20)
    uv=TEMP/'uv';run('copy-real-uv-binary',['sudo','docker','cp',extract_container+':/uv',str(uv)],30);run('remove-uv-extraction-only',['sudo','docker','rm',extract_container],15);extract_container=None
    run('owned-uv-binary-mode',['sudo','chmod','0755',str(uv)],10)
    cache=context_dir/'offline-cache'
    run('prepare-frozen-public-wheel-cache',[str(uv),'sync','--frozen','--no-dev','--python','/usr/bin/python3.12','--cache-dir',str(cache),'--project',str(context_dir)],420,True,{'UV_PYTHON_DOWNLOADS':'never','UV_NO_PROGRESS':'1','UV_LINK_MODE':'copy','UV_CONCURRENT_DOWNLOADS':'4','UV_CONCURRENT_INSTALLS':'2','UV_CONCURRENT_BUILDS':'2'})
    inventory=[];total=0
    for path in sorted(cache.rglob('*')):
        if path.is_symlink():
            target=path.resolve();target.relative_to(cache.resolve());inventory.append({'path':str(path.relative_to(cache)),'symlink':os.readlink(path)})
        elif path.is_file():
            size=path.stat().st_size;total+=size;inventory.append({'path':str(path.relative_to(cache)),'sha256':sha(path),'bytes':size})
    if total>3*1024**3:raise RuntimeError('Actual public offline cache exceeds bounded 3GiB budget')
    save('actual-public-offline-cache-inventory.json',{'bytes':total,'files':inventory,'source':'ONE frozen-lock public dependency prefetch for this first Docker image build; not lock resolution or semantic QA'})
    shutil.rmtree(context_dir/'.venv')
    for item in manifest['contextFiles']:
        if sha(ROOT/item['path'])!=item['sha256'] or sha(context_dir/Path(item['path']).name)!=item['sha256']:raise RuntimeError('Exact registered source mutated')
    iid=OUT/'actual-prepared-image-id.txt'
    run('actual-exact-course-image-build',['sudo','docker','build','--network=none','--progress=plain','--build-arg','PYTHON_IMAGE='+python_image,'--build-arg','UV_IMAGE='+uv_image,'--iidfile',str(iid),str(context_dir)],600)
    image=iid.read_text().strip()
    if not re.fullmatch('sha256:[0-9a-f]{64}',image):raise RuntimeError('Actual local prepared image identity not returned')
    prepared=json.loads(text('actual-prepared-image-inspect',['sudo','docker','image','inspect',image],20))[0]
    save('actual-prepared-image-public-identity.json',{'Id':prepared['Id'],'RepoDigests':prepared.get('RepoDigests',[]),'imageIdentityKind':'actual local immutable Engine image ID; NOT invented repository@digest','registeredSourceFiles':manifest['contextFiles']})
    inputs=TEMP/'inputs';inputs.mkdir();(inputs/'request.json').write_text(json.dumps({'title':'Academy Docker configuration inspection','product_request':'Inspect the prepared runtime only; no team or provider execution.'})+'\n')
    mailbox=TEMP/'mailbox';mailbox.mkdir();run('owned-mailbox-tmpfs',['sudo','mount','-t','tmpfs','-o','size=16m,mode=0700,nosuid,nodev','tmpfs',str(mailbox)],15)
    host_mailbox=text('actual-host-mailbox-filesystem',['findmnt','--target',str(mailbox),'--noheadings','--output','FSTYPE,SIZE,OPTIONS'],10).strip()
    stat=os.statvfs(mailbox);mailbox_capacity=stat.f_blocks*stat.f_frsize
    if mailbox_capacity>16*1024*1024 or not host_mailbox.startswith('tmpfs'):raise RuntimeError('Actual mailbox is not the required bounded owned tmpfs')
    container='eca-whole-'+uuid.uuid4().hex
    args=['sudo','docker','run','--detach','--rm','--name',container,'--label','eca.whole.owner='+container,'--pull=never','--log-driver=none','--network=none','--read-only','--cap-drop=ALL','--cap-add=SETUID','--cap-add=SETGID','--security-opt=no-new-privileges','--user=0:0','--memory=768m','--memory-swap=768m','--cpus=2','--pids-limit=64','--ulimit=nofile=128:128','--ulimit=fsize=1048576:1048576','--tmpfs','/tmp:rw,nosuid,nodev,size=64m,mode=1777','--tmpfs','/work:rw,nosuid,nodev,size=128m,mode=1777','--mount','type=bind,source='+str(inputs)+',target=/inputs,readonly','--mount','type=bind,source='+str(mailbox)+',target=/mailbox','--workdir=/work','--env=HOME=/tmp','--env=PYTHONDONTWRITEBYTECODE=1',image,'python','-c','import time; time.sleep(240)']
    run('start-one-owned-configuration-inspection-container',args,20)
    actual=json.loads(text('actual-one-owned-container-inspect',['sudo','docker','container','inspect',container],20))[0]
    details={'Name':actual['Name'],'Id':actual['Id'],'Image':actual['Image'],'Running':actual['State']['Running'],'ConfigImage':actual['Config']['Image'],'WorkingDir':actual['Config']['WorkingDir'],'User':actual['Config']['User'],'MailboxHostFilesystem':host_mailbox,'MailboxHostCapacityBytes':mailbox_capacity,'NetworkMode':actual['HostConfig']['NetworkMode'],'ReadonlyRootfs':actual['HostConfig']['ReadonlyRootfs'],'Tmpfs':actual['HostConfig']['Tmpfs'],'Mounts':[{k:v for k,v in m.items()if k in ['Type','Source','Destination','RW']}for m in actual['Mounts']],'Memory':actual['HostConfig']['Memory'],'PidsLimit':actual['HostConfig']['PidsLimit'],'CapDrop':actual['HostConfig']['CapDrop'],'CapAdd':actual['HostConfig']['CapAdd'],'OwnerLabel':actual['Config']['Labels'].get('eca.whole.owner'),'ExecutionScope':'CONFIGURATION-ONLY benign hold command on exact prepared image; production launcher/team/provider workflow NOT executed','ImageIdentityKind':'actual local Engine image ID; no registry RepoDigest invented'}
    if details['Image']!=image or not details['Running'] or details['NetworkMode']!='none' or details['WorkingDir']!='/work' or not details['ReadonlyRootfs']:raise RuntimeError('Actual own container runtime differs')
    bydest={m['Destination']:m for m in details['Mounts']}
    if bydest['/inputs']['RW'] or not bydest['/mailbox']['RW'] or '/work' not in details['Tmpfs']:raise RuntimeError('Actual own mount configuration differs')
    save('actual-owned-container-configuration.json',details)
    path=OUT/'actual-owned-container-readable.txt'
    lines=['ACTUAL configuration-only inspection of this one running owned container.','No production launcher/team/provider workflow executed.','Name: '+details['Name'],'Owner: '+details['OwnerLabel'],'Actual Engine image ID: '+details['Image'],'Container Config.Image: '+details['ConfigImage'],'Registry RepoDigests: '+json.dumps(prepared.get('RepoDigests',[])),'Running: '+str(details['Running'])+' | explicit User: '+details['User'],'WorkingDir: '+details['WorkingDir']+' | NetworkMode: '+details['NetworkMode']+' | ReadonlyRootfs: '+str(details['ReadonlyRootfs'])]
    lines+=['Tmpfs '+k+': '+v for k,v in details['Tmpfs'].items()]
    lines+=['Mount '+json.dumps(m,separators=(',',':')) for m in details['Mounts']]
    lines+=['Mailbox host filesystem: '+details['MailboxHostFilesystem']+' | capacity bytes: '+str(details['MailboxHostCapacityBytes'])]
    lines+=['Memory bytes: '+str(details['Memory'])+' | PIDs: '+str(details['PidsLimit']),'Capabilities dropped: '+json.dumps(details['CapDrop'])+' | added: '+json.dumps(details['CapAdd']),'Source argv/runtime flags preserved; benign sleep replaces team command for inspection.','Local Engine image ID is genuine; no repository@digest has been invented.','Full original inspect JSON retained separately in this run.']
    path.write_text('\n'.join(lines)+'\n')
    terminal('s14l04-actual-owned-container-configuration',path,'cmwf8v4du004l5c8c5bhjdigf','Actual prepared image, read-only input, writable work tmpfs/mailbox, working directory and no-network configuration')
    state['s14l04MissingThreeOperationsObserved']=True;state['allRequestedOperationsCompleted']=state['s14l03MissingNineOperationsObserved']
except Exception as error:
    state['error']=str(error);state['errorAt']=now();state['allRequestedOperationsCompleted']=False
finally:
    cleanup=[]
    try:
        for name in [container,extract_container,hello]:
            if name:
                r=subprocess.run(['sudo','docker','rm','-f',name],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
                confirm=subprocess.run(['sudo','docker','container','inspect',name],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=10)
                absent=confirm.returncode==1 and b'No such' in confirm.stderr
                cleanup.append({'exactOwnedContainer':name,'removeExit':r.returncode,'absenceConfirmed':absent})
                if not absent:state['allRequestedOperationsCompleted']=False
        if mailbox and mailbox.exists():
            r=subprocess.run(['mountpoint','-q',str(mailbox)])
            if r.returncode==0:
                r=subprocess.run(['sudo','umount',str(mailbox)],capture_output=True,timeout=15);cleanup.append({'exactOwnedMailbox':str(mailbox),'unmountExit':r.returncode})
        for p in reversed(owned):
            if p.poll() is None:
                p.terminate()
                try:p.wait(timeout=10)
                except subprocess.TimeoutExpired:p.kill();p.wait(timeout=5)
    except Exception as cleanup_error:
        cleanup.append({'cleanupError':str(cleanup_error),'VMDisposalStillApplies':True});state['allRequestedOperationsCompleted']=False
    state['cleanup']={'ownedProcessesTerminal':all(p.poll()is not None for p in owned),'scopedObjects':cleanup,'remainingVMTeardown':'Standard GitHub-hosted VM disposal; no Studio host package/service/network change'}
    state['finishedAt']=now();state['elapsedSeconds']=round(time.monotonic()-START,3)
    state['independentVisualPASSClaimed']=False
    save('job-state.json',state)
    files=[{'path':str(p.relative_to(OUT)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(OUT.rglob('*'))if p.is_file()and p.name!='output-manifest.json']
    save('output-manifest.json',{'at':now(),'runId':state['runId'],'headSha':state['headSha'],'files':files,'allRequestedOperationsCompleted':state['allRequestedOperationsCompleted'],'independentVisualPASSClaimed':False})
    print(json.dumps({'runId':state['runId'],'allRequestedOperationsCompleted':state['allRequestedOperationsCompleted'],'captures':len(state['captures']),'error':state.get('error'),'noAutomaticRerun':True}))
sys.exit(0 if state['allRequestedOperationsCompleted'] else 1)
