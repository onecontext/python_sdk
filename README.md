# OneContext

[![PyPI - Version](https://img.shields.io/pypi/v/onecontext.svg)](https://pypi.org/project/onecontext)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/onecontext.svg)](https://pypi.org/project/onecontext)

-----
**Table of Contents**
- [LLM Context as a Service](#llm-context-as-a-service)
- [Quick Start](#quick-start)
- [License](#license)

-----

## LLM Context as a Service

OneContext makes it really easy and fast to augment your LLM application with your own data
in a few API calls. Upload your data to a `Knowledge Base` and directly it
query with natural languge to retrieve relevant context for your LLM application.

We manage the full document processing and retrieval pipeline so that you don't have to:

- document ingestion, chunking and cleaning
- effcient vector embeddings at scale using state of the art open source models
- low latency multi stage query pipeline to provide the most relevant context
for your LLM application

We keep up with the latest research to provide an accurate and fast retrieval pipeline
based on model evalution and best practice heuristics.

### Multi stage query pipeline out of the box:
- Fast base-model retrieves a large pool of documents
- Cross-encoder reranks the retrieved documents to provide the precise
results relevant to the query.

### Use Cases:
- Question Answering over a large knowledge base
- Long term memorry for chatbots
- Runtime context for instruction following agents
- Prevent and detect hallucinations based on custom data


## Quick Start

```console
pip install onecontext
```

### Configuration

    export ONECONTEXT_API_KEY="YOUR_API_KEY"

You can get an api key by joining our closed beta. Email Ross at ross@onecontext.ai to get on the list.

### Usage

#### Create a Knowledge Base:

```python
from onecontext import KnowledgeBase

my_knowledge_base = KnowledgeBase("my_knowledge_base")

my_knowledge_base.create()

```

#### List Knowledge Bases


```python
from onecontext import list_knowledge_bases

print(list_knowledge_bases())

```

#### Upload files to the Knowledge Base:

You can upload an entire directory like this:

```python

my_kb = KnowledgeBase("my_knowledge_base")

directory = "/path/to/local_directory"

my_kb.upload_from_directory(directory)
```

Or, you can upload an individual file like this:

```python

my_kb = KnowledgeBase("my_knowledge_base")

my_kb.upload_file(
    "/path/to/local_file.pdf"
)

```

If you like, you can also add metadata to your files. This makes it really easy to filter your query-space later on. Metadata can be any key-value pairs, passed as a dictionary. For example:

```python

my_kb = KnowledgeBase("my_knowledge_base")

my_kb.upload_file(
    "/path/to/local_file.pdf", metadata={"ContainsPII": True, "author": "ross", "description": "passport", "file-type": "scan", "category": "personal"}
)

```

Currently, you can upload any of [.pdf, .docx, .txt] files. Don't worry if the PDF is a scan (and doesn't have easily extractable text), OneContext will figure it out via OCR.
In the near future you'll be able to upload video, audio, and connect to multiple file-storage platforms.

Once the files have been uploaded they will be processed, chunked
and embedded by OneContext.

Check sync status:

```python
print(my_knowledge_base.is_synced)
```

#### Query the Knowledge Base


```python

from onecontext import Retriever

retriever = Retriever(knowledge_bases=[my_kb])

documents = retriever.query("what is onecontext?", output_k=20)

```

And, filtering by metadata:

```python

from onecontext import Retriever

retriever = Retriever(knowledge_bases=[my_kb])

documents = retriever.query("what is onecontext?", output_k=20, metadata_filters={"ContainsPII": True, "author": "ross"})

```


By default the query pipeline is composed of two steps:

- Retrieval: fetch the larger pool of documents (rerank_pool_size)
- Re-ranking: re-rank the results with a downstream model to get most relevant documents

To improve recall you can increase the rerank_pool_size:

```python

documents = retriever.query("what is onecontext?", output_k=10, rerank_pool_size=80)

```

You can also skip the re-ranking step entirely if you want to prioritise speed over accuracy of results.

```python

documents = retriever.query_no_rerank("what is onecontext?")

```

##### Custom Chunking Pipeline

```python
from onecontext import KnowledgeBase, ChunkParams

my_knowledge_base = KnowledgeBase("my_knowledge_base")

chunk_params = ChunkParams(split_size_words=100)

my_knowledge_base.create(chunk_params=chunk_params)


```

## License

`onecontext` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.

