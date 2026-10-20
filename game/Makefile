# Prefer the checkout SDK; managed worktrees can reuse the primary checkout SDK.
LOCAL_GDK := $(abspath ..)/SGDK
COMMON_GDK := $(abspath $(shell git rev-parse --path-format=absolute --git-common-dir)/..)/SGDK
GDK ?= $(if $(wildcard $(LOCAL_GDK)/makefile.gen),$(LOCAL_GDK),$(COMMON_GDK))
export GDK

# includes internos resolvidos a partir de src/ (ex.: "actors/player.h")
EXTRA_FLAGS := -Isrc

include $(GDK)/makefile.gen
