# Prefer the checkout SDK; managed worktrees can reuse the primary checkout SDK.
LOCAL_GDK := $(abspath ..)/SGDK
COMMON_GDK := $(abspath $(shell git rev-parse --path-format=absolute --git-common-dir)/..)/SGDK
GDK ?= $(if $(wildcard $(LOCAL_GDK)/makefile.gen),$(LOCAL_GDK),$(COMMON_GDK))
export GDK

# includes internos resolvidos a partir de src/ (ex.: "actors/player.h")
EXTRA_FLAGS := -Isrc

include $(GDK)/makefile.gen

# Keep authored UTF-8 intact, then encode accented string literals after the C
# preprocessor has resolved includes/macros. Each ROM character is one byte.
$(OUT_DIR)/%.o: %.c $(DEP_DIR)/%.d
	@$(MKDIR) -p $(dir $@)
	$(CC) $(CFLAGS) -E $< -o $(@:.o=.utf8.i)
	python3 tools/encode_text.py $(@:.o=.utf8.i) $(@:.o=.i)
	$(CC) $(CFLAGS) -c $(@:.o=.i) -o $@

$(addprefix $(OUT_DIR)/,$(SRC_C:.c=.o)): tools/encode_text.py tools/text_codec.py

# SGDK keeps rom.bin internally; publish the game name after padding/checksum.
.PHONY: package-rom
release debug: package-rom
package-rom: padROM
	python3 tools/package_rom.py --output "$(OUT_DIR)"

ifeq ($(BUILD_TYPE),debug)
padROM: injectSymbolsInROM
endif
