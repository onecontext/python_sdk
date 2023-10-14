import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests


class ServerError(Exception):
    ...


class ConfigurationError(Exception):
    ...


@dataclass
class URLS:
    base_url: str = "https://api.onecontext.ai"

    def _join_base(self, url: str) -> str:
        return urljoin(self.base_url, url)

    def query(self) -> str:
        return self._join_base("query")

    def upload(self) -> str:
        return self._join_base("upload")

    def knowledge_base(self, knowledge_base_name: Optional[str] = None) -> str:
        return self._join_base(f"knowledge_bases/{knowledge_base_name}" if knowledge_base_name else "knowledge_bases")

    def knowledge_base_files(self, knowledge_base_name: Optional[str] = None) -> str:
        return "/".join([self.knowledge_base(knowledge_base_name), "files"])

    def files(self, file_id: Optional[str] = None) -> str:
        return self._join_base(f"files/{file_id}" if file_id else "files")


class ApiClient:
    def __init__(self, api_key: Optional[str] = None) -> None:
        if api_key is None:
            self.api_key = os.environ.get("ONECONTEXT_API_KEY")

        if self.api_key is None:
            msg = "ONECONTEXT_API_KEY not found in environment variables."
            raise ConfigurationError(msg)

        self.session = requests.Session()
        self.session.headers.update(self._auth_headers)

    @property
    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        try:
            response_json = response.json()
        except ValueError:
            response_json = {}

        if response.ok:
            return response_json

        error_msg = response_json.get("errors", [])

        if error_msg:
            msg = f"{response.status_code}: {error_msg.pop()}"
            raise ServerError(msg)
        else:
            response.raise_for_status()

    def get(self, endpoint: str) -> Dict[str, Any]:
        response = self.session.get(endpoint)
        return self._handle_response(response)

    def post(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.session.post(endpoint, **kwargs)
        return self._handle_response(response)

    def delete(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.session.delete(endpoint, **kwargs)
        return self._handle_response(response)
