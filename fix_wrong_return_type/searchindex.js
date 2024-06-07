Search.setIndex({"docnames": ["developer/explanations/decisions", "developer/explanations/decisions/0001-record-architecture-decisions", "developer/how-to/build-docs", "developer/how-to/contribute", "developer/how-to/lint", "developer/how-to/make-release", "developer/how-to/move-code", "developer/how-to/run-tests", "developer/how-to/static-analysis", "developer/how-to/update-tools", "developer/index", "developer/reference/standards", "developer/tutorials/dev-install", "genindex", "index", "user/explanations/docs-structure", "user/how-to/run-container", "user/index", "user/reference/api", "user/tutorials/get_started", "user/tutorials/installation"], "filenames": ["developer/explanations/decisions.rst", "developer/explanations/decisions/0001-record-architecture-decisions.rst", "developer/how-to/build-docs.rst", "developer/how-to/contribute.rst", "developer/how-to/lint.rst", "developer/how-to/make-release.rst", "developer/how-to/move-code.rst", "developer/how-to/run-tests.rst", "developer/how-to/static-analysis.rst", "developer/how-to/update-tools.rst", "developer/index.rst", "developer/reference/standards.rst", "developer/tutorials/dev-install.rst", "genindex.rst", "index.rst", "user/explanations/docs-structure.rst", "user/how-to/run-container.rst", "user/index.rst", "user/reference/api.rst", "user/tutorials/get_started.rst", "user/tutorials/installation.rst"], "titles": ["Architectural Decision Records", "1. Record architecture decisions", "Build the docs using sphinx", "Contributing to the project", "Run linting using pre-commit", "Make a release", "Moving code from another repo", "Run the tests using pytest", "Run static analysis using mypy", "Update the tools", "Developer Guide", "Standards", "Developer install", "API Index", "dodal", "About the documentation", "Run in a container", "User Guide", "API", "Getting Started", "Installation"], "terms": {"we": [0, 1, 3, 6], "major": 0, "adr": [0, 1], "describ": [0, 1], "michael": [0, 1], "nygard": [0, 1], "below": 0, "i": [0, 3, 4, 6, 7, 8, 9, 10, 11, 15, 17, 18, 19, 20], "list": 0, "our": 0, "current": [0, 9, 20], "1": [0, 11], "date": 1, "2022": 1, "02": 1, "18": 1, "accept": 1, "need": [1, 15, 20], "made": 1, "thi": [1, 2, 4, 5, 6, 9, 11, 12, 15, 18, 19, 20], "project": [1, 2, 7, 9, 10], "us": [1, 6, 10, 11, 12, 14, 16, 20], "see": [1, 2, 5], "": [1, 6, 19], "articl": 1, "link": [1, 10, 17], "abov": [1, 4], "To": [1, 5, 9, 12, 16, 19], "creat": [1, 5, 6], "new": [1, 3, 5, 12, 17], "copi": [1, 6], "past": 1, "from": [1, 2, 10, 11, 16, 17, 19, 20], "exist": [1, 3, 20], "ones": 1, "you": [2, 3, 4, 5, 6, 7, 8, 12, 19, 20], "can": [2, 3, 4, 6, 7, 8, 12, 19, 20], "base": 2, "directori": [2, 6, 11, 19], "run": [2, 3, 9, 10, 11, 12, 17], "tox": [2, 4, 7, 8, 12], "e": [2, 4, 6, 7, 8, 12], "static": [2, 10, 11, 12], "which": [2, 9, 12], "includ": [2, 17], "api": [2, 11, 17], "pull": [2, 3, 6, 9, 16], "docstr": [2, 11], "code": [2, 4, 10, 14, 19], "document": [2, 3, 10, 17], "standard": [2, 3, 10], "The": [2, 3, 4, 11, 14, 15, 20], "built": [2, 16], "html": 2, "open": [2, 3, 12], "local": [2, 6, 12, 19], "web": 2, "brows": 2, "firefox": 2, "index": [2, 17], "also": [2, 3, 7, 10, 17, 19, 20], "an": [2, 4, 6, 9], "process": [2, 6, 11], "watch": 2, "your": [2, 3, 19], "chang": [2, 3, 4, 6, 9, 14], "rebuild": 2, "whenev": 2, "reload": 2, "ani": [2, 3, 4, 6, 9, 19, 20], "browser": 2, "page": [2, 5, 11], "view": 2, "localhost": 2, "http": [2, 5, 6, 9, 14, 20], "8000": 2, "If": [2, 3, 4, 6, 19, 20], "ar": [2, 3, 6, 11, 15, 16, 19], "make": [2, 3, 6, 10], "sourc": [2, 6, 8, 12, 14, 20], "too": 2, "tell": [2, 4], "src": [2, 6], "most": [3, 15], "welcom": 3, "all": [3, 4, 6], "request": [3, 9], "handl": [3, 4], "through": [3, 12], "github": [3, 5, 6, 9, 12, 14, 16, 20], "pleas": [3, 5, 11, 19], "check": [3, 4, 6, 7, 8, 9, 11, 12], "befor": 3, "file": [3, 4, 6, 8, 19], "one": [3, 15], "have": [3, 4, 6, 12, 19], "great": 3, "idea": [3, 6], "involv": 3, "big": 3, "ticket": 3, "want": [3, 6], "sure": 3, "don": 3, "t": [3, 15], "spend": 3, "time": [3, 4], "someth": [3, 9], "might": 3, "fit": [3, 6], "scope": 3, "offer": 3, "place": 3, "ask": 3, "question": 3, "share": 3, "end": 3, "obviou": 3, "when": [3, 12, 19], "close": [3, 9], "rais": 3, "instead": [3, 16, 19], "while": 3, "100": 3, "doe": 3, "librari": [3, 17], "bug": 3, "free": 3, "significantli": 3, "reduc": 3, "number": [3, 5, 16, 18], "easili": 3, "caught": 3, "remain": 3, "same": [3, 5], "improv": [3, 15], "contain": [3, 11, 12, 14, 17, 19], "inform": [3, 15], "set": [3, 4, 11, 19], "up": [3, 6, 10, 19], "environ": [3, 12], "test": [3, 6, 10], "what": [3, 19], "should": [3, 20], "follow": [3, 5, 6, 11, 12, 19], "black": [4, 11], "flake8": [4, 11], "isort": [4, 11], "under": [4, 12], "command": 4, "Or": 4, "instal": [4, 6, 10, 14, 16, 17], "hook": 4, "each": 4, "do": [4, 6, 8, 19], "git": [4, 6, 9, 12, 20], "just": 4, "report": [4, 7], "reformat": 4, "repositori": [4, 6, 11], "likewis": 4, "get": [4, 5, 10, 12, 16, 17], "those": 4, "manual": 4, "json": 4, "formatt": 4, "well": 4, "save": [4, 19], "highlight": [4, 8], "editor": 4, "window": 4, "checklist": 5, "choos": [5, 12], "pep440": 5, "compliant": 5, "pep": 5, "python": [5, 6, 9, 12], "org": 5, "0440": 5, "go": [5, 19], "draft": 5, "click": [5, 12], "tag": 5, "suppli": 5, "chose": 5, "gener": [5, 6, 9], "note": [5, 6, 17], "review": 5, "edit": 5, "titl": [5, 11], "publish": 5, "push": [5, 6, 19], "main": [5, 6, 16], "branch": [5, 6], "ha": [5, 9, 20], "effect": 5, "except": 5, "option": 5, "In": 6, "write": [6, 15], "other": [6, 14, 19], "dl": [6, 14, 19, 20], "mai": 6, "come": 6, "realis": 6, "more": [6, 9, 15, 17, 19], "sens": 6, "dodal": [6, 12, 16, 20], "It": [6, 7, 8, 20], "good": [6, 15], "keep": [6, 9], "histori": 6, "devic": [6, 14], "diamondlightsourc": [6, 9, 12, 14, 16, 20], "artemi": 6, "exampl": [6, 11], "clone": 6, "codebas": 6, "com": [6, 9, 12, 20], "clone_for_histori": 6, "cd": [6, 12], "remov": 6, "remot": 6, "avoid": 6, "mistaken": 6, "rm": 6, "origin": 6, "filter": 6, "out": 6, "onli": [6, 19], "pip": [6, 9, 12, 14, 20], "path": [6, 20], "f": 6, "clean": 6, "everyth": 6, "reset": 6, "hard": 6, "gc": 6, "aggress": 6, "prune": 6, "fd": 6, "add": 6, "everi": 6, "commit": [6, 10, 11, 12], "messag": [6, 19], "mention": 6, "been": [6, 20], "msg": 6, "sed": 6, "came": 6, "issu": [6, 8], "refer": [6, 15, 18], "old": 6, "modifi": 6, "point": 6, "explicit": 6, "assum": 6, "123": 6, "notat": 6, "ever": 6, "own": 6, "0": 6, "9": 6, "g": 6, "prepar": 6, "correct": 6, "structur": [6, 9], "mkdir": 6, "p": [6, 12], "mv": 6, "At": 6, "log": 6, "ensur": 6, "look": [6, 7], "mostli": 6, "m": [6, 12, 20], "import": [6, 11, 19], "differ": [6, 15], "folder": 6, "now": [6, 12, 19, 20], "safe": 6, "checkout": 6, "b": 6, "add_code_from_artemi": 6, "old_repo": 6, "rebas": [6, 9], "allow": 6, "unrel": 6, "where": [6, 8, 9], "re": 6, "tidi": 6, "so": [6, 12, 19, 20], "case": 6, "had": 6, "some": [6, 19], "depend": [6, 16, 20], "done": [7, 8], "find": 7, "function": [7, 11, 15, 19], "like": [7, 19], "them": [7, 8, 19], "error": 7, "coverag": 7, "commandlin": [7, 20], "cov": 7, "xml": 7, "type": [8, 11, 12, 20], "definit": 8, "without": 8, "potenti": 8, "match": 8, "modul": 9, "merg": 9, "python3": [9, 12, 20], "skeleton": 9, "provid": [9, 19], "mean": 9, "techniqu": 9, "sync": 9, "between": 9, "multipl": 9, "latest": 9, "version": [9, 16, 18], "fals": 9, "conflict": 9, "indic": 9, "area": 9, "setup": [9, 12], "detail": 9, "split": [10, 14, 17], "four": [10, 15, 17], "categori": [10, 17], "access": [10, 17, 19], "side": [10, 17], "bar": [10, 17], "contribut": [10, 14], "move": 10, "anoth": 10, "repo": 10, "build": [10, 11], "doc": [10, 11, 12], "sphinx": [10, 11, 12], "pytest": [10, 12], "analysi": [10, 11, 12], "mypi": [10, 11, 12], "lint": [10, 11, 12], "pre": [10, 11, 12, 16], "updat": 10, "tool": [10, 11], "releas": [10, 14, 16, 17, 20], "practic": [10, 17], "step": [10, 12, 17], "dai": 10, "dev": [10, 12], "task": 10, "architectur": 10, "decis": 10, "record": 10, "why": [10, 17], "technic": [10, 15, 17], "materi": [10, 17], "defin": 11, "conform": 11, "format": 11, "style": 11, "order": [11, 15], "how": [11, 15], "guid": [11, 14, 15], "napoleon": 11, "extens": 11, "As": 11, "googl": 11, "consid": 11, "hint": 11, "signatur": 11, "For": 11, "def": 11, "func": 11, "arg1": 11, "str": [11, 18], "arg2": 11, "int": 11, "bool": 11, "summari": 11, "line": 11, "extend": 11, "descript": 11, "arg": 11, "return": 11, "valu": 11, "true": 11, "extract": 11, "underlin": 11, "convent": 11, "headl": 11, "head": 11, "2": [11, 14], "3": [11, 12, 20], "These": 12, "instruct": 12, "take": 12, "minim": 12, "requir": [12, 15, 20], "first": 12, "either": 12, "host": 12, "machin": 12, "venv": [12, 20], "8": [12, 20], "later": [12, 20], "vscode": 12, "virtualenv": 12, "bin": [12, 20], "activ": [12, 20], "devcontain": 12, "reopen": 12, "prompt": 12, "termin": [12, 20], "graph": 12, "packag": 12, "tree": 12, "pipdeptre": 12, "parallel": 12, "ophyd": [14, 19], "util": 14, "could": 14, "across": [14, 19], "beamlin": [14, 19], "pypi": 14, "io": [14, 16], "section": 14, "user": 14, "develop": 14, "back": 14, "grand": 15, "unifi": 15, "theori": 15, "david": 15, "la": 15, "There": 15, "secret": 15, "understood": 15, "softwar": [15, 20], "isn": 15, "thing": 15, "call": 15, "thei": 15, "tutori": 15, "explan": 15, "repres": 15, "purpos": 15, "approach": 15, "creation": 15, "understand": 15, "implic": 15, "help": [15, 19], "often": 15, "immens": 15, "topic": 15, "its": [16, 20], "alreadi": 16, "avail": 16, "registri": 16, "docker": 16, "ghcr": 16, "start": 17, "typic": 17, "usag": 17, "here": 17, "experienc": 17, "about": 17, "work": [17, 19], "wai": 17, "intern": 18, "__version__": 18, "calcul": 18, "pypa": 18, "setuptools_scm": 18, "blueski": 19, "plan": 19, "commonli": 19, "mani": 19, "think": 19, "would": 19, "cover": 19, "anyth": 19, "hardwar": 19, "i03": 19, "dcm": 19, "workstat": 19, "give": 19, "immedi": 19, "real": 19, "default": 19, "connect": 19, "simul": 19, "instrument": 19, "helper": 19, "set_up_logging_handl": 19, "logger": 19, "occur": 19, "increas": 19, "amount": 19, "debug": 19, "explicitli": 19, "info": 19, "am": 19, "dls_sw": 19, "graylog": 19, "next": 19, "instanc": 19, "exlus": 19, "recommend": 20, "interfer": 20, "featur": 20, "interfac": 20}, "objects": {"": [[18, 0, 0, "-", "dodal"]], "dodal.dodal": [[18, 1, 1, "", "__version__"]]}, "objtypes": {"0": "py:module", "1": "py:data"}, "objnames": {"0": ["py", "module", "Python module"], "1": ["py", "data", "Python data"]}, "titleterms": {"architectur": [0, 1], "decis": [0, 1], "record": [0, 1], "1": 1, "statu": 1, "context": 1, "consequ": 1, "build": [2, 12], "doc": 2, "us": [2, 4, 7, 8, 19], "sphinx": 2, "autobuild": 2, "contribut": 3, "project": 3, "issu": [3, 4], "discuss": 3, "code": [3, 6, 11], "coverag": 3, "develop": [3, 10, 12], "guid": [3, 10, 17], "run": [4, 7, 8, 16], "lint": 4, "pre": 4, "commit": 4, "fix": 4, "vscode": 4, "support": 4, "make": 5, "releas": 5, "move": 6, "from": 6, "anoth": 6, "repo": 6, "test": [7, 12], "pytest": 7, "static": 8, "analysi": 8, "mypi": 8, "updat": 9, "tool": 9, "tutori": [10, 17], "how": [10, 14, 17], "explan": [10, 17], "refer": [10, 17], "standard": 11, "document": [11, 14, 15], "instal": [12, 20], "clone": 12, "repositori": 12, "depend": 12, "see": 12, "what": 12, "wa": 12, "api": [13, 18], "index": 13, "dodal": [14, 18, 19], "i": 14, "structur": 14, "about": 15, "contain": 16, "start": [16, 19], "user": 17, "get": 19, "The": 19, "purpos": 19, "devic": 19, "ad": 19, "log": 19, "check": 20, "your": 20, "version": 20, "python": 20, "creat": 20, "virtual": 20, "environ": 20, "librari": 20}, "envversion": {"sphinx.domains.c": 3, "sphinx.domains.changeset": 1, "sphinx.domains.citation": 1, "sphinx.domains.cpp": 9, "sphinx.domains.index": 1, "sphinx.domains.javascript": 3, "sphinx.domains.math": 2, "sphinx.domains.python": 4, "sphinx.domains.rst": 2, "sphinx.domains.std": 2, "sphinx.ext.intersphinx": 1, "sphinx.ext.viewcode": 1, "sphinx": 58}, "alltitles": {"Architectural Decision Records": [[0, "architectural-decision-records"]], "1. Record architecture decisions": [[1, "record-architecture-decisions"]], "Status": [[1, "status"]], "Context": [[1, "context"]], "Decision": [[1, "decision"]], "Consequences": [[1, "consequences"]], "Build the docs using sphinx": [[2, "build-the-docs-using-sphinx"]], "Autobuild": [[2, "autobuild"]], "Contributing to the project": [[3, "contributing-to-the-project"]], "Issue or Discussion?": [[3, "issue-or-discussion"]], "Code coverage": [[3, "code-coverage"]], "Developer guide": [[3, "developer-guide"]], "Run linting using pre-commit": [[4, "run-linting-using-pre-commit"]], "Running pre-commit": [[4, "running-pre-commit"]], "Fixing issues": [[4, "fixing-issues"]], "VSCode support": [[4, "vscode-support"]], "Make a release": [[5, "make-a-release"]], "Moving code from another repo": [[6, "moving-code-from-another-repo"]], "Run the tests using pytest": [[7, "run-the-tests-using-pytest"]], "Run static analysis using mypy": [[8, "run-static-analysis-using-mypy"]], "Update the tools": [[9, "update-the-tools"]], "Developer Guide": [[10, "developer-guide"]], "Tutorials": [[10, null], [17, null]], "How-to Guides": [[10, null], [17, null]], "Explanations": [[10, null], [17, null]], "Reference": [[10, null], [17, null]], "Standards": [[11, "standards"]], "Code Standards": [[11, "code-standards"]], "Documentation Standards": [[11, "documentation-standards"]], "Developer install": [[12, "developer-install"]], "Clone the repository": [[12, "clone-the-repository"]], "Install dependencies": [[12, "install-dependencies"]], "See what was installed": [[12, "see-what-was-installed"]], "Build and test": [[12, "build-and-test"]], "API Index": [[13, "api-index"]], "dodal": [[14, "dodal"], [18, "dodal"]], "How the documentation is structured": [[14, "how-the-documentation-is-structured"]], "About the documentation": [[15, "about-the-documentation"]], "Run in a container": [[16, "run-in-a-container"]], "Starting the container": [[16, "starting-the-container"]], "User Guide": [[17, "user-guide"]], "API": [[18, "module-dodal"]], "Getting Started": [[19, "getting-started"]], "The Purpose of Dodal": [[19, "the-purpose-of-dodal"]], "Using Devices": [[19, "using-devices"]], "Adding Logging": [[19, "adding-logging"]], "Installation": [[20, "installation"]], "Check your version of python": [[20, "check-your-version-of-python"]], "Create a virtual environment": [[20, "create-a-virtual-environment"]], "Installing the library": [[20, "installing-the-library"]]}, "indexentries": {"dodal": [[18, "module-dodal"]], "dodal.__version__ (in module dodal)": [[18, "dodal.dodal.__version__"]], "module": [[18, "module-dodal"]]}})