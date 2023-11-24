import os
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests

from onecontext.api import URLS, ApiClient

api = ApiClient()
urls = URLS()

SUPPORTED_FILE_TYPES = (".pdf", ".docx", ".txt", ".md")


@dataclass
class Document:
    id: str
    content: str
    file_name: str
    file_id: str
    page: int
    score: float


@dataclass
class ChunkParams:
    """Chunking Params to customise the chunking algorithm.

    Args:
        split_size_words (int): the number of words to split on
        split_size_overlap (int): the overlap in words between chunks
        split_on_sentence (bool): whether to respect sentences boundaries
        max_chars_hard_stop (int): only applies if split_on_sentence, hard stop in chars if sentence boundary is not found
    """
    split_size_words: Optional[int] = None
    split_size_overlap:  Optional[int] = None
    split_on_sentence: Optional[bool] = None
    max_chars_hard_stop: Optional[int] = None

@dataclass
class ScoreParams:
    model_name: str

@dataclass
class ClusterParams:
    model_name: str

@dataclass
class FileIndexingConfig:
    punctuate: bool

@dataclass
class KnowledgeBase:
    """The KnowledgeBase class provides api access to a given knowledge base.
    knowledge bases names must unique.

    Args:
        name (str): The name of the knowledge bases
        id (str): the id, this will be returned by the api
        sync_status (bool): the current sync status, this will be returned by the api
    """

    name: str
    id: Optional[str] = None
    sync_status: Optional[str] = None
    chunk_params: Optional[ChunkParams] = None
    score_params: Optional[ScoreParams] = None
    cluster_params: Optional[ClusterParams] = None

    def upload_file(self, file_path: Union[str, Path], metadata: Optional[dict] = None, file_indexing_config: Optional[FileIndexingConfig] = None) -> None:
        metadata_json = json.dumps(metadata) if metadata else None

        file_indexing_config_json = json.dumps(asdict(file_indexing_config)) if file_indexing_config else None

        file_path = Path(file_path)
        suffix = file_path.suffix

        if suffix not in SUPPORTED_FILE_TYPES:
            msg = f"{suffix} files are not supported. Supported file types: {SUPPORTED_FILE_TYPES}"
            raise ValueError(msg)

        file_path = file_path.expanduser().resolve()

        with open(file_path, "rb") as file:
            files = {"files": (str(file_path), file)}
            data = {"knowledge_base_name": self.name}
            if metadata_json:
                data.update({"metadata_json": metadata_json})

            if file_indexing_config_json:
                data.update({"file_indexing_config_json": file_indexing_config_json})

            api.post(urls.upload(), data=data, files=files)

    def upload_from_directory(
        self, directory: Union[str, Path], metadata: Optional[Union[dict, List[dict]]] = None
    ) -> None:
        directory = Path(directory).expanduser().resolve()
        if not directory.is_dir():
            msg = "You must provide a direcotry"
            raise ValueError(msg)
        directory = str(directory)
        all_files = [os.path.join(directory, file) for file in os.listdir(directory)]
        files_to_upload = [file for file in all_files if file.endswith(SUPPORTED_FILE_TYPES)]

        if isinstance(metadata, list):
            if len(metadata) != len(files_to_upload):
                raise ValueError("Metadata list len does not match the number of files in directory")
        else:
            metadata = [metadata] * len(files_to_upload)

        for file_path, metadata in zip(files_to_upload, metadata):
            self.upload_file(file_path, metadata)

    def list_files(self) -> List[Dict[str, Any]]:
        return api.get(urls.knowledge_base_files(self.name))

    def get_info(self) -> None:
        info = api.get(urls.knowledge_base(self.name))
        self.sync_status = info["sync_status"]
        self.id = info["id"]

    def create(self) -> None:
        data = asdict(self)
        api.post(urls.knowledge_base(), json=data)

    def delete(self) -> None:
        api.delete(urls.knowledge_base(self.name))

    @property
    def is_synced(self):
        self.get_info()
        return self.sync_status == "SYNCED"


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
        dict: the file information, including download link, file name and sync status
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

    def __post_init__(self):
        for knowledge_base in self.knowledge_bases:
            if not isinstance(knowledge_base, KnowledgeBase):
                raise TypeError(
                    f"knowledge_bases parameter should be a list of KnowledgeBase, recieved {type(knowledge_base)} instead."
                )

    def query(
        self,
        query: str,
        output_k: int = 10,
        *,
        rerank_pool_size: int = 50,
        rerank_fast=True,
        metadata_filters: Optional[Dict] = None,
    ) -> List[Document]:

        """
        The preferred query method. The query pipeline is composed of two stages behind the scenes:
            1. Fast Retrieval of a larger sample set by our base model
            2. Cross-Encoder re ranking to get the most relevant results

        Note that only the final results are returned by the API. To access the
        base retrieval model directly use the query_no_rerank method

        Args:
            query (str):
              the query search string, prefer longer sentences and paragraphs
              for best results
            output_k (int):
              the number of result Documents to return
            rerank_pool_size (int):
              the initial pool of documents to fetch in stage 1. Higher values
              increase recall at the cost of latency
            rerank_fast (bool):
                set to False to access an experimental more powerful cross-encoder
                pipeline. Note that this will increase latency and is often
                not required depending on the use case. We recommend evaluating
                the default pipeline first .
            metadata_filters (dict):
                used to filter the query based on metadata provided at file
                upload.
                eg:
                    {"category" : "legal"}
                will restrict the query to files with a "category" key
                matching "legal" value

                to filter the search to multiple values pass a list instead:
                    {"category" : ["legal", "finance"]

                Note: "file_name" filter is available by default. Be sure
                to provide the full file name including the extension.
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
            "metadata_filters": metadata_filters,
        }
        return self._post_query(params)

    def query_no_rerank(self, query: str, output_k: int = 10) -> List[Document]:
        """
        A simple single stage retrieval query.

        Use this method to fetch a large number of Documents with the lowest latency.
        Accuracy is lower than the default query method with cross-encoder.

        Args:
            query (str):
              the query search string, prefer longer sentences and paragraphs
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

def wait_for_sync(kb, verbose=False):
    import time
    while not kb.is_synced:
        syncing = filter(lambda f : f['has_embedding'] == False, kb.list_files())
        message = [f"Syncing: {file['name']}" for file in syncing]
        if verbose:
            print("\n".join(message), end="\r")
        time.sleep(3)
    if verbose:
        print("\nDone")

