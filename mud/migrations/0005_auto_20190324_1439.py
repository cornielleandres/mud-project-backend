# Generated by Django 2.1.7 on 2019-03-24 18:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mud', '0004_inventory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='name',
            field=models.CharField(default='default item name', max_length=32, unique=True),
        ),
    ]
