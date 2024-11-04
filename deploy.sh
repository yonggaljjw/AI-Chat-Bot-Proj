#!bin/bash 

# Copy the requirements.txt file to the root of the django project
printf "Copying requirements.txt to the root of the django project\n"
cp requirements.txt project/WEB/requirements.txt \
    && printf "Done!\n"

# Build the django project to the server and run the docker-compose (Deploy the django project)
printf "Building the django project to the server\n"
cd project/WEB \
    && docker-compose up -d --build \
    && printf "Done! Deploy also ~\n"

# Deploy the Airflow project and ELK stack
printf "Deploying the Airflow project and ELK stack\n"
cd ../../ \
    && cd DB
    && docker-compose up -d \
    && printf "Done! Deployed the Airflow project and ELK stack\n"