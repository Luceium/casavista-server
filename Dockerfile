# Use an official Python runtime as a parent image
FROM python:3.9-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt ./

# Install any needed packages specified in requirements.txt
RUN apk add --no-cache gcc musl-dev
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of the application into the container
COPY . .

# Expose the port that the Flask app runs on
EXPOSE 6060

# Set environment variables
ENV FLASK_APP=api.wsgi:app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=6060

ENV CLIENT_ORIGIN_URL=*


# Run Gunicorn server with the config file
CMD ["gunicorn", "-c", "gunicorn.conf.py", "api.wsgi:app"]
# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]

