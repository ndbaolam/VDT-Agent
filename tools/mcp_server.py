import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import platform
import psutil
import shlex
import subprocess
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from typing import Dict, List, Union, Optional, Any

os.environ['DANGEROUSLY_OMIT_AUTH'] = 'true'

mcp = FastMCP()

@mcp.tool()
def get_system_metrics(
    metrics_type: str = "all"
) -> Union[Dict, List[Dict]]:
    """
    Collect system metrics.
    
    Args:
        metrics_type: one of "system", "cpu", "ram", "disk", "all"
    
    Returns:
        Dict or List[Dict] depending on metrics_type
    """
    try:
        # System info
        system_info = {
            "system": platform.system(),
            "node_name": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }

        # CPU info
        cpu_info = {
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "cpu_count_physical": psutil.cpu_count(logical=False),
            "cpu_percent": psutil.cpu_percent(interval=1)
        }

        # RAM info
        virtual_mem = psutil.virtual_memory()
        ram_info = {
            "total": virtual_mem.total,
            "available": virtual_mem.available,
            "used": virtual_mem.used,
            "percent": virtual_mem.percent
        }

        # Disk info
        disk_info: List[Dict[str, Union[str, int, float]]] = []
        for partition in psutil.disk_partitions():
            usage = psutil.disk_usage(partition.mountpoint)
            disk_info.append({
                "device": partition.device,
                "mountpoint": partition.mountpoint,
                "fstype": partition.fstype,
                "total": usage.total,
                "used": usage.used,
                "free": usage.free,
                "percent": usage.percent
            })

        # Return based on metrics_type
        metrics_type = metrics_type.lower()
        if metrics_type == "system":
            return system_info
        elif metrics_type == "cpu":
            return cpu_info
        elif metrics_type == "ram":
            return ram_info
        elif metrics_type == "disk":
            return disk_info
        elif metrics_type == "all":
            return {
                "system_info": system_info,
                "cpu_info": cpu_info,
                "ram_info": ram_info,
                "disk_info": disk_info
            }
        else:
            return {"error": f"Unknown metrics_type: {metrics_type}"}

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_process_metrics(pid: Optional[int] = None) -> Dict[str, Any]:
    """
    Collect metrics of running processes including PID, name, user, status, CPU and memory usage.

    Args:
        pid (Optional[int]): If provided, return metrics only for the process with this PID.
                             If None, return top 10 processes sorted by memory_percent.

    Returns:
        dict: {
            "processes": List of process info dicts,
            "error": Optional error message if something goes wrong
        }
    """
    try:
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info

                # Filter out processes with no CPU and memory usage
                if pinfo['cpu_percent'] == 0 and pinfo['memory_percent'] == 0:
                    continue

                # If pid is provided, only collect that process
                if pid is not None and pinfo['pid'] != pid:
                    continue

                processes.append({
                    "pid": pinfo['pid'],
                    "name": pinfo['name'],
                    "user": pinfo['username'],
                    "status": pinfo['status'],
                    "cpu_percent": pinfo['cpu_percent'],
                    "memory_percent": pinfo['memory_percent']
                })

                # If we found the specific pid, break early
                if pid is not None:
                    break

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # If pid is not specified, sort by memory usage and take top 10
        if pid is None:
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
            processes = processes[:10]

        return {"processes": processes}

    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def execute_command(command: str, cwd: Optional[str] = None, timeoutSec: int = 30):
    """
    Execute a system command safely (without shell).

    Args:
        command (str): The system command to run, e.g. 'ls -la'.
        cwd (Optional[str]): The working directory. Defaults to current directory.
        timeoutSec (int): Maximum time allowed to run the command (seconds).

    Returns:
        List[TextContent]: Text output including stdout, stderr, returncode, or error.
    """
    try:
        # Split command safely
        args = shlex.split(command)
        if not args:
            return [TextContent(type="text", text="[exec] Error: empty command")]

        # Validate cwd
        if cwd is not None and not os.path.isdir(cwd):
            return [TextContent(type="text", text=f"[exec] Error: cwd does not exist: {cwd}")]

        # Run the command
        result = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeoutSec,
        )

        # Prepare output
        report = []
        report.append(f"$ {command}")
        if cwd:
            report.append(f"[cwd] {cwd}")
        report.append(f"[returncode] {result.returncode}")

        report.append("\n[stdout]")
        report.append(result.stdout.strip() or "(empty)")

        report.append("\n[stderr]")
        report.append(result.stderr.strip() or "(empty)")

        return [TextContent(type="text", text="\n".join(report))]

    except subprocess.TimeoutExpired:
        return [TextContent(type="text", text=f"[exec] Error: command timed out after {timeoutSec}s")]
    except Exception as e:
        return [TextContent(type="text", text=f"[exec] Error: {e}")]

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
