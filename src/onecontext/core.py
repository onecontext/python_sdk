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
        self.get_info()
        return self.sync_status == 'SYNCED'


def list_knowledge_bases() -> List[KnowledgeBase]:
    """List the available Knowledge Bases"""
    knowledge_base_dicts = api.get(urls.knowledge_base())
    return [KnowledgeBase(**kb) for kb in knowledge_base_dicts]


def get_file_metadata(file_id: str) -> Dict[str, Any]:
    """
    Fetch the file meta data

    Args:
        file_id (str): the id of the file (returned with every Document result)

    Returns:
        dict: the file information, including dowload link, file name and sync status
    """
    return api.get(urls.files(file_id))


def download_file(file_id: str, download_dir: Path) -> None:
    """
    Download a file

    Args:
        file_id (str): the id of the file (returned with every Document result)
        download_dir (str): the directory to which the file will be downloaded

    """
    file_metadata = get_file_metadata(file_id)
    download_url = file_metadata["download_url"]
    file_path = download_dir / file_metadata["name"]
    response = requests.get(download_url, timeout=10)
    with open(file_path, mode="wb") as file:
        file.write(response.content)


@dataclass
class Retriever:
    """
    The query interface to one or more knowledge_bases

    Args:
        knowledge_bases (list[KnowledgeBase]): A list of knowledge bases to query.

    """
    knowledge_bases: List[KnowledgeBase]

    def query(self, query: str, output_k: int = 10, *, rerank_pool_size: int = 50, rerank_fast=True) -> List[Document]:
        """

        The preffered query method. The query pipline is composed of two stages behind the scenes:
            1. Fast Retrieval of a larger sample set by our base model
            2. Cross-Encoder reranking to get the most relevant results

        Note that only the final results are returned by the API. To access the
        base retrieval model directly use teh query_no_rerank method

        Args:
            query (str):
              the query search string, prefer longer senteces and paragraphs
              for best results
            output_k (int):
              the number of result Documents to return
            rerank_pool_size (int):
              the initial pool of documents to fetch in stage 1. Higher values
              increase recall at the cost of latency
            rerank_fast (bool):
                set to False to access an experimental more powerful cross-encoder
                pipeline. Note that this will increase latency and is often
                not required dependig on the use case. We recommend evaluating
                the default pipeline first .

        Returns:
            list[Document] : the most relevant document chunks
        """
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
        """
        A simple single stage retrieval query.

        Use this method to fetch a large number of Documents with the lowest latecy.
        Accuracy is lower thant the defaul query method with cross-encoder.

        Args:
            query (str):
              the query search string, prefer longer senteces and paragraphs
              for best results
            output_k (int):
              the number of result Documents to return
        Returns:
            list[Document] : the most relevant document chunks

        """
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
