from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import requests
from onecontext.api import URLS, ApiClient

api = ApiClient()
urls = URLS()

@dataclass
class Document:
    id: str
    content: str
    file_name: str
    file_id: str
    page: int
    score: float


@dataclass
class KnowledgeBase:
    """The KnowledgeBase class provides api access to a given knowledge base.
    knowledge bases names must unique.

    Args:
        name (str): The name of the knowledge bases
    """

    name: str
    id: Optional[str] = None
    sync_status: Optional[str] = None

    def upload_file(self, file_path: Union[str, Path]) -> None:
        with open(Path(file_path).expanduser().resolve(), "rb") as file:
            files = {"files": (str(file_path), file)}
            data = {"knowledge_base_name": self.name}
            api.post(urls.upload(), data=data, files=files)

    def list_files(self) -> List[Dict[str, Any]]:
        return api.get(urls.knowledge_base_files(self.name))

    def get_info(self) -> None:
        info = api.get(urls.knowledge_base(self.name))
        self.sync_status = info["sync_status"]
        self.id = info["id"]

    def create(self) -> None:
        api.post(urls.knowledge_base(self.name))

    def delete(self) -> None:
        api.delete(urls.knowledge_base(self.name))

    @property
    def is_synced(self):
        if self.sync_status is None:
            self.get_info()
        return self.sync_status == 'SYNCED'


def list_knowledge_bases() -> List[KnowledgeBase]:
    knowledge_base_dicts = api.get(urls.knowledge_base())
    return [KnowledgeBase(**kb) for kb in knowledge_base_dicts]


def get_file_metadata(file_id: str) -> Dict[str, Any]:
    return api.get(urls.files(file_id))


def download_file(file_id: str, download_dir: Path) -> None:
    file_metadata = get_file_metadata(file_id)
    download_url = file_metadata["download_url"]
    file_path = download_dir / file_metadata["name"]
    response = requests.get(download_url, timeout=10)
    with open(file_path, mode="wb") as file:
        file.write(response.content)


@dataclass
class Retriever:
    knowledge_bases: List[KnowledgeBase]

    def query(self, query: str, output_k: int = 10, *, rerank_pool_size: int = 50, rerank_fast=True) -> List[Document]:
        params = {
            "query": query,
            "output_k": output_k,
            "knowledge_base_names": [kb.name for kb in self.knowledge_bases],
            "rerank_pool_size": rerank_pool_size,
            "rerank_fast": rerank_fast,
            "rerank": True,
        }

        return self._post_query(params)

    def query_no_rerank(self, query: str, output_k: int = 10) -> List[Document]:
        params = {
            "query": query,
            "output_k": output_k,
            "knowledge_base_names": [kb.name for kb in self.knowledge_bases],
            "rerank": False,
        }
        return self._post_query(params)

    def _post_query(self, params: Dict[str, Any]) -> List[Document]:
        results = api.post(urls.query(), json=params)
        return [Document(**document) for document in results["documents"]]
