.PHONY: verify pack-zip pack-smoke setup clean

verify:
	./scripts/verify-pack.sh

pack-zip:
	./scripts/build-pack-zip.sh

pack-smoke:
	./scripts/verify-sidecar-smoke.sh

setup:
	./scripts/setup-aws-sidecar.sh

clean:
	rm -rf dist
