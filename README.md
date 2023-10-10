# OneContext

[![PyPI - Version](https://img.shields.io/pypi/v/onecontext.svg)](https://pypi.org/project/onecontext)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/onecontext.svg)](https://pypi.org/project/onecontext)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install onecontext
```

## License

`onecontext` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.


## Configuration

    export ONECONTEXT_API_KEY="YOUR_API_KEY"

You can get the api key for free here:

## Usage

### Create a Knowledge Base:

```python
from onecontext import KnowledgeBase

my_knowledge_base = KnowledgeBase("my_knowledge_base")

my_knowledge_base.create()

```

### Upload files to the Knowledge Base:

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

You can check the satus of the sync like so:

```python
my_knowledge_base.is_synced
```

### Query the Knowledge Base

```python

from onecontext import Retriever

retriver = Retriever(knowledge_bases=[my_knowledge_base])

documents = retriver.query("what is onecontext?")

```
