.PHONY: venv install uk-cities uk-osm uk-cluster uk-stats uk-cv uk-report uk clean report deploy

venv:
	python3 -m venv .venv

install:
	./.venv/bin/pip install -r requirements.txt

uk-cities:
	./.venv/bin/python scripts/01_uk_cities.py

uk-osm: uk-cities
	./.venv/bin/python scripts/02_overpass_fetch.py --region uk

uk-cluster: uk-osm
	./.venv/bin/python scripts/03_cluster_clubs.py --region uk

uk-stats: uk-cluster
	./.venv/bin/python scripts/04_compute_stats.py --region uk

uk-cv:
	./.venv/bin/python scripts/05_cv_verify.py --region uk --sample 300

uk-report: uk-stats
	./.venv/bin/python scripts/06_render_report.py --region uk

uk: uk-stats uk-report

clean:
	rm -rf data/processed/* reports/uk_*.png reports/uk_*.md

# Render the densest-circle writeup to HTML + PDF
report:
	./.venv/bin/python scripts/27_pdf_report.py

# Copy the latest HTML/PDF to the repo root so GitHub Pages serves them
# as index.html and as a downloadable PDF.
deploy: report
	cp reports/_densest_circle_full_writeup.html index.html
	cp reports/densest_circle_full_writeup.pdf densest_circle_full_writeup.pdf
	@echo "Deployed. Commit + push to publish via GitHub Pages."
