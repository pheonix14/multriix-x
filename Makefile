# MULTRIIX X — High-Performance Makefile
# Author: Pheonix14 / ZeroX

CXX ?= clang++
CXXFLAGS ?= -std=c++17 -O3 -Wall -Wextra

PREFIX ?= /usr/local
TERMUX_PREFIX = /data/data/com.termux/files/usr

SRC = multriix_x/cli/mx.cpp
BIN = bin/mx

all: $(BIN)

$(BIN): $(SRC)
	@mkdir -p bin
	@echo "🔨 Compiling native C++ CLI (mx)..."
	$(CXX) $(CXXFLAGS) $(SRC) -o $(BIN)
	@echo "✅ Built $(BIN) successfully!"

install: $(BIN)
	@echo "📦 Installing mx to PATH..."
	@if [ -d "$(TERMUX_PREFIX)/bin" ]; then \
		cp $(BIN) $(TERMUX_PREFIX)/bin/mx && chmod +x $(TERMUX_PREFIX)/bin/mx && echo "✅ Installed to $(TERMUX_PREFIX)/bin/mx"; \
	elif [ -d "$$HOME/bin" ]; then \
		mkdir -p $$HOME/bin && cp $(BIN) $$HOME/bin/mx && chmod +x $$HOME/bin/mx && echo "✅ Installed to $$HOME/bin/mx"; \
	else \
		install -m 755 $(BIN) $(PREFIX)/bin/mx && echo "✅ Installed to $(PREFIX)/bin/mx"; \
	fi

test:
	@echo "🧪 Running Multriix X verification suite..."
	@python3 multriix_x/tests/run_all_tests.py

clean:
	@rm -rf bin
	@echo "🧹 Cleaned build artifacts."

.PHONY: all install test clean
