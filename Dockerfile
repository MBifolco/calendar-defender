FROM python:3.7
  
# Add requirements.txt
ADD requirements.txt .
 
# Install app requirements
RUN pip install -r requirements.txt
 
# Create app directory
COPY ./app /app

#startup
CMD [ "python", "app/main.py" ]