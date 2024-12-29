# Keep It Simple

My technical blog for sharing ideas, documentations and proTipes. MkDocs Material framework is used for creating this repo.


### Setup Instruction.

Refer to [MkDocs Material](https://squidfunk.github.io/mkdocs-material/getting-started/) website to get started with the setps or follow the guide below. 

- Create python virtual environment
```sh
python -m venv .keep-it-simple
source .keep-it-simple/bin/activate
```

- install mkdocs-material using pip
```sh
pip install mkdocs-material
pip install --upgrade pip
```

- After the installation, create site using following command. It will create `docs/` folder and `mkdocs.yaml` file in your github repo. 

```sh
mkdocs new .
```

- You can now follow the guides given on mkdocs material documentation to customize it according to your preference or copy my format in `mkdocs.yaml`. 
- finally bundle and preview your website using `mkdocs serve` command.


<!--
    Reference to Similar Blogs.

    - https://github.com/Andre601/blog
    - https://github.com/4kelly/material-mkdocs-blog
    - https://github.com/timvink/personal-site
    - https://github.com/james-willett/jameswillett.dev/tree/main

 -->