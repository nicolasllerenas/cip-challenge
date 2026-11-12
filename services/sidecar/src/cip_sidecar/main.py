import os
import threading
from pathlib import Path

import uvicorn
from cip_agents.api import create_app as create_agents
from cip_documents.api import create_app as create_documents
from cip_gateway.api import create_app as create_gateway
from cip_library.api import create_app as create_library
from fastapi import FastAPI

HOST = "127.0.0.1"
PORTS = {"gateway": 8000, "library": 8001, "agents": 8002, "documents": 8003}


def configure_environment(environ: dict[str, str]) -> dict[str, str]:
    data_dir = Path(environ.get("CIP_DATA_DIR", Path.home() / ".cip-assistant")).expanduser()
    exports_dir = Path(environ.get("CIP_EXPORTS_DIR", data_dir / "exports")).expanduser()
    defaults = {
        "CIP_LIBRARY_DATA_DIR": str(data_dir / "library"),
        "CIP_GATEWAY_DATA_DIR": str(data_dir / "gateway"),
        "CIP_GATEWAY_EXPORTS_DIR": str(exports_dir),
        "CIP_GATEWAY_LIBRARY_URL": f"http://{HOST}:{PORTS['library']}",
        "CIP_GATEWAY_AGENTS_URL": f"http://{HOST}:{PORTS['agents']}",
        "CIP_GATEWAY_DOCUMENTS_URL": f"http://{HOST}:{PORTS['documents']}",
        "CIP_AGENTS_LIBRARY_URL": f"http://{HOST}:{PORTS['library']}",
    }
    return {**defaults, **environ}


def build_apps() -> dict[str, FastAPI]:
    return {
        "library": create_library(),
        "agents": create_agents(),
        "documents": create_documents(),
        "gateway": create_gateway(),
    }


def server(app: FastAPI, port: int) -> uvicorn.Server:
    return uvicorn.Server(uvicorn.Config(app, host=HOST, port=port, log_level="warning", access_log=False))


def main() -> None:
    os.environ.update(configure_environment(dict(os.environ)))
    apps = build_apps()
    gateway = server(apps.pop("gateway"), PORTS["gateway"])
    for name, app in apps.items():
        threading.Thread(target=server(app, PORTS[name]).run, name=name, daemon=True).start()
    gateway.run()


if __name__ == "__main__":
    main()
