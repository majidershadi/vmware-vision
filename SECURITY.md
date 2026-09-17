# Reporting security issues

Do not put credentials, customer logs or an unpatched exploit in a public issue. Use the repository's private vulnerability reporting feature if available, or the contact details on [the maintainer's website](https://majidershadi.github.io/).

Include the package version, Splunk version, affected component and a sanitized reproduction. Describe whether exploitation requires administrator, search or ingestion access.

The application does not store VMware credentials or call VMware APIs. Syslog transport, input permissions, index access and Splunk platform maintenance remain deployment responsibilities. Keep raw events and exported search results within the same access policy as the original logs.
