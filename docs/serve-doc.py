from livereload import Server, shell


def main():
    server = Server()
    server.watch("**/*.rst", shell("make html"), delay=1)
    server.watch("../src/qiclib/**/*.py", shell("make html"), delay=1)
    server.watch("_static/*", shell("make html"), delay=1)
    server.watch("_templates/*", shell("make html"), delay=1)
    server.serve(root="_build/html")


if __name__ == "__main__":
    main()
