# user, password and database we create in PostgreSQL which will be used by Airflow
# POSTGRES_USER=airflow
# POSTGRES_PASSWORD=airflow
# POSTGRES_DB=airflow
# POSTGRES_DNS=airflow-postgres   # DNS name of PostgreSQL (name of the kubernetes service we will create for Postgres deployment)



# Create namespaces and a secret for pulling images from ACR. It uses credentials of a Service Principal with proper permissions
# ('acrpush' role). We have here the following arguments:
	# - docker-server: ACR URL (<registry-name>.azurecr.io)
	# - docker-username: Service Principal client ID
	# - docker-password: Service Principal client secret
	# - docker-email: It doesn't matter what we put here but it is needed
for ns in "source-db" "semantic-search" "rag" "data-gov"; do
	kubectl create namespace $ns
done



# Create a secret used by PostgreSQL deployment (to create a user and database used by Airflow)
# kubectl create secret generic airflow-postgres \
# 	--from-literal=postgres_user=$POSTGRES_USER \
# 	--from-literal=postgres_password=$POSTGRES_PASSWORD \
# 	--from-literal=postgres_database=$POSTGRES_DB \
# 	-n airflow