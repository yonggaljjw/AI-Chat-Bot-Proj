#!bin/bash 

# Copy the requirements.txt file to the root of the django project
printf "Copying requirements.txt to the root of the django project\n"
cp requirements.txt project/WEB/requirements.txt \
    && printf "Done!\n"

# Build the django project to the server and run the docker-compose (Deploy the django project)
printf "Building the django project to the server\n"
cd project/WEB \
    && docker compose up -d --build \
    && printf "Done! Deploy also ~\n"

# Move to the Airflow project and ELK stack directory
cd ../../ \
    && cd project/DB

# Deploy the Airflow project
cd airflow \
    && printf "Deploying the Airflow project\n" \
    && docker compose build \
    && docker compose up -d \
    && printf "Done! \n"

# # Deploy the ELK stack
# cd ../elk \
#     && printf "Deploying the ELK stack\n" \
#     && docker compose up -d \
#     && printf "Done! \n"