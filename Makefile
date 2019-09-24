SHELL=/bin/sh

CC=gcc

ROOTDIR?=""

BMKDIR=$(ROOTDIR)/opt/hep-benchmark-suite
SCRIPTDIR=$(BMKDIR)/scripts
PYSCRIPTDIR=$(BMKDIR)/pyscripts

MAIN=hep-benchmark-suite
SOFTLINK=/usr/bin/hep-benchmark-suite
SCRIPTFILES=scripts/*
PYSCRIPTFILES=pyscripts/*

OTHERFILES=LICENSE README.md Makefile

DIR=$(shell pwd)

all: safeclean prepare install_basedep 

prepare:
	@echo -e "\n -- Prepare installation directories at $(BMKDIR) -- \n"

	@if test ! -d $(BMKDIR); then \
		mkdir -p $(SCRIPTDIR) $(PYSCRIPTDIR); \
		cp -f $(MAIN) $(OTHERFILES) $(BMKDIR) ; \
		chmod a+x $(BMKDIR)/$(MAIN)	; \
		if test ! -e $(SOFTLINK); then \
			ln -s $(BMKDIR)/$(MAIN) $(SOFTLINK) ;\
		fi ;\
		cp -fr $(SCRIPTFILES) $(SCRIPTDIR) ; cp -f $(PYSCRIPTFILES) $(PYSCRIPTDIR);\
	else \
		echo "WARN: $(BMKDIR) already exists. do 'make clean' to remove it" ; \
	fi

install_basedep:
	@echo -e "\n -- Install and configure default dependencies from ./lib... -- \n"

	bash -i -c "source $(SCRIPTDIR)/install-dependencies.sh; base_dependencies; hs06_dependencies ; hepscore_dependencies"\

clean:
	@echo -e "\n -- Deleting $(BMKDIR) and all its content -- \n"

	@if test -d $(BMKDIR); then \
		rm -fr $(BMKDIR) ; \
	fi

	@if test -e $(SOFTLINK); then \
		rm -f $(SOFTLINK) ; \
	fi


safeclean:
	@echo -e "\n -- Backup current $(BMKDIR) and clean it -- \n"

	@if test -d $(BMKDIR); then \
		tar cvzf $(BMKDIR)-$(shell date +"%d%m%y").tar.gz $(BMKDIR) ; make clean ; \
	else \
		if test -e $(SOFTLINK); then \
			rm -f $(SOFTLINK) ; \
		fi ;\
	fi