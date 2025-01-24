
# Documentation


# References
## Running this on your laptop
Create a virtual environment.
You can use:
1. [Miniconda](https://docs.conda.io/en/latest/miniconda.html) (preferred) 
2. [Virtual Env](https://docs.python.org/3/tutorial/venv.html) (venv)
3. [Anaconda](https://www.anaconda.com/products/distribution)
4. Don't create a virtual environment at all and trample on a single Python environment you might already have

What are the diffs between Miniconda and Anaconda? [See this](https://stackoverflow.com/questions/45421163/anaconda-vs-miniconda)

You'll need to run Python 3.9.7 (see runtime.txt) to match the same version that Heroku runs.

Once you have a virtual environment ready, you will want to install the project dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file under the root project directory and populate it with the following content:

_You will need to get these values from Leon_.
```bash
# Flask Settings
FLASK_APP=api
FLASK_RUN_PORT=6060
FLASK_ENV=development
PORT=6060


```


Run the project in development mode:
```bash
flask run
```


# References
- [Firestore UI](https://github.com/thanhlmm/refi-app)
- [Using Python with Firestore](https://towardsdatascience.com/nosql-on-the-cloud-with-python-55a1383752fc)
- [Querying Firestore with Python](https://firebase.google.com/docs/firestore/query-data/get-data)

