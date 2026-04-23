PORT ?= 8000
HOST ?= 127.0.0.1

.PHONY: serve

serve:
	@echo "Serving on http://$(HOST):$(PORT)"
	python3 -m http.server $(PORT) --bind $(HOST)
