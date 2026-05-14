# Django CLI 

### Migrar un una app

Comando asociados a la migración en Django.
``` python
python manage.py migrate # Use it after app or models creation.
python makemigration <app_name> # Create an ORM model, like a SQL table creation, also if we want to update the model.
python manage.py sqlmigrate <app_name> [migration index, like 0001] 
```

### Data management in python CLI

We can manage DB data in python shell.

```commandline
python manage.py shell
```
Then we manage de data.
```python
from app_name.models import Model
Model.objects.all() # select all the objects of a model

# Create a record on DB.
app_name = Model(firstname='Emil', lastname='Refsnes')
app_name.save()

Model.objects.all().values() # Show the objects attributes.

# Update a record.
x = Model.objects.all()[0]
var = x.firstname  # This show the attribute value.

x.firstname = "Liam"
x.save()

# Delete a record.
x = Model.objects.all()[0]
x.delete()

```
Quick use of the items given.

```python
def sel(model):
    return model.object.all()

def add(obj: list):
    for i in obj:
        i.save()

def update(model, pk, **campos):
    obj = model.objects.filter(pk=pk).first()
    if not obj:
        return None

    for campo, valor in campos.items():
        setattr(obj, campo, valor)

    obj.save()
    return obj
    
def delete(model, idx: int):
    x = model.objects.all()[idx]
    x.delete()
```





