# ELK Health

This is a POC to monitor the health of an ELK stack.

The base idea sees a checker machine injecting a `check` in the ELK pipeline.
Then, the presence of this `check` within the Elasticsearch cluster is
checked.

If present, the ELK stack is healthy. If not, _Houston, we have a problem..._
