# Changelog

## Support Collector Lambda v1.0.1

* Partition support cases and Health data using their creation date in S3 (YYYY/MM) to avoid saving duplicates on the daily sync
* Flatten Trusted Advisor checks in S3 to avoid duplicates during daily sync.

## Support Collector Lambda v1.0.0

* Update to Python 3.11 runtime
