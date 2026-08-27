This Helm chart runs a JavaScript script in a Job which extracts metadata about scripts and tables from a specified SQL server. 

This metadata will be then used by the Data Governance Backend (deployed using the `helm_charts/data_gov_backend` Helm chart). 

For example, this script prepares a list of tables for which we will be able to create documentation in the Data Governance app.