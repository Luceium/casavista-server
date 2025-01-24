# Documentation

## 1.  API Endpoints
Creating an API endpoint is pretty easy, just follow the example for the `auth` folder or the `email` folders. You need an entry point, is the `bp (blueprint)` section and finally you need to add it to `api/__init__.py` like this 

folder_name_parent.folder_name_child import your_entry_point
```
from api.email import email_views
```
Don't foget to register with your blueprint with the app like so 
our_app_object.register_blueprint(your_entry_point.your_blueprint_object)
```
app.register_blueprint(email_views.bp)
```




