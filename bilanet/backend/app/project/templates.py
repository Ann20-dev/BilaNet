"""Ready-made project skeletons. They work instantly and offline, without the AI model,
which matters on slow laptops. For anything custom, the /project/scaffold endpoint asks the model."""

TEMPLATES = {
    "python-cli": {
        "name": "Python command-line app",
        "files": {
            "README.md": "# My App\n\nRun it:\n\n```bash\npython -m venv .venv\n.venv/bin/pip install -r requirements.txt   # Windows: .venv\\Scripts\\pip\npython main.py --name Amina\n```\n\nTest it:\n\n```bash\npython -m unittest\n```\n",
            "requirements.txt": "",
            "main.py": "import argparse\n\nfrom app.core import greet\n\n\ndef main():\n    parser = argparse.ArgumentParser(description=\"My app\")\n    parser.add_argument(\"--name\", default=\"world\")\n    args = parser.parse_args()\n    print(greet(args.name))\n\n\nif __name__ == \"__main__\":\n    main()\n",
            "app/__init__.py": "",
            "app/core.py": "def greet(name: str) -> str:\n    return f\"Hello, {name}!\"\n",
            "tests/__init__.py": "",
            "tests/test_core.py": "import unittest\n\nfrom app.core import greet\n\n\nclass TestGreet(unittest.TestCase):\n    def test_greet(self):\n        self.assertEqual(greet(\"Amina\"), \"Hello, Amina!\")\n\n\nif __name__ == \"__main__\":\n    unittest.main()\n",
            ".gitignore": "__pycache__/\n.venv/\n",
        },
    },
    "fastapi": {
        "name": "Python web API (FastAPI)",
        "files": {
            "README.md": "# My API\n\n```bash\npython -m venv .venv\n.venv/bin/pip install -r requirements.txt\n.venv/bin/uvicorn app.main:app --reload\n```\n\nOpen http://127.0.0.1:8000/docs to try it.\n",
            "requirements.txt": "fastapi\nuvicorn[standard]\n",
            "app/__init__.py": "",
            "app/main.py": "from fastapi import FastAPI, HTTPException\nfrom pydantic import BaseModel\n\napp = FastAPI(title=\"My API\")\n\n\nclass Item(BaseModel):\n    name: str\n    price: float\n\n\nitems: dict[int, Item] = {}\n\n\n@app.get(\"/items\")\ndef list_items():\n    return items\n\n\n@app.post(\"/items/{item_id}\")\ndef add_item(item_id: int, item: Item):\n    items[item_id] = item\n    return item\n\n\n@app.get(\"/items/{item_id}\")\ndef get_item(item_id: int):\n    if item_id not in items:\n        raise HTTPException(404, \"Item not found\")\n    return items[item_id]\n",
            ".gitignore": "__pycache__/\n.venv/\n",
        },
    },
    "flask": {
        "name": "Python website (Flask)",
        "files": {
            "README.md": "# My Site\n\n```bash\npython -m venv .venv\n.venv/bin/pip install -r requirements.txt\n.venv/bin/flask --app app run --debug\n```\n",
            "requirements.txt": "flask\n",
            "app.py": "from flask import Flask, render_template\n\napp = Flask(__name__)\n\n\n@app.route(\"/\")\ndef home():\n    return render_template(\"index.html\", title=\"Home\")\n",
            "templates/index.html": "<!doctype html>\n<html>\n<head>\n  <meta charset=\"utf-8\">\n  <title>{{ title }}</title>\n  <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='style.css') }}\">\n</head>\n<body>\n  <h1>Welcome</h1>\n</body>\n</html>\n",
            "static/style.css": "body { font-family: sans-serif; max-width: 700px; margin: 2rem auto; padding: 0 1rem; }\n",
            ".gitignore": "__pycache__/\n.venv/\n",
        },
    },
    "website": {
        "name": "Static website (HTML/CSS/JS)",
        "files": {
            "index.html": "<!doctype html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"utf-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n  <title>My Site</title>\n  <link rel=\"stylesheet\" href=\"css/style.css\">\n</head>\n<body>\n  <header><h1>My Site</h1></header>\n  <main>\n    <p id=\"message\">Hello!</p>\n    <button id=\"btn\">Click me</button>\n  </main>\n  <script src=\"js/main.js\"></script>\n</body>\n</html>\n",
            "css/style.css": "* { box-sizing: border-box; }\nbody { margin: 0; font-family: system-ui, sans-serif; line-height: 1.5; }\nheader { background: #1b5e20; color: white; padding: 1rem; }\nmain { max-width: 700px; margin: 0 auto; padding: 1rem; }\n",
            "js/main.js": "document.getElementById(\"btn\").addEventListener(\"click\", () => {\n  document.getElementById(\"message\").textContent = \"You clicked the button!\";\n});\n",
            "README.md": "# My Site\n\nOpen index.html in your browser. No installation needed.\n",
        },
    },
    "node-express": {
        "name": "Node.js API (Express)",
        "files": {
            "package.json": "{\n  \"name\": \"my-api\",\n  \"version\": \"1.0.0\",\n  \"type\": \"module\",\n  \"scripts\": {\n    \"start\": \"node src/index.js\",\n    \"dev\": \"node --watch src/index.js\"\n  },\n  \"dependencies\": {\n    \"express\": \"^4.21.0\"\n  }\n}\n",
            "src/index.js": "import express from \"express\";\nimport { router as items } from \"./routes/items.js\";\n\nconst app = express();\napp.use(express.json());\napp.use(\"/items\", items);\n\nconst port = process.env.PORT || 3000;\napp.listen(port, () => console.log(`Listening on http://localhost:${port}`));\n",
            "src/routes/items.js": "import { Router } from \"express\";\n\nexport const router = Router();\nconst items = [];\n\nrouter.get(\"/\", (req, res) => res.json(items));\n\nrouter.post(\"/\", (req, res) => {\n  items.push(req.body);\n  res.status(201).json(req.body);\n});\n",
            "README.md": "# My API\n\n```bash\nnpm install\nnpm run dev\n```\n",
            ".gitignore": "node_modules/\n",
        },
    },
    "java-console": {
        "name": "Java console app",
        "files": {
            "src/main/java/app/Main.java": "package app;\n\nimport java.util.Scanner;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner in = new Scanner(System.in);\n        System.out.print(\"Your name: \");\n        String name = in.nextLine();\n        System.out.println(Greeter.greet(name));\n    }\n}\n",
            "src/main/java/app/Greeter.java": "package app;\n\npublic class Greeter {\n    public static String greet(String name) {\n        return \"Hello, \" + name + \"!\";\n    }\n}\n",
            "README.md": "# My Java App\n\n```bash\njavac -d out src/main/java/app/*.java\njava -cp out app.Main\n```\n",
            ".gitignore": "out/\n*.class\n",
        },
    },
    "cpp-console": {
        "name": "C++ console app",
        "files": {
            "src/main.cpp": "#include <iostream>\n#include \"greet.h\"\n\nint main() {\n    std::string name;\n    std::cout << \"Your name: \";\n    std::getline(std::cin, name);\n    std::cout << greet(name) << \"\\n\";\n    return 0;\n}\n",
            "src/greet.h": "#pragma once\n#include <string>\n\nstd::string greet(const std::string& name);\n",
            "src/greet.cpp": "#include \"greet.h\"\n\nstd::string greet(const std::string& name) {\n    return \"Hello, \" + name + \"!\";\n}\n",
            "README.md": "# My C++ App\n\n```bash\ng++ -std=c++17 -Wall src/*.cpp -o app\n./app\n```\n",
        },
    },
}


def tree(files: dict[str, str]) -> str:
    """Render file paths as an indented folder tree."""
    lines, seen = [], set()
    for path in sorted(files, key=lambda p: (p.count("/") == 0, p)):
        parts = path.split("/")
        for depth in range(len(parts) - 1):
            folder = "/".join(parts[: depth + 1])
            if folder not in seen:
                seen.add(folder)
                lines.append("  " * depth + parts[depth] + "/")
        lines.append("  " * (len(parts) - 1) + parts[-1])
    return "\n".join(lines)
