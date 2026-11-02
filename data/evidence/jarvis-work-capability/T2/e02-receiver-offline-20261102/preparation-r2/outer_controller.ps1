# Preparation only. The root must independently release this exact entrypoint.
$ErrorActionPreference = 'Stop'
$clock = [Diagnostics.Stopwatch]::StartNew()
$prep = 'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-receiver-offline-20261102/preparation-r2'
$root = Split-Path -Parent $prep
$controller = Join-Path $root 'controller-r1'
$python = 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe'
$basePython = 'C:/Users/Administrator/AppData/Local/Doubao/User Data/sandbox_runtime/bases/772984f6fd3a8ae0ae7d2422cd7c2bfa/python/python.exe'
$runner = Join-Path $prep 'run_probe.py'
$fixedPowerShell = 'C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/powershell/pwsh.exe'
if ($PSVersionTable.PSEdition -ne 'Core' -or $PSVersionTable.PSVersion.Major -lt 7 -or
    [IO.Path]::GetFullPath([Environment]::ProcessPath) -ine [IO.Path]::GetFullPath($fixedPowerShell)) { throw 'Require fixed pwsh7; no compiler subprocess permitted' }
if ((Test-Path -LiteralPath $controller) -or (Test-Path -LiteralPath (Join-Path $root 'actual-r1'))) { throw 'Existing first-run output: STOP without overwrite/retry' }
foreach ($path in @($root,$prep)) {
    $item = Get-Item -LiteralPath $path
    while ($null -ne $item) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Output ancestor is a reparse point' }
        $item = $item.Parent
    }
}
$manifest = Get-Content -Raw -LiteralPath (Join-Path $prep 'manifest.json') | ConvertFrom-Json
foreach ($property in $manifest.bound_hashes.PSObject.Properties) {
    if ((Get-FileHash -Algorithm SHA256 -LiteralPath $property.Name).Hash -ine $property.Value) { throw ('Pinned hash mismatch: '+$property.Name) }
}
if ($clock.Elapsed.TotalSeconds -ge 30) { throw 'Preflight exceeded fixed entry budget; Python never launched' }
[IO.Directory]::CreateDirectory($controller) | Out-Null
$protected = @((Get-Content -Raw -LiteralPath $manifest.runtime_before | ConvertFrom-Json).protected5 | ForEach-Object { [int]$_.pid })
$native = @'
using System;
using System.IO;
using System.Diagnostics;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;

