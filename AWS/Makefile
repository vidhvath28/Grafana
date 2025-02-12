# Makefile to run all Python scripts one by one

# Define the Python executable
PYTHON = python

# List of your Python scripts
SCRIPTS = aws_cost_per_account.py  aws_cost_per_service.py  aws_cost_per_service_per_account.py aws_gpu_cost_report.py

# Default target to run all scripts
all: $(SCRIPTS)

# Rule to run each script
$(SCRIPTS):
	$(PYTHON) $@
