# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS     ?=
SPHINXBUILD    ?= sphinx-build
SPHINXAPIDOC   ?= sphinx-apidoc
APIDOC_EXCLUDE ?= ../src/qiclib/packages/grpc/*
SOURCEDIR      = .
BUILDDIR       = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

apidoc :
	@$(SPHINXAPIDOC) --tocfile qiclib --separate -d 2 --module-first -o qiclib --templatedir $(SOURCEDIR)/_templates ../src/qiclib $(APIDOC_EXCLUDE)

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
