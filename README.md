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

OneContext makes it easy to augment your LLM application with your own data
in a few API calls. Simply upload your data to a Knowledge Base and directly
query with natrual languge to retrieve relevant context for your LLM application.

We manage the full document processing and retrieval pipeline so that you don't have to:

- document ingestion, chunking and cleaning
- effcient vector embeddings at scale using state of the art open source models
- low latency multi stage query pipeline to provide the most relevant context
for your LLM application

We keep up with the latest research to provide an accurate and fast retrieval pipeline
based on model evalution and best practice heuristics.

### Multi stage query pipeline out of the box:
- fast base model retrives a large pool of documents
- cross-encoder reranks the retrived documents to provide the prceise
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

You can get the api key for free at  [OneContext](www.onecontext.ai)

### Usage

#### Create a Knowledge Base:

```python
from onecontext import KnowledgeBase

my_knowledge_base = KnowledgeBase("my_knowledge_base")

my_knowledge_base.create()

```

#### Upload files to the Knowledge Base:

```python

import os
from pathlib import Path

my_knowledge_base = KnowledgeBase("my_knowledge_base")

folder = "/path/to/local_folder"

file_types = (".pdf", ".docx", ".txt", ".md")

files = []

# Get all file paths in the specified directory
all_files = [os.path.join(folder, file) for file in os.listdir(folder)]

# Filter the files based on the supported extension
files_to_upload = [file for file in all_files if file.endswith(file_types)]

for file_path in files_to_upload:
    my_knowledge_base.upload_file(file_path)
```

Once the files have been uploaded they will be processed, chunked
and embedded by OneContext.

Check sync status:

```python
print(my_knowledge_base.is_synced)
```

#### Query the Knowledge Base

```python

from onecontext import Retriever

retriver = Retriever(knowledge_bases=[my_knowledge_base])

documents = retriver.query("what is onecontext?")

```


## License

`onecontext` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