// Fixed single-batch ownership helper. No process-tree kill or generic runner.
public static class ReceiverOuterR2 {
  [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Entry {
    public uint size,usage,pid; public IntPtr heap; public uint module,threads,parent;
    public int priority; public uint flags;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst=260)] public string exe;
  }
  [DllImport("kernel32",SetLastError=true)] static extern IntPtr OpenProcess(uint access,bool inherit,int pid);
  [DllImport("kernel32")] static extern bool CloseHandle(IntPtr h);
  [DllImport("kernel32")] static extern uint WaitForSingleObject(IntPtr h,uint ms);
  [DllImport("kernel32",SetLastError=true)] static extern bool TerminateProcess(IntPtr h,uint code);
  [DllImport("kernel32",SetLastError=true)] static extern bool GetProcessTimes(IntPtr h,out long created,out long exit,out long kernel,out long user);
  [DllImport("kernel32",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool QueryFullProcessImageName(IntPtr h,uint flags,StringBuilder value,ref int size);
  [DllImport("kernel32",SetLastError=true)] static extern IntPtr CreateToolhelp32Snapshot(uint flags,uint pid);
  [DllImport("kernel32",CharSet=CharSet.Unicode)] static extern bool Process32First(IntPtr h,ref Entry entry);
  [DllImport("kernel32",CharSet=CharSet.Unicode)] static extern bool Process32Next(IntPtr h,ref Entry entry);
  [DllImport("ntdll")] static extern int NtQueryInformationProcess(IntPtr h,int kind,IntPtr data,int length,out int needed);
  [DllImport("shell32",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr CommandLineToArgvW(string command,out int count);
  [DllImport("kernel32")] static extern IntPtr LocalFree(IntPtr value);
  class Owned {
    public int pid,parent; public long created; public string exe,command,role;
    public IntPtr handle; public bool terminated,absent;
  }
  static readonly object Gate=new object();
  static List<Owned> owned=new List<Owned>();
  static List<string> findings=new List<string>();
  static bool timedOut=false;
  static string Norm(string p) { return Path.GetFullPath(p).TrimEnd('\\').ToLowerInvariant(); }
  static List<Entry> Snapshot() {
    IntPtr h=CreateToolhelp32Snapshot(2,0);
    if(h==new IntPtr(-1)) throw new IOException("Process snapshot failed");
    try { var rows=new List<Entry>(); Entry e=new Entry(); e.size=(uint)Marshal.SizeOf<Entry>();
      if(!Process32First(h,ref e)) throw new IOException("Process snapshot first failed");
      do { rows.Add(e); } while(Process32Next(h,ref e)); return rows;
    } finally { CloseHandle(h); }
  }
  static string Command(IntPtr h) {
    int length; NtQueryInformationProcess(h,60,IntPtr.Zero,0,out length);
    if(length<16 || length>131072) throw new IOException("Command length unavailable");
    IntPtr data=Marshal.AllocHGlobal(length);
    try { if(NtQueryInformationProcess(h,60,data,length,out length)!=0) throw new IOException("Command query failed");
      int chars=(ushort)Marshal.ReadInt16(data)/2;
      IntPtr text=Marshal.ReadIntPtr(data,IntPtr.Size==8?8:4);
      long first=data.ToInt64(), begin=text.ToInt64();
      if(begin<first || begin+chars*2>first+length) throw new IOException("Command buffer out of bounds");
      return Marshal.PtrToStringUni(text,chars);
    } finally { Marshal.FreeHGlobal(data); }
  }
  static bool FixedArgs(string command,string python,string baseExe,string script) {
    int count; IntPtr argv=CommandLineToArgvW(command,out count);
    if(argv==IntPtr.Zero) return false;
    try { if(count!=5) return false;
      string[] a=new string[count]; for(int i=0;i<count;i++) a[i]=Marshal.PtrToStringUni(Marshal.ReadIntPtr(argv,i*IntPtr.Size));
      return (Norm(a[0])==Norm(python)||Norm(a[0])==Norm(baseExe)) && a[1]=="-B" && a[2]=="-X" && a[3]=="utf8" && Norm(a[4])==Norm(script);
    } finally { LocalFree(argv); }
  }
  static Owned Capture(int pid,int parent,string role,string exe,string python,string baseExe,string script,int[] protectedPids,long notBefore) {
    if(Array.IndexOf(protectedPids,pid)>=0) throw new IOException("Protected PID cannot be owned");
    // Retained handle includes termination right; never reopen by PID to kill.
    IntPtr h=OpenProcess(0x00101401,false,pid);
    if(h==IntPtr.Zero) throw new IOException("Cannot retain process handle "+pid);
    try {
      long created,exit,kernel,user; if(!GetProcessTimes(h,out created,out exit,out kernel,out user)) throw new IOException("Creation query failed");
      int n=32768; var name=new StringBuilder(n); if(!QueryFullProcessImageName(h,0,name,ref n)) throw new IOException("Image query failed");
      string command=Command(h);
      if(created<notBefore || Norm(name.ToString())!=Norm(exe) || !FixedArgs(command,python,baseExe,script)) throw new IOException("Owned identity/command mismatch "+pid);
      bool linked=false; foreach(var row in Snapshot()) if(row.pid==pid && row.parent==parent) linked=true;
      if(!linked || WaitForSingleObject(h,0)!=258) throw new IOException("Parent linkage/liveness unverified "+pid);
      return new Owned {pid=pid,parent=parent,created=created,exe=name.ToString(),command=command,role=role,handle=h};
    } catch { CloseHandle(h); throw; }
  }
  static object Record(Owned p) { return new {pid=p.pid,parent_pid=p.parent,creation_filetime=p.created,
    executable=p.exe,command=p.command,role=p.role,identity_verified=true,retained_handle=true,terminated=p.terminated,absent=p.absent}; }
  public static string Run(string python,string baseExe,string script,string destination,int[] protectedPids,double elapsed) {
    var clock=Stopwatch.StartNew(); var done=new ManualResetEvent(false);
    var stdout=new FileStream(Path.Combine(destination,"stdout.bin"),FileMode.CreateNew,FileAccess.Write,FileShare.Read);
    var stderr=new FileStream(Path.Combine(destination,"stderr.bin"),FileMode.CreateNew,FileAccess.Write,FileShare.Read);
    Process process=null; Task outCopy=null,errCopy=null; Thread watchdog=null;
    int? exitCode=null; string error=null; bool normal=false,discovery=false;
    long launchAfter=DateTime.UtcNow.ToFileTimeUtc();
    try {
      var info=new ProcessStartInfo(python,"-B -X utf8 \""+script+"\"") {UseShellExecute=false,CreateNoWindow=true,
        RedirectStandardOutput=true,RedirectStandardError=true,WorkingDirectory=Path.GetDirectoryName(script)};
      // Fixed 1790s from outer entry leaves ten seconds for bounded terminal readback.
      watchdog=new Thread(()=> { int remaining=(int)Math.Max(0,1790000-elapsed*1000-clock.ElapsedMilliseconds);
        if(done.WaitOne(remaining)) return;
        lock(Gate) { timedOut=true; foreach(var p in owned) {
          if(WaitForSingleObject(p.handle,0)==258) {
            p.terminated=TerminateProcess(p.handle,124);
            if(!p.terminated) findings.Add("Retained-handle termination failed "+p.pid);
          }
        }}
      }); watchdog.IsBackground=true; watchdog.Start();
      process=Process.Start(info); outCopy=process.StandardOutput.BaseStream.CopyToAsync(stdout); errCopy=process.StandardError.BaseStream.CopyToAsync(stderr);
      Owned redirector=Capture(process.Id,Environment.ProcessId,"venv-redirector",python,python,baseExe,script,protectedPids,launchAfter);
      lock(Gate) { if(timedOut) throw new IOException("Deadline before ownership capture"); owned.Add(redirector); }
      File.AppendAllText(Path.Combine(destination,"identities.jsonl"),JsonSerializer.Serialize(Record(redirector))+"\n");
      // Discover only the normal direct base-Python child, while redirector lives.
      while(clock.Elapsed.TotalSeconds+elapsed<1790) {
        if(WaitForSingleObject(redirector.handle,0)==0) break;
        foreach(var row in Snapshot()) if(row.parent==redirector.pid) {
          bool known=false; lock(Gate) { if(timedOut) break; foreach(var p in owned) if(p.pid==row.pid) known=true; }
          if(!known) {
            if(discovery) throw new IOException("Unexpected second child; no kill authority for it");
            // Native queries never hold the watchdog lock.
            Owned child=Capture((int)row.pid,redirector.pid,"base-python",baseExe,python,baseExe,script,protectedPids,redirector.created);
            if(WaitForSingleObject(redirector.handle,0)!=258) {
              CloseHandle(child.handle); throw new IOException("Redirector ended during child linkage capture; identity uncertain");
            }
            lock(Gate) {
              owned.Add(child); discovery=true;
              if(timedOut && WaitForSingleObject(child.handle,0)==258) {
                findings.Add("Child ownership established after deadline; hard bound unverified");
                child.terminated=TerminateProcess(child.handle,124);
              }
            }
            File.AppendAllText(Path.Combine(destination,"identities.jsonl"),JsonSerializer.Serialize(Record(child))+"\n");
          }
        }
        Thread.Sleep(100);
      }
      normal=process.WaitForExit(0);
      if(normal) exitCode=process.ExitCode;
      if(!discovery) findings.Add("Base child never positively captured; child ownership unverified");
    } catch(Exception e) { error=e.ToString(); findings.Add("Ownership/controller exception; unknown processes never terminated"); }
    finally {
      // If an exception occurred, the watchdog still bounds only verified owned
      // handles. It has no authority over an uncaptured/unknown process.
      bool active=false; lock(Gate) { foreach(var p in owned) if(WaitForSingleObject(p.handle,0)==258) active=true; }
      if(active) { int remaining=(int)Math.Max(0,1792000-elapsed*1000-clock.ElapsedMilliseconds); watchdog.Join(remaining); }
      done.Set(); if(watchdog!=null) watchdog.Join(1000);
      lock(Gate) { foreach(var p in owned) { p.absent=WaitForSingleObject(p.handle,200)==0; if(!p.absent) findings.Add("Owned process remains active "+p.pid); } }
      try { if(outCopy!=null && !outCopy.Wait(500)) findings.Add("stdout copy incomplete"); }
      catch(Exception e) { findings.Add("stdout copy fault "+e.Message); }
      try { if(errCopy!=null && !errCopy.Wait(500)) findings.Add("stderr copy incomplete"); }
      catch(Exception e) { findings.Add("stderr copy fault "+e.Message); }
      stdout.Dispose(); stderr.Dispose();
    }
    var records=new List<object>(); bool absent=true; int terminations=0;
    lock(Gate) { foreach(var p in owned) { records.Add(Record(p)); absent &= p.absent; if(p.terminated) terminations++; CloseHandle(p.handle); } }
    bool clean=normal && exitCode==0 && !timedOut && discovery && absent && findings.Count==0 && error==null;
    return JsonSerializer.Serialize(new {status=clean?"CONTROLLER_CLEAN":"INCOMPLETE",controller_pid=Environment.ProcessId,exit_code=exitCode,timeout=timedOut,
      entry_elapsed_seconds=elapsed+clock.Elapsed.TotalSeconds,owned=records,owned_absent=absent,
      termination_count=terminations,normal_exit=normal,findings=findings,error=error,
      hard_bound_scope="verified retained redirector/base handles only; unknown/unverified child prevents acceptance",
      E02="NOT_PASSED",T2="NOT_PASSED",model_calls=0,product_edits=0},new JsonSerializerOptions {WriteIndented=true});
  }
}
'@
# PowerShell7 Add-Type uses its in-process Roslyn compiler; fixed runtime is pinned.
try {
    Add-Type -TypeDefinition $native -Language CSharp
    if ($clock.Elapsed.TotalSeconds -ge 30) { throw 'Compilation/preflight budget exhausted; Python never launched' }
    $terminal = [ReceiverOuterR2]::Run($python,$basePython,$runner,$controller,$protected,$clock.Elapsed.TotalSeconds)
} catch {
    $terminal = @{ status='INCOMPLETE'; error=$_.Exception.ToString(); entry_elapsed_seconds=$clock.Elapsed.TotalSeconds; acceptance=$false } | ConvertTo-Json -Depth 5
}
[IO.File]::WriteAllText((Join-Path $controller 'terminal.json'),$terminal,[Text.UTF8Encoding]::new($false))
$record = $terminal | ConvertFrom-Json
if ($record.status -ne 'CONTROLLER_CLEAN') { exit 1 }
$probe = Join-Path $root 'actual-r1/result.json'
if (-not (Test-Path -LiteralPath $probe) -or (Get-Content -Raw -LiteralPath $probe | ConvertFrom-Json).status -ne 'PASS') { exit 1 }
exit 0
